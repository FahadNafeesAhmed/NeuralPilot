import time
import cv2
import numpy as np
from mss import mss
from gradio_client import Client, handle_file
import os
import pyautogui
import google.generativeai as genai
from PIL import Image
import json
import ctypes
import logging
import sys

logging.basicConfig(
    filename='agent.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filemode='w'
)

class LoggerWriter:
    def __init__(self, level):
        self.level = level
    def write(self, message):
        if message != '\n':
            logging.log(self.level, message.strip())
        sys.__stdout__.write(message)
    def flush(self):
        sys.__stdout__.flush()

sys.stdout = LoggerWriter(logging.INFO)

# Fix PyAutoGUI clicking the wrong spot due to Windows 11 Display Scaling
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-Monitor DPI Aware (Modern)
except AttributeError:
    ctypes.windll.user32.SetProcessDPIAware() # Fallback

# ==========================================
# 1. PASTE YOUR APIS HERE
# ==========================================
# Set this in your terminal: $env:GEMINI_API_KEY="your_key"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COLAB_URL = "https://16865f3844876f330c.gradio.live"

# ==========================================
# 2. WHAT IS THE OVERALL GOAL?
# ==========================================
OBJECTIVE = "Open the start menu, open cmd, and type the command to launch chrome."

def setup_gemini():
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-3.5-flash')

def ask_gemini_brain(model, image_path, objective):
    img = Image.open(image_path)
    prompt = f"""Your overall objective is: {objective}
Look at this screenshot of the computer screen. What is the single NEXT action I must take to make progress?

You must reply with a valid JSON object representing one of these three actions:
1. click: Tells the visual model to find an icon/button and click it.
   {{"action": "click", "target": "short highly descriptive visual name including colors (e.g. 'blue Windows start button')"}}
2. type: Types out a string of text on the keyboard.
   {{"action": "type", "text": "the text to type"}}
3. press: Presses a specific key on the keyboard.
   {{"action": "press", "key": "win"}} (You can use "win" to open the start menu instantly, "enter", "esc", etc)
4. done: The objective is complete.
   {{"action": "done"}}

Reply with ONLY the raw JSON object and nothing else."""
    
    response = model.generate_content([prompt, img])
    return response.text.strip()


def extract_boxes_from_annotated_image(annotated_img, original_w, original_h):
    annotated_h, annotated_w = annotated_img.shape[:2]
    hsv = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2HSV)

    lower_vivid = np.array([0, 120, 120])
    upper_vivid = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower_vivid, upper_vivid)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    centers = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 10 or h < 10:
            continue

        scale_x = original_w / annotated_w
        scale_y = original_h / annotated_h

        real_x1 = int(x * scale_x)
        real_y1 = int(y * scale_y)
        real_x2 = int((x + w) * scale_x)
        real_y2 = int((y + h) * scale_y)

        center_x = (real_x1 + real_x2) // 2
        center_y = (real_y1 + real_y2) // 2
        centers.append((center_x, center_y))

    return centers


def main():
    if not GEMINI_API_KEY:
        print("[ERROR] Please set the GEMINI_API_KEY environment variable!")
        return

    print("Configuring Google Gemini API (The Brain)...")
    gemini_model = setup_gemini()

    print(f"Connecting to Colab API at: {COLAB_URL} (The Eyes)...")
    try:
        eyes_client = Client(COLAB_URL)
        print("Connected successfully!")
    except Exception as e:
        print(f"\n[ERROR] Failed to connect: {e}")
        return

    with mss() as sct:
        monitor = sct.monitors[1]
        orig_w = monitor["width"]
        orig_h = monitor["height"]

    print(f"\n[STARTING OS AGENT] Objective: '{OBJECTIVE}'\n")
    temp_file = "temp_screenshot.jpg"

    with mss() as sct:
        while True:
            # 1. Take Screenshot
            print("📸 Taking screenshot...")
            sct_img = sct.grab(monitor)
            frame_bgra = np.array(sct_img)
            frame_bgr = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)
            
            # Resize for speed
            frame_resized = cv2.resize(frame_bgr, (1280, 720))
            cv2.imwrite(temp_file, frame_resized)

            # 2. Ask The Brain (Google Gemini)
            print(f"🧠 Asking Gemini Brain: What to do next for '{OBJECTIVE}'?")
            try:
                brain_response = ask_gemini_brain(gemini_model, temp_file, OBJECTIVE)
                
                # Parse JSON
                try:
                    action_data = json.loads(brain_response)
                except json.JSONDecodeError:
                    print(f"  ⚠️ Brain returned invalid JSON: {brain_response}")
                    time.sleep(2)
                    continue

                action = action_data.get("action")
                print(f"  → Brain decided to: {action_data}")

                if action == "done":
                    print("\n✅ Objective Complete! Exiting.")
                    break
                    
                elif action == "type":
                    text = action_data.get("text", "")
                    print(f"  ⌨️ Typing: '{text}'")
                    pyautogui.write(text, interval=0.05)
                    
                elif action == "press":
                    key = action_data.get("key", "")
                    print(f"  ⌨️ Pressing key: '{key}'")
                    pyautogui.press(key)
                    
                elif action == "click":
                    target = action_data.get("target", "")
                    print(f"👁️ Asking Colab Eyes to locate: '{target}'")
                    try:
                        annotated_img_path = eyes_client.predict(
                            frame=handle_file(temp_file),
                            search_query=target,
                            api_name="/eyes"
                        )
                        
                        output_image = cv2.imread(annotated_img_path)
                        centers = extract_boxes_from_annotated_image(output_image, orig_w, orig_h)
                        
                        cv2.imshow("NeuralPilot - OS Agent", output_image)
                        cv2.waitKey(1)
                        
                        if centers:
                            cx, cy = centers[0]
                            
                            # Add multi-monitor offset so it clicks the correct screen
                            abs_x = cx + monitor["left"]
                            abs_y = cy + monitor["top"]
                            
                            print(f"🖱️ Clicking at ({abs_x}, {abs_y})")
                            pyautogui.moveTo(abs_x, abs_y, duration=0.3)
                            pyautogui.click()
                        else:
                            print("  ⚠️ Eyes couldn't find the target on screen.")
                            
                    except Exception as e:
                        print(f"Eyes Error: {e}")

                else:
                    print(f"  ⚠️ Unknown action type: {action}")
                    
            except Exception as e:
                print(f"Brain Error: {e}")
                time.sleep(2)
                continue

            print("⏳ Waiting 3 seconds for UI to update...\n")
            cv2.waitKey(3000)

    cv2.destroyAllWindows()
    if os.path.exists(temp_file):
        os.remove(temp_file)

if __name__ == "__main__":
    main()

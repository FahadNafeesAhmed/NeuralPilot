import sys
import os
import cv2
import torch
import numpy as np
from mss import mss
from PIL import Image

# Add Eagle/Embodied to system path so we can import locateanything_worker
project_dir = os.path.dirname(os.path.abspath(__file__))
eagle_path = os.path.join(project_dir, 'Eagle', 'Embodied')
if eagle_path not in sys.path:
    sys.path.append(eagle_path)

try:
    from locateanything_worker import LocateAnythingWorker
except ImportError as e:
    print(f"Error importing LocateAnythingWorker: {e}")
    print(f"Please ensure the 'Eagle/Embodied' directory contains 'locateanything_worker.py'")
    sys.exit(1)

def main():
    # Hardcoding to CPU because the Ryzen 9 is powerful and CUDA lacks Blackwell support
    device = "cpu"
    print(f"Initializing LocateAnythingWorker on {device}...")
    
    # FORCING MATH BACKEND for SDPA
    # This disables FlashAttention/MemEfficientAttention which are likely missing the Blackwell kernels
    if device == "cuda":
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
        print("Forced PyTorch SDPA to Math backend for RTX 5000 compatibility.")
    
    # Initialize the model worker
    try:
        worker = LocateAnythingWorker("nvidia/LocateAnything-3B", device=device)
    except Exception as e:
        print(f"Failed to initialize model worker: {e}")
        return

    # Target categories for open-vocabulary grounding
    categories = ["person", "phone", "coffee mug"]
    print(f"Searching for: {categories}")

    # Set up super-fast screen capture
    sct = mss()
    monitor = sct.monitors[1]  # Capture primary monitor
        
    print("Screen capture started. Press 'q' in the video window to exit.")

    # Assign some standard colors (BGR)
    colors = {
        "person": (0, 255, 0),       # Green
        "phone": (0, 0, 255),        # Red
        "coffee mug": (255, 0, 0),   # Blue
    }
    default_color = (0, 255, 255)    # Yellow for unknown

    while True:
        # Capture the screen directly into memory
        sct_img = sct.grab(monitor)
        # Convert to a standard numpy array (BGRA format)
        frame_bgra = np.array(sct_img)
        # Convert to standard BGR for OpenCV
        frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)
            
        # Convert BGR (OpenCV format) to RGB for the AI model
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)
        orig_w, orig_h = pil_image.size
        
        # VITAL: Shrink the image to speed up CPU inference massively!
        pil_image.thumbnail((512, 512))
        
        for category in categories:
            try:
                # Use fast generation mode to squeeze out extra CPU speed
                result = worker.ground_multi(pil_image, category, generation_mode="fast")
                
                # Parse the bounding boxes using ORIGINAL dimensions so they scale back up to your full screen size
                boxes = LocateAnythingWorker.parse_boxes(result["answer"], orig_w, orig_h)
                
                color = colors.get(category, default_color)
                
                for box in boxes:
                    x1, y1, x2, y2 = int(box["x1"]), int(box["y1"]), int(box["x2"]), int(box["y2"])
                    
                    # Draw a nice thick box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 4)
                    label_text = f"{category}"
                    cv2.putText(frame, label_text, (x1, max(y1 - 10, 0)), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
            except Exception as e:
                print(f"Inference error for {category}: {e}")

        # Render the frame to a small preview window (so it doesn't take up your whole screen)
        preview_frame = cv2.resize(frame, (1280, 720))
        cv2.imshow("LocateAnything-3B Live Grounding", preview_frame)
        
        # Graceful stream termination on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Quitting...")
            break

    # Clean up resources
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

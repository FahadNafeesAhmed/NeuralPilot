import time
import cv2
import numpy as np
from mss import mss
from gradio_client import Client, handle_file
import os

# ==========================================
# 1. PASTE YOUR COLAB PUBLIC LINK HERE
# ==========================================
COLAB_URL = "https://179ac29634a2f6bbf1.gradio.live"

# ==========================================
# 2. TYPE WHAT YOU WANT TO SEARCH FOR
# ==========================================
SEARCH_QUERY = "app icon on the Windows taskbar"

def main():
    print(f"Connecting to Colab API at: {COLAB_URL} ...")
    try:
        client = Client(COLAB_URL)
        print("Connected successfully!")
    except Exception as e:
        print(f"\n[ERROR] Failed to connect: {e}")
        print("-> Did you paste the correct link in COLAB_URL?")
        print("-> Is your Google Colab cell currently running?")
        return

    # Set up screen capture
    sct = mss.MSS()
    monitor = sct.monitors[1]  # Capture primary monitor

    print(f"\n[STARTING] Screen capture started. Searching for: '{SEARCH_QUERY}'")
    print("-> Press 'q' in the video window to exit.")

    temp_file = "temp_screenshot.jpg"

    while True:
        start_time = time.time()
        
        # 1. Capture the screen locally
        sct_img = sct.grab(monitor)
        frame_bgra = np.array(sct_img)
        frame_bgr = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)
        
        # 2. Shrink to 720p to save internet upload time
        frame_resized = cv2.resize(frame_bgr, (1280, 720))
        cv2.imwrite(temp_file, frame_resized)
        
        # 3. Send to Colab GPU via API
        try:
            # Use submit instead of predict to keep the window responsive!
            job = client.submit(
                frame=handle_file(temp_file),
                search_text=SEARCH_QUERY,
                api_name="/predict"
            )
            
            # Keep the OpenCV window alive while we wait for the Colab response
            while not job.done():
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    return
            
            result = job.result()
            
            # 4. Read the resulting image from the API
            if result:
                output_image = cv2.imread(result)
                if output_image is not None:
                    # Show the image with bounding boxes!
                    cv2.imshow("LocateAnything - Colab API Client", output_image)
        except Exception as e:
            print(f"API Error: {e}")
            # Show original frame if API fails so the window doesn't freeze
            cv2.imshow("LocateAnything - Colab API Client", frame_resized)

        # Calculate Frames Per Second (FPS)
        fps = 1.0 / (time.time() - start_time)
        print(f"Processed frame at {fps:.2f} FPS")

    # Clean up
    cv2.destroyAllWindows()
    if os.path.exists(temp_file):
        os.remove(temp_file)

if __name__ == "__main__":
    main()

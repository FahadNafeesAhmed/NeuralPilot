# NeuralPilot: Visual OS Agent

NeuralPilot is a highly capable, dual-model autonomous OS Agent. It can view your screen, reason about tasks, and physically control your mouse and keyboard to execute complex objectives on your computer.

It is built using a **Split-Brain Architecture**:
1. **The Brain (Google Gemini 3.5 Flash)**: Runs via API. Looks at screenshots of your computer and outputs structured JSON action plans (`type`, `click`, `press`).
2. **The Eyes (NVIDIA LocateAnything-3B)**: Hosted on a free Google Colab T4 GPU. Receives visual descriptions from the Brain (e.g., "blue Windows start button") and generates exact pixel coordinates for PyAutoGUI to click.

---

## 🚀 Setup & Installation

### 1. Start the Eyes (Colab Backend)
Because running large vision models locally requires a powerful GPU, NeuralPilot hosts the "Eyes" on a free Google Colab instance.
1. Upload `LocateAnything_Colab.ipynb` to Google Colab.
2. Go to **Runtime > Run all**.
3. Scroll to the bottom and copy the public `.gradio.live` URL.

### 2. Setup the Brain (Local Execution)
Run the actual agent locally on your Windows machine.

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/NeuralPilot.git
cd NeuralPilot

# Install dependencies
pip install -r requirements.txt
pip install google-generativeai mss pyautogui opencv-python gradio_client Pillow numpy
```

### 3. Run the Agent
The Brain requires a free Google Gemini API key. You can get one at [aistudio.google.com](https://aistudio.google.com/).

Before running the agent, set your API key as an environment variable and update the Colab URL in the script.

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

Open `os_agent.py` and paste your Colab `.gradio.live` link into `COLAB_URL`.

**Start the agent:**
```bash
python os_agent.py
```

## 🧠 How it Works

1. **Screenshot**: `mss` takes a screenshot of your primary monitor.
2. **Reasoning**: The screenshot and the objective (e.g. "Open Chrome") are sent to Gemini 3.5 Flash.
3. **JSON Router**: Gemini outputs a JSON command:
    - `{"action": "click", "target": "chrome icon"}`
    - `{"action": "type", "text": "hello"}`
    - `{"action": "press", "key": "win"}`
4. **Grounding**: If the action is `click`, the target string is sent to the Colab GPU running NVIDIA LocateAnything-3B, which returns the exact X/Y pixel coordinates of that object on your screen.
5. **Execution**: PyAutoGUI moves your physical mouse and clicks, or types on your keyboard.

## ⚠️ Notes
- If your mouse clicks the wrong spot, ensure Windows Display Scaling is handled. The script currently uses `ctypes.windll.shcore.SetProcessDpiAwareness(2)`.
- Google Colab free tier will disconnect after periods of inactivity. You will need to click "Reconnect" and generate a new Gradio link if it times out.

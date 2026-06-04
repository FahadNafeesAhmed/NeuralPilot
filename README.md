# 🧠 NeuralPilot

**A real-time AI screen agent powered by NVIDIA's LocateAnything-3B model.**

NeuralPilot watches your computer screen and can find *anything* you describe using natural language — icons, buttons, people, objects — and pinpoints their exact pixel location. This is the foundation for building fully autonomous OS agents that can control your computer on their own.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![NVIDIA](https://img.shields.io/badge/Model-LocateAnything--3B-76b900?logo=nvidia)
![Google Colab](https://img.shields.io/badge/Backend-Google%20Colab%20GPU-F9AB00?logo=googlecolab)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎬 What It Does

NeuralPilot takes a screenshot of your PC screen every second, fires it to a cloud GPU running the NVIDIA LocateAnything-3B model, and draws precise bounding boxes around whatever you describe in plain English — in real time.

**Example:** Type `"app icon on the Windows taskbar"` and watch it instantly light up every single icon on your taskbar with a glowing box.

---

## 🏗️ Architecture

This project uses a **Client-Server hybrid** to combine cloud GPU power with a local desktop feel — completely free.

```
Your PC (Client)                      Google Colab (Server — FREE GPU)
────────────────────                  ────────────────────────────────
 📸 mss  →  Screenshot
 📤  ──────────────────────────────►  🧠 NVIDIA LocateAnything-3B (T4 GPU)
 🖼️  ◄──────────────────────────────  📦 Image with bounding boxes drawn
 🖥️  Display result window
```

---

## 🚀 Quick Start

### Step 1: Launch the Cloud GPU Server (Google Colab)

1. Open [`LocateAnything_Colab.ipynb`](./LocateAnything_Colab.ipynb) in [Google Colab](https://colab.research.google.com/).
2. Set the runtime to **GPU → T4**.
3. Run **Cell 1** to install all dependencies.
4. Run **Cell 2** to launch the Gradio API server.
5. Copy the public `.gradio.live` URL that appears in the output.

### Step 2: Run the Local Client (Your PC)

1. Clone this repository:
   ```bash
   git clone https://github.com/FahadNafeesAhmed/NeuralPilot.git
   cd NeuralPilot
   ```

2. Install local dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Open `api_client.py` and fill in your two settings:
   ```python
   # Line 11 — Paste your Colab .gradio.live URL here
   COLAB_URL = "https://YOUR_LINK_HERE.gradio.live"

   # Line 16 — Type what you want to find on your screen
   SEARCH_QUERY = "Google Chrome icon"
   ```

4. Run it!
   ```bash
   python api_client.py
   ```

A window pops up showing your live screen with glowing bounding boxes drawn around your target. Press **`q`** to quit.

---

## 💡 Example Search Queries

| Query | What it finds |
|---|---|
| `"app icon on the Windows taskbar"` | All taskbar icons at once |
| `"Google Chrome icon"` | The Chrome browser icon |
| `"close button"` | The ✕ button on any window |
| `"person"` | Any human visible on screen |
| `"dog"` | Any dog visible on screen |
| `"the search bar"` | Any text input field |

---

## 📁 Project Structure

```
NeuralPilot/
├── 📓 LocateAnything_Colab.ipynb   # Google Colab notebook (the GPU server)
├── 🐍 api_client.py                # Local client — sends frames to Colab API
├── 🐍 app.py                       # Alternative: run model locally on CPU
├── 📦 requirements.txt             # Local Python dependencies
└── 📖 README.md
```

> **Note:** The NVIDIA Eagle model source code is cloned at runtime inside the Colab notebook. It is not included in this repo.

---

## 🔮 Roadmap — Building a Full OS Agent

NeuralPilot is the **Vision Layer** of a complete autonomous OS agent. Here is what's next:

- [ ] Return raw `(x1, y1, x2, y2)` coordinates from API instead of an annotated image
- [ ] Add `pyautogui` to automatically move the mouse and click detected targets
- [ ] Integrate a reasoning LLM (Claude 3.5 / GPT-4o) as the autonomous "Brain"
- [ ] Build the full agent loop: `Screenshot → Think → Find → Click → Repeat`
- [ ] Add voice input: *"Open YouTube"* triggers the full autonomous loop

---

## 🙏 Credits

- **NVIDIA Research** for the [LocateAnything-3B](https://huggingface.co/nvidia/LocateAnything-3B) model
- **Google Colab** for the free T4 GPU
- **Gradio** for the zero-config API server framework

---

## 📄 License

MIT License — feel free to fork and build on top of this!

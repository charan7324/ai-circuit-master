# AI Circuit Master ⚡

An intelligent, physically-aware Electronic Design Automation (EDA) tool. This application uses the Gemini 2.5 Flash model to convert natural language descriptions or hand-drawn images into professional, LaTeX-rendered circuit schematics.


## 🌟 Key Features
- **Physically Intelligent Rendering:** The AI analyzes current flow. If a circuit is "broken" (e.g., an open switch in series), output components like LEDs are automatically rendered in a "Dark/Off" state.
- **Multimodal Input:** Supports both text prompts and image uploads. You can draw a circuit on paper, take a photo, and get a professional schematic in seconds.
- **LaTeX Backend:** Uses the `lcapy` library with a full TeX Live environment to produce textbook-quality SVG/PNG diagrams.
- **Auto-Topology Correction:** Intelligently handles complex series and parallel layouts based on engineering best practices.

## 🛠️ Tech Stack
- **AI:** Google Gemini 2.5 Flash (Multimodal)
- **Backend:** Python
- **Engineering Library:** Lcapy (Linear Circuit Analysis)
- **Rendering:** LaTeX (TeX Live) / dvipng
- **Deployment:** customtkinter (ux)

## 📦 Local Installation
1. Clone the repo: `git clone https://github.com/YOUR_USERNAME/ai-circuit-master.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Set your API Key: `export GOOGLE_API_KEY='your_key_here'`
4. Run the app: `python app.py`

*Note: For LaTeX rendering, you must have a TeX distribution (like MiKTeX or TeX Live) installed on your local machine.*

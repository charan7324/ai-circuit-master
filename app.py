import os
import re
import uuid
import google.generativeai as genai
from flask import Flask, render_template, request
from lcapy import Circuit
import PIL.Image

app = Flask(__name__)

# --- Configuration ---
GOOGLE_API_KEY = "AIzaSyBMwpryiWMBKgDqCu7yOZgwB8USVTLDNEo"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Ensure static directory exists for Railway
os.makedirs('static/circuits', exist_ok=True)

def get_ai_netlist(user_prompt, image_path=None):
    system_prompt = """
    You are an Expert Electrical Engineer AI. Convert prompts or images into Lcapy netlists.
    RULES:
    1. Node 0 is bottom-left. 
    2. Build strict 4-corner rectangular loops.
    3. If current is blocked (open series switch), render LED as 'kind=led' (Dark).
    4. If current flows, use 'kind=led, color=blue'.
    5. Component Dictionary: Battery (V1 1 0; down), Resistor (R1 1 2; right), 
       Open Switch (SW1 2 3; right), Closed Switch (W_SW 2 3; right, l=Closed-SW), 
       LED (D1 4 5; down).
    
    OUTPUT FORMAT: [REASONING] followed by [NETLIST].
    """
    
    content = [system_prompt, f"User Request: {user_prompt}"]
    if image_path:
        img = PIL.Image.open(image_path)
        content.append(img)
        content.append("Analyze this image and convert it to a professional schematic.")

    response = model.generate_content(content)
    raw = response.text
    try:
        reasoning = raw.split("[REASONING]")[1].split("[NETLIST]")[0].strip()
        netlist = raw.split("[NETLIST]")[1].replace("```text", "").replace("```", "").strip()
    except:
        reasoning, netlist = "Processed input.", raw.strip()
    return reasoning, netlist

@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    reasoning = None
    if request.method == 'POST':
        prompt = request.form.get('prompt', '')
        uploaded_file = request.files.get('circuit_image')
        
        temp_img_path = None
        if uploaded_file and uploaded_file.filename != '':
            temp_img_path = os.path.join('static/circuits', f"upload_{uuid.uuid4()}.png")
            uploaded_file.save(temp_img_path)

        reasoning, ai_netlist = get_ai_netlist(prompt, temp_img_path)
        
        # Spacing Middleware
        clean_netlist = re.sub(r'\b(right|left)(?!=)\b', r'\g<1>=2.5', ai_netlist)
        clean_netlist = re.sub(r'\b(up|down)(?!=)\b', r'\g<1>=2', clean_netlist)

        filename = f"{uuid.uuid4()}.png"
        save_path = os.path.join('static/circuits', filename)
        
        # LaTeX Drawing
        c = Circuit(clean_netlist)
        c.draw(save_path, label_nodes=False, dpi=300)
        image_url = f"/static/circuits/{filename}"

    return render_template('index.html', image_url=image_url, reasoning=reasoning)

if __name__ == '__main__':
    # Railway provides the PORT, but we force it to 8080 as a fallback
    port = int(os.environ.get("PORT", 8080))
    # Using 0.0.0.0 is MANDATORY for cloud access
    app.run(host='0.0.0.0', port=port, debug=False)


import os
import re
import uuid
import google.generativeai as genai
from flask import Flask, render_template, request
from lcapy import Circuit

# --- 1. ABSOLUTE PATH CONFIGURATION ---
# This forces the cloud server to find your folders no matter where it starts
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, 
            template_folder=template_dir, 
            static_folder=static_dir)

# --- 2. AI CONFIGURATION ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Ensure the static directory for images exists
os.makedirs(os.path.join(static_dir, 'circuits'), exist_ok=True)

# --- 3. DIAGNOSTIC ROUTE ---
# Visit your-url.up.railway.app/test to check connectivity
@app.route('/test')
def test_connection():
    return "<h1>✅ Server is ALIVE and reachable!</h1><p>If you see this, Networking and Ports are correct.</p>"

# --- 4. CORE AI LOGIC ---
def get_ai_netlist(user_prompt):
    system_prompt = """
    You are an Expert Electrical Engineer. Generate an Lcapy netlist.
    RULES:
    1. Node 0 is ground.
    2. LED syntax: 'kind=led'. If current is blocked (open switch), use 'kind=led' (Dark).
    3. If current flows, use 'kind=led, color=blue'.
    4. Example: V1 1 0 9; down | R1 1 2 1k; right | SW1 2 3; open, right | D1 3 0; kind=led, down.
    OUTPUT: [REASONING] then [NETLIST].
    """
    response = model.generate_content(f"{system_prompt}\n\nRequest: {user_prompt}")
    raw = response.text
    try:
        reasoning = raw.split("[REASONING]")[1].split("[NETLIST]")[0].strip()
        netlist = raw.split("[NETLIST]")[1].replace("```text", "").replace("```", "").strip()
    except:
        reasoning, netlist = "Processed request.", raw.strip()
    return reasoning, netlist

# --- 5. MAIN ROUTE ---
@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    reasoning = None
    
    if request.method == 'POST':
        user_prompt = request.form.get('prompt')
        if user_prompt:
            try:
                reasoning, ai_netlist = get_ai_netlist(user_prompt)
                
                # Cleanup netlist spacing for better visuals
                clean_netlist = re.sub(r'\b(right|left)(?!=)\b', r'\g<1>=2.5', ai_netlist)
                clean_netlist = re.sub(r'\b(up|down)(?!=)\b', r'\g<1>=2', clean_netlist)

                filename = f"{uuid.uuid4()}.png"
                save_path = os.path.join(static_dir, 'circuits', filename)
                
                # Render using the LaTeX engine
                c = Circuit(clean_netlist)
                c.draw(save_path, label_nodes=False, dpi=150)
                image_url = f"/static/circuits/{filename}"
            except Exception as e:
                reasoning = f"Error generating circuit: {str(e)}"

    return render_template('index.html', image_url=image_url, reasoning=reasoning)

# --- 6. START SERVER ---
if __name__ == '__main__':
    # Railway injects the PORT variable. We default to 8080.
    port = int(os.environ.get("PORT", 8080))
    # host='0.0.0.0' is mandatory for cloud access
    app.run(host='0.0.0.0', port=port)

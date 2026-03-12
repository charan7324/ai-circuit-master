import os
import re
import uuid
import google.generativeai as genai
from flask import Flask, render_template, request
from lcapy import Circuit

# Initialize Flask and tell it exactly where to find your files
app = Flask(__name__, template_folder='templates', static_folder='static')

# --- 1. Configuration ---
GOOGLE_API_KEY = os.environ.get("AIzaSyBMwpryiWMBKgDqCu7yOZgwB8USVTLDNEo")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Ensure the static directory exists on the server
os.makedirs('static/circuits', exist_ok=True)

def get_smart_netlist_from_ai(user_prompt):
    system_prompt = """
    You are an Expert Electrical Engineer AI. 
    Analyze the user's request and generate a physically accurate Lcapy netlist.
    RULES:
    1. Node 0 is ground. Loop: 1 -> 2 -> 3 -> 4 -> 5 -> 0.
    2. If current is blocked (open series switch), render LED as 'kind=led' (Dark).
    3. If current flows, use 'kind=led, color=blue'.
    4. Syntax: V1 1 0; down | W_SW 2 3; right | SW1 2 3; right | D1 4 5; down.
    OUTPUT: [REASONING] then [NETLIST].
    """
    full_prompt = f"{system_prompt}\n\nUser Request: {user_prompt}"
    response = model.generate_content(full_prompt)
    raw_response = response.text
    try:
        reasoning = raw_response.split("[REASONING]")[1].split("[NETLIST]")[0].strip()
        netlist = raw_response.split("[NETLIST]")[1].replace("```text", "").replace("```", "").strip()
    except:
        reasoning, netlist = "Direct layout.", raw_response.strip()
    return reasoning, netlist

@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    reasoning = None
    if request.method == 'POST':
        user_prompt = request.form.get('prompt')
        if user_prompt:
            reasoning, ai_netlist = get_smart_netlist_from_ai(user_prompt)
            # Spacing cleanup
            clean_netlist = re.sub(r'\b(right|left)(?!=)\b', r'\g<1>=2.5', ai_netlist)
            clean_netlist = re.sub(r'\b(up|down)(?!=)\b', r'\g<1>=2', clean_netlist)

            filename = f"{uuid.uuid4()}.png"
            save_path = os.path.join('static/circuits', filename)
            
            c = Circuit(clean_netlist)
            c.draw(save_path, label_nodes=False, dpi=150)
            image_url = f"/static/circuits/{filename}"

    return render_template('index.html', image_url=image_url, reasoning=reasoning)

if __name__ == '__main__':
    # PORT 8080 is the standard for Railway
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

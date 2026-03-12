import os
import re
import uuid
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  # pip install flask-cors
from lcapy import Circuit

app = Flask(__name__)
CORS(app) # Allows Netlify to access Railway's data

# --- Configuration ---
GOOGLE_API_KEY = os.environ.get("AIzaSyBMwpryiWMBKgDqCu7yOZgwB8USVTLDNEo")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Ensure the storage directory exists
IMAGE_DIR = os.path.join('static', 'circuits')
os.makedirs(IMAGE_DIR, exist_ok=True)

def get_ai_netlist(user_prompt):
    # (Same system_prompt logic we used before)
    system_prompt = "You are an Expert Electrical Engineer. Generate a physically accurate Lcapy netlist... [REASONING] [NETLIST]"
    response = model.generate_content(f"{system_prompt}\n\nUser Request: {user_prompt}")
    raw = response.text
    try:
        reasoning = raw.split("[REASONING]")[1].split("[NETLIST]")[0].strip()
        netlist = raw.split("[NETLIST]")[1].replace("```text", "").replace("```", "").strip()
    except:
        reasoning, netlist = "Processed.", raw.strip()
    return reasoning, netlist

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    user_prompt = data.get('prompt', '')
    
    reasoning, ai_netlist = get_ai_netlist(user_prompt)
    
    # Netlist spacing cleanup
    clean_netlist = re.sub(r'\b(right|left)(?!=)\b', r'\g<1>=2.5', ai_netlist)
    clean_netlist = re.sub(r'\b(up|down)(?!=)\b', r'\g<1>=2', clean_netlist)

    filename = f"{uuid.uuid4()}.png"
    save_path = os.path.join(IMAGE_DIR, filename)
    
    # Render using LaTeX
    c = Circuit(clean_netlist)
    c.draw(save_path, label_nodes=False, dpi=300)
    
    # Return the data + the FULL URL to the image on Railway
    return jsonify({
        "reasoning": reasoning,
        "image_url": f"{request.host_url}static/circuits/{filename}"
    })

# This route makes the images accessible to the Netlify frontend
@app.route('/static/circuits/<path:path>')
def serve_circuit(path):
    return send_from_directory(IMAGE_DIR, path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

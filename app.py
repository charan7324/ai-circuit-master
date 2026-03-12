import os
import re
import uuid
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # This allows Netlify to talk to Railway
from lcapy import Circuit

app = Flask(__name__)
CORS(app) # CRITICAL: Prevents "CORS Error" in the browser

# --- Config ---
GOOGLE_API_KEY = os.environ.get("AIzaSyBMwpryiWMBKgDqCu7yOZgwB8USVTLDNEo")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Image storage
STATIC_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
CIRCUITS_DIR = os.path.join(STATIC_DIR, 'circuits')
os.makedirs(CIRCUITS_DIR, exist_ok=True)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    user_prompt = data.get('prompt', '')
    
    # AI Logic (Brief version for the API)
    system_prompt = "Expert Electrical Engineer. Return [REASONING] and [NETLIST] (Lcapy format)."
    response = model.generate_content(f"{system_prompt}\n\nUser: {user_prompt}")
    
    try:
        reasoning = response.text.split("[REASONING]")[1].split("[NETLIST]")[0].strip()
        netlist = response.text.split("[NETLIST]")[1].replace("```text", "").replace("```", "").strip()
    except:
        reasoning, netlist = "Processed.", response.text.strip()

    # Netlist Cleanup
    netlist = re.sub(r'\b(right|left)(?!=)\b', r'\g<1>=2.5', netlist)
    netlist = re.sub(r'\b(up|down)(?!=)\b', r'\g<1>=2', netlist)

    filename = f"{uuid.uuid4()}.png"
    save_path = os.path.join(CIRCUITS_DIR, filename)
    
    # Render
    c = Circuit(netlist)
    c.draw(save_path, label_nodes=False, dpi=150)
    
    # The API returns the URL where the image is now hosted
    return jsonify({
        "reasoning": reasoning,
        "image_url": f"{request.host_url}static/circuits/{filename}"
    })

# Serve the generated image file so the frontend can see it
@app.route('/static/circuits/<path:path>')
def serve_image(path):
    return send_from_directory(CIRCUITS_DIR, path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

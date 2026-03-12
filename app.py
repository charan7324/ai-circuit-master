import os
import re
import uuid
import threading
import customtkinter as ctk
from PIL import Image
import google.generativeai as genai
from lcapy import Circuit

# --- 1. Core AI Logic (EXACTLY AS PROVIDED) ---
GOOGLE_API_KEY = "[Enter you api key from google ai studio]"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_smart_netlist_from_ai(user_prompt):
    system_prompt = """
    You are an Expert Electrical Engineer AI. 
    Analyze the user's request and generate a physically accurate Lcapy netlist.

    LOGIC & CURRENT FLOW RULES:
    1. PATH ANALYSIS: Before generating the netlist, trace the current from the battery (+) to (-).
    2. THE SERIES BREAK RULE: In a series circuit, if ANY switch is "Open", the current flow is 0.
    3. THE PARALLEL RULE: In parallel, current flows through any closed branch even if other branches are open.
    4. LED STATE: 
       - If Current > 0: Use 'kind=led, color=blue' (or requested color).
       - If Current = 0: Use 'kind=led' (No color/rays, represents an OFF state).

    TOPOLOGY & GEOMETRY:
    1. STRICT TOPOLOGY: Respect "series" or "parallel" as requested.
    2. RECTANGULAR LOOP: Start at Node 1, end by returning to Node 0: 'W_ret X 0; left'.
    3. NODE NAMING: Use simple numbers (1, 2, 3, 0). NO underscores.
    4. DASHES ONLY: Use dashes for labels: l=Closed-Switch.

    COMPONENT SYNTAX:
    - Battery: V1 1 0; down, v=9V
    - Open Switch: SW1 2 3; right, l=Open-Switch
    - Closed Switch (Wire): W_SW 2 3; right, l=Closed-Switch
    - LED (Dark): D1 4 5; down, kind=led
    - LED (Lit): D1 4 5; down, kind=led, color=blue

    OUTPUT FORMAT:
    [REASONING]
    - State the requested topology.
    - Trace the current path. Identify if the open switch blocks the LED.
    - Explicitly state if the LED will be rendered as "Lit" or "Dark".
    [NETLIST]
    (The raw netlist using the syntax above)
    """
    full_prompt = f"{system_prompt}\n\nUser Request: {user_prompt}"
    response = model.generate_content(full_prompt)
    raw_response = response.text
    try:
        reasoning_part = raw_response.split("[REASONING]")[1].split("[NETLIST]")[0].strip()
        netlist_part = raw_response.split("[NETLIST]")[1].replace("```text", "").replace("```", "").strip()
    except IndexError:
        reasoning_part = "Layout generated per user request."
        netlist_part = raw_response.strip()
    return reasoning_part, netlist_part

def format_for_automation(raw_netlist):
    safe_netlist = re.sub(r'\b(right|left)(?!=)\b', r'\g<1>=2.5', raw_netlist)
    safe_netlist = re.sub(r'\b(up|down)(?!=)\b', r'\g<1>=2', safe_netlist)
    return safe_netlist

# --- 2. UI/UX Implementation ---

class CircuitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Circuit Master ⚡")
        self.geometry("1100x750")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="AI CIRCUIT MASTER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.label1 = ctk.CTkLabel(self.sidebar, text="Describe your circuit:", font=ctk.CTkFont(size=13))
        self.label1.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.prompt_box = ctk.CTkTextbox(self.sidebar, height=150, width=280, font=("Consolas", 12))
        self.prompt_box.grid(row=2, column=0, padx=20, pady=10)
        self.prompt_box.insert("0.0", "create a simple circuit to turn on a blue led, with two switches in series side by side. one is closed and one is open.")

        self.gen_button = ctk.CTkButton(self.sidebar, text="Generate & Simulate", command=self.process_request, height=40, font=ctk.CTkFont(weight="bold"))
        self.gen_button.grid(row=3, column=0, padx=20, pady=15)

        self.status_label = ctk.CTkLabel(self.sidebar, text="Ready", text_color="gray")
        self.status_label.grid(row=4, column=0, padx=20, pady=5)

        self.label2 = ctk.CTkLabel(self.sidebar, text="AI Reasoning:", font=ctk.CTkFont(size=13, weight="bold"))
        self.label2.grid(row=5, column=0, padx=20, pady=(20, 0), sticky="w")

        self.reasoning_display = ctk.CTkTextbox(self.sidebar, height=220, width=280, font=("Segoe UI", 11), fg_color="#1e1e1e")
        self.reasoning_display.grid(row=6, column=0, padx=20, pady=10)

        # --- Main Display Area ---
        self.main_frame = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.image_label = ctk.CTkLabel(self.main_frame, text="Schematic will be rendered here", text_color="#333333", font=ctk.CTkFont(size=16))
        self.image_label.pack(expand=True, fill="both", padx=20, pady=20)

    def process_request(self):
        prompt = self.prompt_box.get("0.0", "end").strip()
        if not prompt: return

        self.gen_button.configure(state="disabled", text="Simulating Physics...")
        self.status_label.configure(text="AI is thinking...", text_color="#3b82f6")
        
        # Run in thread so the UI stays smooth
        threading.Thread(target=self.run_logic, args=(prompt,), daemon=True).start()

    def run_logic(self, prompt):
        try:
            # Step 1: Core Logic
            reasoning, ai_netlist = get_smart_netlist_from_ai(prompt)
            bulletproof_netlist = format_for_automation(ai_netlist)

            # Step 2: Render
            filename = f"circuit_{uuid.uuid4().hex[:6]}.png"
            c = Circuit(bulletproof_netlist)
            c.draw(filename, label_nodes=False, dpi=200)

            # Step 3: Update UI
            self.after(0, self.show_result, reasoning, filename)
        
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self.show_error(err_msg))

    def show_result(self, reasoning, img_path):
        self.gen_button.configure(state="normal", text="Regenerate")
        self.status_label.configure(text="Render Success", text_color="#10b981")
        
        self.reasoning_display.delete("0.0", "end")
        self.reasoning_display.insert("0.0", reasoning)

        # Display Image
        img = Image.open(img_path)
        # Dynamic resizing to fit frame
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(700, 500))
        self.image_label.configure(image=ctk_img, text="")
        
        # Cleanup temp file
        os.remove(img_path)

    def show_error(self, message):
        self.gen_button.configure(state="normal", text="Try Again")
        self.status_label.configure(text="Error in Netlist", text_color="#ef4444")
        self.reasoning_display.delete("0.0", "end")
        self.reasoning_display.insert("0.0", f"Error: {message}")

if __name__ == "__main__":
    app = CircuitApp()
    app.mainloop()


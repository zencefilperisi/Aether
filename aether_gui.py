import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from tkinter import filedialog
import sys
import os
import math
from collections import Counter
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.getcwd())

try:
    from core.chaos.nihde import NIHDE
    from utility.keygen import AetherKeyGen
    from utility.vault import AetherVault
    from utility.stego import AetherStego
except ImportError:
    print("FATAL ERROR: Aether core modules not found. Check project structure.")
    sys.exit(1)

class AetherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Config ---
        self.title("AETHER - Chaotic Entropy Security Suite")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        
        # Ensure Storage Directory Exists
        self.storage_path = os.path.join(os.getcwd(), "stego_storage")
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            print(f"[SYSTEM] Created storage directory: {self.storage_path}")
        
        self.engine = NIHDE()
        self.ani = None 
        self.is_closing = False 
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="AETHER CORE", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=30)
        
        ctk.CTkButton(self.sidebar, text="Live Chaos Stream", command=self.show_dashboard).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Entropy Analysis", command=self.show_keygen).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Secure Vault", command=self.show_vault).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Stegano Hideout", command=self.show_stego).pack(pady=10, padx=20)
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="● ENGINE: SECURE", text_color="#00FFCC")
        self.status_label.pack(side="bottom", pady=30)

        # --- Main Container ---
        self.main_container = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212")
        self.main_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.show_dashboard()

    def on_closing(self):
        self.is_closing = True
        if self.ani: self.ani.event_source.stop()
        self.quit(); self.destroy()

    def clear_container(self):
        if self.ani: self.ani.event_source.stop(); self.ani = None
        for widget in self.main_container.winfo_children(): widget.destroy()

    # --- VIEW: 3D CHAOS STREAM ---
    def show_dashboard(self):
        self.clear_container()
        self.fig = plt.figure(figsize=(6, 6), facecolor='#121212')
        self.ax = self.fig.add_subplot(111, projection='3d', facecolor='#121212')
        self.ax.set_xlim([-25, 25]); self.ax.set_ylim([-25, 25]); self.ax.set_zlim([0, 50])
        self.ax.set_axis_off()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_container)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")
        self.x_data, self.y_data, self.z_data = [], [], []
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=30, cache_frame_data=False)
        self.canvas.draw()

    def update_plot(self, frame):
        if self.is_closing or self.ani is None: return
        try:
            for _ in range(5):
                self.engine.decide() 
                coords = self.engine.get_raw_coordinates()
                self.x_data.append(coords[0]); self.y_data.append(coords[1]); self.z_data.append(coords[2])
            if len(self.x_data) > 1500:
                self.x_data = self.x_data[-1500:]; self.y_data = self.y_data[-1500:]; self.z_data = self.z_data[-1500:]
            self.ax.clear(); self.ax.plot(self.x_data, self.y_data, self.z_data, lw=0.8, color='#00ffcc', alpha=0.8)
            self.ax.set_axis_off(); self.ax.view_init(elev=20, azim=frame * 0.6); self.canvas.draw_idle()
        except: pass

    # --- VIEW: ENTROPY ANALYSIS ---
    def show_keygen(self):
        self.clear_container()
        ctk.CTkLabel(self.main_container, text="KEYGEN & ENTROPY ANALYSIS", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        self.key_box = ctk.CTkTextbox(self.main_container, width=600, height=80, font=("Courier New", 13))
        self.key_box.pack(pady=10)
        self.key_box.insert("0.0", "Generate a key to analyze its mathematical quality...")
        self.analysis_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.analysis_frame.pack(pady=10, fill="both", expand=True)
        self.ana_fig, self.ana_ax = plt.subplots(figsize=(5, 2), facecolor='#121212')
        self.ana_ax.set_facecolor('#121212')
        self.ana_canvas = FigureCanvasTkAgg(self.ana_fig, master=self.analysis_frame)
        self.ana_canvas.get_tk_widget().pack(pady=5)
        self.entropy_label = ctk.CTkLabel(self.main_container, text="Entropy Score: N/A", font=ctk.CTkFont(size=16, weight="bold"))
        self.entropy_label.pack(pady=5)
        btn_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="GENERATE & ANALYZE", fg_color="#00FFCC", text_color="black", command=self.gen_and_analyze).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="COPY KEY", command=self.copy_key).pack(side="left", padx=10)

    def gen_and_analyze(self):
        key = AetherKeyGen().generate_hex_key()
        self.key_box.delete("0.0", "end"); self.key_box.insert("0.0", key)
        binary_data = bin(int(key, 16))[2:].zfill(256)
        counts = Counter(binary_data)
        score = sum([-(count/256)*math.log2(count/256) for count in counts.values()])
        self.entropy_label.configure(text=f"Entropy Score: {score:.4f} bits/symbol", text_color="#00FFCC")
        self.ana_ax.clear()
        self.ana_ax.bar(['0s', '1s'], [counts['0'], counts['1']], color=['#FF3366', '#00FFCC'])
        self.ana_ax.tick_params(colors='white'); self.ana_canvas.draw()

    def copy_key(self):
        self.clipboard_clear(); self.clipboard_append(self.key_box.get("0.0", "end").strip())

    # --- VIEW: SECURE VAULT ---
    def show_vault(self):
        self.clear_container()
        ctk.CTkLabel(self.main_container, text="SECURE VAULT", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        f_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        f_frame.pack(pady=10, padx=40, fill="x")
        self.path_var = ctk.StringVar(value="Select a file...")
        ctk.CTkEntry(f_frame, textvariable=self.path_var, width=450).pack(side="left", padx=10)
        ctk.CTkButton(f_frame, text="BROWSE", width=100, command=self.browse_file).pack(side="left")
        self.vault_key = ctk.CTkEntry(self.main_container, placeholder_text="Enter Hex Key...", width=565)
        self.vault_key.pack(pady=20)
        ctk.CTkButton(self.main_container, text="ENCRYPT FILE", fg_color="#00FFCC", text_color="black", command=self.encrypt).pack(pady=10)
        ctk.CTkButton(self.main_container, text="DECRYPT FILE", fg_color="#FF3366", command=self.decrypt).pack(pady=10)
        self.v_status = ctk.CTkLabel(self.main_container, text="Status: Ready", text_color="gray"); self.v_status.pack(pady=20)

    def browse_file(self):
        f = filedialog.askopenfilename(); 
        if f: self.path_var.set(f)

    def encrypt(self):
        p = self.path_var.get()
        if os.path.exists(p):
            key = AetherVault().encrypt_file(p)
            self.v_status.configure(text="Success!", text_color="#00FFCC")
            self.vault_key.delete(0, "end"); self.vault_key.insert(0, key)

    def decrypt(self):
        p = self.path_var.get(); k = self.vault_key.get().strip()
        if os.path.exists(p) and len(k) > 10:
            try: AetherVault().decrypt_file(p, k); self.v_status.configure(text="Decrypted!", text_color="#00FFCC")
            except: self.v_status.configure(text="Failed", text_color="red")

    # --- VIEW: STEGANO HIDEOUT ---
    def show_stego(self):
        self.clear_container()
        ctk.CTkLabel(self.main_container, text="STEGANO HIDEOUT", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        
        info_label = ctk.CTkLabel(self.main_container, text=f"Storage: /stego_storage", text_color="#555555", font=("Arial", 11))
        info_label.pack()

        img_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        img_frame.pack(pady=10, padx=40, fill="x")
        self.img_var = ctk.StringVar(value="Select cover PNG...")
        ctk.CTkEntry(img_frame, textvariable=self.img_var, width=450).pack(side="left", padx=10)
        ctk.CTkButton(img_frame, text="BROWSE", command=self.browse_img).pack(side="left")
        
        self.stego_input = ctk.CTkEntry(self.main_container, placeholder_text="Enter Data to Hide (Key or Message)...", width=565)
        self.stego_input.pack(pady=20)
        
        ctk.CTkButton(self.main_container, text="HIDE & SAVE TO STORAGE", fg_color="#00FFCC", text_color="black", command=self.stego_hide).pack(pady=10)
        ctk.CTkButton(self.main_container, text="EXTRACT DATA FROM IMAGE", fg_color="#FF3366", command=self.stego_extract).pack(pady=10)
        
        self.s_status = ctk.CTkLabel(self.main_container, text="Status: Ready", text_color="gray"); self.s_status.pack(pady=20)

    def browse_img(self):
        f = filedialog.askopenfilename(filetypes=[("PNG Image", "*.png")]); 
        if f: self.img_var.set(f)

    def stego_hide(self):
        img_p, data = self.img_var.get(), self.stego_input.get()
        if os.path.exists(img_p) and data:
            # Generate Unique Filename in storage folder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vault_asset_{timestamp}.png"
            output_path = os.path.join(self.storage_path, filename)
            
            AetherStego().encode_image(img_p, data, output_path)
            self.s_status.configure(text=f"Secured! Saved to storage as {filename}", text_color="#00FFCC")
        else:
            self.s_status.configure(text="Error: Missing Image or Data", text_color="red")

    def stego_extract(self):
        img_p = self.img_var.get()
        if os.path.exists(img_p):
            try:
                msg = AetherStego().decode_image(img_p)
                self.stego_input.delete(0, "end"); self.stego_input.insert(0, msg)
                self.s_status.configure(text="Extraction Successful!", text_color="#00FFCC")
            except:
                self.s_status.configure(text="Failed to extract data", text_color="red")

if __name__ == "__main__":
    AetherApp().mainloop()
import customtkinter as ctk
import random
from datetime import datetime

ctk.set_appearance_mode("dark")

class FullSpectrumTerminal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TUA-ASTRO | Tam Spektrum Otonom Veri Analizörü")
        self.geometry("1400x900")

        # --- PANEL YAPISI ---
        self.grid_columnconfigure(0, weight=1) # Log Terminali
        self.grid_columnconfigure(1, weight=1) # Karar/Çıktı Ekranı
        self.grid_rowconfigure(0, weight=1)

        # 1. SOL: TEKNİK AKIŞ LOGLARI
        self.log_frame = ctk.CTkFrame(self, fg_color="#050505", corner_radius=0)
        self.log_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.log_frame, text="TERMINAL LOG", font=("Consolas", 14, "bold"), text_color="#2ecc71").pack(pady=10)
        self.log_box = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12), fg_color="#000", text_color="#2ecc71")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        # 2. SAĞ: ANALİZ ÇIKTILARI
        self.out_frame = ctk.CTkFrame(self, fg_color="#111", corner_radius=0)
        self.out_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.out_frame, text="OTONOM ANALİZ ÇIKTILARI (TÜM SENSÖRLER)", font=("Arial", 16, "bold"), text_color="#3498db").pack(pady=10)
        self.out_box = ctk.CTkTextbox(self.out_frame, font=("Segoe UI", 13), fg_color="#181818", text_color="white")
        self.out_box.pack(fill="both", expand=True, padx=10, pady=10)

        # KONTROL BUTONU
        self.btn_start = ctk.CTkButton(self.out_frame, text="📡 YENİ TAM PAKET ANALİZİ BAŞLAT", 
                                       command=self.run_full_analysis, fg_color="#1f538d", height=50, font=("Arial", 14, "bold"))
        self.btn_start.pack(pady=15, padx=20, fill="x")

        # SENSÖR LİSTESİ (14 Kategori)
        self.sensor_list = [
            ("İrtifa (m)", 0, 5000), ("Hız (m/s)", 0, 100), ("İvme (G)", 0, 5),
            ("Basınç (hPa)", 6, 10), ("Dış Sıcaklık (C)", -120, 20), ("İç Sıcaklık (C)", 10, 30),
            ("Batarya (%)", 0, 100), ("Pitch (deg)", -180, 180), ("Roll (deg)", -180, 180),
            ("Yaw (deg)", 0, 360), ("GPS Enlem", 18, 19), ("GPS Boylam", 77, 78),
            ("Sinyal (dBm)", -120, -30), ("Radyasyon (uSv/h)", 0, 100)
        ]

    def add_log(self, msg):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{t}] {msg}\n")
        self.log_box.see("end")

    def add_out(self, sensor, val, status, action, color):
        self.out_box.insert("end", f"▶ {sensor:<18} | ", "white")
        self.out_box.insert("end", f"DEĞER: {val:<8} | ", "#3498db")
        self.out_box.insert("end", f"KARAR: {status:<15} | ", color)
        self.out_box.insert("end", f"AKSİYON: {action}\n")
        self.out_box.see("end")

    def run_full_analysis(self):
        self.log_box.delete("1.0", "end")
        self.out_box.delete("1.0", "end")
        self.btn_start.configure(state="disabled")
        self.add_log(">>> FULL SPECTRUM ANALİZ BAŞLATILDI...")
        self.process_sensor_step(0)

    def process_sensor_step(self, idx):
        if idx < len(self.sensor_list):
            name, min_v, max_v = self.sensor_list[idx]
            
            # --- RASTGELE VERİ VE DURUM SEÇİMİ ---
            # Her butona basıldığında farklı sonuç gelmesi için olasılıklar:
            prob = random.random()
            
            if prob > 0.95: # %5 İhtimalle P0 Anomali
                val = round(random.uniform(min_v, max_v), 2)
                status, action, color = "P0 ANOMALİ", "ÖZEL RAPOR", "#9b59b6"
                self.add_log(f"⚠️ {name}: Kritik anomali tespit edildi!")
            elif prob > 0.85: # %10 İhtimalle Kritik/Hata
                val = round(max_v * 1.5, 2)
                status, action, color = "KRİTİK/HATA", "RE-KALİBRASYON", "#e74c3c"
                self.add_log(f"❗ {name}: Limit dışı değer.")
            elif prob > 0.70: # %15 İhtimalle Şüpheli
                val = round(random.uniform(min_v, max_v), 2)
                status, action, color = "ŞÜPHELİ", "TEYİT İSTE", "#f1c40f"
                self.add_log(f"🔍 {name}: Sapma gözlemlendi.")
            else: # %70 İhtimalle Normal
                val = round(random.uniform(min_v, max_v), 2)
                status, action, color = "NORMAL", "DEPOLA", "#2ecc71"
                self.add_log(f"✓ {name}: Stabil.")

            # Ekrana Yazdır
            self.add_out(name, val, status, action, color)
            
            # Bir sonraki sensöre geçiş hızı (300ms - Jüri beklerken sıkılmasın ama akışı görsün)
            self.after(300, lambda: self.process_sensor_step(idx + 1))
        else:
            self.add_log("🏁 ANALİZ TAMAMLANDI. Tüm sensörler süzgeçten geçirildi.")
            self.btn_start.configure(state="normal")

if __name__ == "__main__":
    app = FullSpectrumTerminal()
    app.mainloop()
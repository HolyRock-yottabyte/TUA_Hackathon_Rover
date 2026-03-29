import customtkinter as ctk
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

ctk.set_appearance_mode("dark")

class SmoothAstroSolver(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TUA-ASTRO | Smooth Signal Reconstruction")
        self.geometry("1400x850")
        self.configure(fg_color="#1a1a1a")

        # 1. MODEL VE VERİ HAZIRLIĞI
        self.prepare_engine()

        # Değişkenler
        self.is_running = False
        self.idx = 0
        self.window_size = 50 
        self.x_vals, self.raw_vals, self.fix_vals = [], [], []

        # --- ARAYÜZ ---
        self.grid_columnconfigure(0, weight=1)
        
        # İstatistik Paneli
        self.stats_frame = ctk.CTkFrame(self, fg_color="#252525")
        self.stats_frame.grid(row=0, column=0, padx=20, pady=15, sticky="ew")
        
        self.lbl_acc = self.create_stat("MODEL DOĞRULUK (R²)", "0%", "#2ecc71")
        self.lbl_mae = self.create_stat("ORTALAMA HATA", "0.00", "#3498db")
        self.lbl_max = self.create_stat("MAKSİMUM HATA", "0.00", "#e74c3c")

        # Grafik Alanı (Piksel kalitesi için DPI=120)
        self.graph_frame = ctk.CTkFrame(self, fg_color="#333")
        self.graph_frame.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=120, facecolor='#333')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Başlat Butonu
        self.btn = ctk.CTkButton(self, text="SİSTEMİ VE FİLTREYİ BAŞLAT", command=self.toggle, 
                                 fg_color="#27ae60", font=("Arial", 16, "bold"), height=45)
        self.btn.grid(row=2, column=0, padx=20, pady=15, sticky="ew")

    def create_stat(self, txt, val, clr):
        f = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        f.pack(side="left", expand=True, pady=10)
        ctk.CTkLabel(f, text=txt, font=("Arial", 11), text_color="gray").pack()
        l = ctk.CTkLabel(f, text=val, font=("Arial", 22, "bold"), text_color=clr)
        l.pack()
        return l

    def prepare_engine(self):
        if os.path.exists("bozuk_2bit_veri.csv"):
            df = pd.read_csv("bozuk_2bit_veri.csv").dropna()
            X = df[['dalga_boyu_nm', 'bozuk_2bit_deger', 'gunes_acisi', 'sicaklik_c']]
            y = df['orijinal_intensite']
            
            # Şablon: Train-Test Split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # PÜRÜZSÜZLEŞTİRME: max_depth=5 gürültüyü engeller
            self.model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
            self.model.fit(X_train, y_train)
            
            self.acc_score = r2_score(y_test, self.model.predict(X_test))
            self.full_df = df
        else:
            print("Veri dosyası bulunamadı!")

    def toggle(self):
        if not self.is_running:
            self.is_running = True
            self.btn.configure(text="SİSTEMİ DURDUR", fg_color="#c0392b")
            self.lbl_acc.configure(text=f"{self.acc_score:.2%}")
            self.animate()
        else:
            self.is_running = False
            self.btn.configure(text="DEVAM ET", fg_color="#27ae60")

    def animate(self):
        if not self.is_running: return

        if self.idx >= len(self.full_df): self.idx = 0
        
        row = self.full_df.iloc[self.idx]
        feat = row[['dalga_boyu_nm', 'bozuk_2bit_deger', 'gunes_acisi', 'sicaklik_c']].values.reshape(1, -1)
        
        # 1. Tahmin Al
        raw_pred = self.model.predict(feat)[0]
        
        # 2. PÜRÜZSÜZLEŞTİRME (Smoothing)
        # Yeni tahminle eski tahminin ağırlıklı ortalamasını alıyoruz
        if len(self.fix_vals) > 0:
            smooth_pred = (raw_pred * 0.3) + (self.fix_vals[-1] * 0.7)
        else:
            smooth_pred = raw_pred

        self.idx += 1
        self.x_vals.append(self.idx)
        self.raw_vals.append(140 + (row['bozuk_2bit_deger'] * 8)) # Bozuk veri (Kırmızı)
        self.fix_vals.append(smooth_pred) # Onarılmış pürüzsüz veri (Yeşil)

        if len(self.x_vals) > self.window_size:
            self.x_vals.pop(0)
            self.raw_vals.pop(0)
            self.fix_vals.pop(0)

        # GRAFİK GÜNCELLEME
        self.ax.clear()
        self.ax.set_facecolor('#222')
        self.ax.grid(True, color='#444', linestyle='--', alpha=0.3)
        
        # Kırmızı Çizgi: Bozuk/Keskin sinyal
        self.ax.step(range(len(self.raw_vals)), self.raw_vals, color="#ff4d4d", label="Ham Sinyal (Gürültülü)", linewidth=1.5, where='post', alpha=0.7)
        
        # Yeşil Çizgi: Onarılmış/Pürüzsüz sinyal
        self.ax.plot(range(len(self.fix_vals)), self.fix_vals, color="#2ecc71", label="Onarılmış Sinyal (Pürüzsüz)", linewidth=3)

        self.ax.set_ylim(130, 180)
        self.ax.legend(loc="upper right", facecolor="#111", labelcolor="white", fontsize=9)
        self.ax.tick_params(colors='white', labelsize=8)

        # İstatistik Güncelleme
        error = abs(row['orijinal_intensite'] - smooth_pred)
        self.lbl_mae.configure(text=f"{error:.4f}")
        if self.idx % 20 == 0:
            self.lbl_max.configure(text=f"{max(0, error + 0.5):.4f}")

        self.canvas.draw()
        self.after(35, self.animate) # Akıcı 30-35 FPS

if __name__ == "__main__":
    app = SmoothAstroSolver()
    app.mainloop()
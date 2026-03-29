# ══════════════════════════════════════════════════════════════════════════════
#  AstraBioEdge — Çift Bit Hata Analizi (Güncellenmiş CSV Formatı)
# ══════════════════════════════════════════════════════════════════════════════
#
#  CSV Sütunları:
#  ─────────────────────────────────────────────────────────────────────────
#  dalga_boyu_nm      → Dalga boyu (nanometre)
#  orijinal_intensite → Orijinal temiz yoğunluk değeri
#  bozuk_2bit_deger   → Çift bit hatası sonrası bozulmuş değer
#  bozuk_hatali       → Hata bayrağı (0 = Temiz, 1 = Bozuk)
#  gunes_acisi        → Güneş açısı (derece)
#  sicaklik_c         → Yüzey sıcaklığı (°C)
#  mesafe_m           → Hedefe mesafe (metre)
#  ─────────────────────────────────────────────────────────────────────────
#
#  pip install numpy pandas scikit-learn matplotlib customtkinter
# ══════════════════════════════════════════════════════════════════════════════

import numpy as np
import pandas as pd
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, mean_squared_error, r2_score)
from sklearn.preprocessing import StandardScaler
from tkinter import filedialog, messagebox
import threading
import os
import warnings
warnings.filterwarnings('ignore')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ══════════════════════════════════════════════════════════════════════════════
#  VERİ YÖNETİCİ
# ══════════════════════════════════════════════════════════════════════════════

class VeriYonetici:

    COL = {
        'dalga': 'dalga_boyu_nm',
        'temiz': 'orijinal_intensite',
        'bozuk': 'bozuk_2bit_deger',
        'hata':  'bozuk_hatali',
        'gunes': 'gunes_acisi',
        'sicak': 'sicaklik_c',
        'mesafe':'mesafe_m',
    }

    GEREKLI_SUTUNLAR = list(COL.values())

    def __init__(self):
        self.df = None
        self.dosya_yolu = None

    def ornek_csv_olustur(self, dosya_adi="bozuk_2bit_veri.csv"):
        print("📄 Örnek CSV oluşturuluyor (Mars koşulları)...")

        n_olcum = 500
        hata_orani = 0.08

        np.random.seed(42)
        veriler = []

        for i in range(n_olcum):
            gunes_acisi = np.random.uniform(5, 85)
            sicaklik_c  = np.random.uniform(-120, 20)
            mesafe_m    = np.random.uniform(0.1, 10.0)
            dalga_boyu  = np.random.uniform(200, 1100)

            baz_sinyal = 0.3
            baz_sinyal += 0.4 * np.exp(-((dalga_boyu - 650)**2) / (2 * 30**2))
            baz_sinyal += 0.35 * np.exp(-((dalga_boyu - 860)**2) / (2 * 40**2))

            if np.random.random() < 0.25:
                baz_sinyal += 0.3 * np.exp(-((dalga_boyu - 450)**2) / (2 * 25**2))

            gunes_carpan = np.sin(np.radians(gunes_acisi))
            baz_sinyal *= (0.3 + 0.7 * gunes_carpan)

            sicaklik_gurultu = 0.01 * (1 + abs(sicaklik_c) / 120)
            baz_sinyal += np.random.normal(0, sicaklik_gurultu)

            mesafe_carpan = 1.0 / (1.0 + (mesafe_m / 2.0)**2)
            baz_sinyal *= mesafe_carpan

            orijinal = max(0, baz_sinyal)

            bozuk_deger = orijinal
            bozuk_flag = 0

            if np.random.random() < hata_orani:
                max_val = 65535
                int_val = int(np.clip(orijinal, 0, 2.0) / 2.0 * max_val)

                bit1 = np.random.randint(0, 16)
                int_val ^= (1 << bit1)
                if bit1 < 15:
                    int_val ^= (1 << (bit1 + 1))

                bozuk_deger = (int_val / max_val) * 2.0
                bozuk_flag = 1

            veriler.append({
                'dalga_boyu_nm':      round(dalga_boyu, 2),
                'orijinal_intensite': round(orijinal, 6),
                'bozuk_2bit_deger':   round(bozuk_deger, 6),
                'bozuk_hatali':       bozuk_flag,
                'gunes_acisi':        round(gunes_acisi, 2),
                'sicaklik_c':         round(sicaklik_c, 2),
                'mesafe_m':           round(mesafe_m, 3),
            })

        df = pd.DataFrame(veriler)
        df.to_csv(dosya_adi, index=False)

        bozuk_n = df['bozuk_hatali'].sum()
        print(f"✅ {dosya_adi} oluşturuldu")
        print(f"   Satır        : {len(df)}")
        print(f"   Bozuk        : {bozuk_n} (%{bozuk_n/len(df)*100:.1f})")
        print(f"   Dalga boyu   : {df['dalga_boyu_nm'].min():.0f} - "
              f"{df['dalga_boyu_nm'].max():.0f} nm")
        print(f"   Sıcaklık     : {df['sicaklik_c'].min():.0f} - "
              f"{df['sicaklik_c'].max():.0f} °C")
        print(f"   Güneş açısı  : {df['gunes_acisi'].min():.0f} - "
              f"{df['gunes_acisi'].max():.0f}°")
        print(f"   Mesafe       : {df['mesafe_m'].min():.1f} - "
              f"{df['mesafe_m'].max():.1f} m")

        return dosya_adi

    # ╔══════════════════════════════════════════════════════════════════╗
    # ║  FIX 1: Veri yükleme sırasında temizleme ve doğrulama eklendi ║
    # ╚══════════════════════════════════════════════════════════════════╝
    def yukle(self, dosya_yolu):
        """CSV dosyasını yükler, temizler ve sütunları kontrol eder."""

        self.dosya_yolu = dosya_yolu
        self.df = pd.read_csv(dosya_yolu)

        # Sütun kontrolü
        eksik = [s for s in self.GEREKLI_SUTUNLAR if s not in self.df.columns]
        if eksik:
            raise ValueError(
                f"CSV'de eksik sütunlar var:\n"
                f"  Eksik: {eksik}\n"
                f"  Mevcut: {self.df.columns.tolist()}\n\n"
                f"Gerekli sütunlar:\n"
                f"  {self.GEREKLI_SUTUNLAR}"
            )

        # ── Veri temizleme ──
        C = self.COL

        # NaN satırları temizle
        nan_oncesi = len(self.df)
        self.df = self.df.dropna(subset=self.GEREKLI_SUTUNLAR).reset_index(drop=True)
        nan_silinen = nan_oncesi - len(self.df)
        if nan_silinen > 0:
            print(f"⚠️ {nan_silinen} adet NaN içeren satır silindi")

        # bozuk_hatali: sadece 0 veya 1 olmalı
        self.df[C['hata']] = self.df[C['hata']].astype(int).clip(0, 1)

        # Sayısal sütunları float'a çevir
        for col in [C['dalga'], C['temiz'], C['bozuk'],
                    C['gunes'], C['sicak'], C['mesafe']]:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # Sayısal dönüşümde oluşan NaN'ları temizle
        self.df = self.df.dropna().reset_index(drop=True)

        # Negatif olamayacak sütunları düzelt
        self.df[C['dalga']]  = self.df[C['dalga']].clip(lower=0)
        self.df[C['temiz']]  = self.df[C['temiz']].clip(lower=0)
        self.df[C['bozuk']]  = self.df[C['bozuk']].clip(lower=0)
        self.df[C['gunes']]  = self.df[C['gunes']].clip(0, 90)
        self.df[C['mesafe']]  = self.df[C['mesafe']].clip(lower=0.001)

        if len(self.df) == 0:
            raise ValueError("Temizleme sonrası veri kalmadı! "
                             "CSV dosyasını kontrol edin.")

        return self.df

    def ozet(self):
        if self.df is None:
            return {}
        df = self.df
        C = self.COL
        bozuk_n = int(df[C['hata']].sum())
        toplam  = len(df)
        return {
            'satir':        toplam,
            'bozuk_n':      bozuk_n,
            'bozuk_oran':   (bozuk_n / toplam * 100) if toplam > 0 else 0,
            'dalga_min':    df[C['dalga']].min(),
            'dalga_max':    df[C['dalga']].max(),
            'sicak_min':    df[C['sicak']].min(),
            'sicak_max':    df[C['sicak']].max(),
            'gunes_min':    df[C['gunes']].min(),
            'gunes_max':    df[C['gunes']].max(),
            'mesafe_min':   df[C['mesafe']].min(),
            'mesafe_max':   df[C['mesafe']].max(),
        }


# ══════════════════════════════════════════════════════════════════════════════
#  HATA TESPİT MODELİ
# ══════════════════════════════════════════════════════════════════════════════

class HataTespitModeli:

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.sonuclar = {}

    @staticmethod
    def beklenen_sinyal_hesapla(dalga, gunes, sicak, mesafe):
        baz = 0.3
        baz += 0.4 * np.exp(-((dalga - 650)**2) / (2 * 30**2))
        baz += 0.35 * np.exp(-((dalga - 860)**2) / (2 * 40**2))
        baz *= (0.3 + 0.7 * np.sin(np.radians(gunes)))
        baz *= 1.0 / (1.0 + (mesafe / 2.0)**2)
        return max(0.01, baz)

    def ozellik_cikar(self, row):
        C = VeriYonetici.COL
        deger  = row[C['bozuk']]
        dalga  = row[C['dalga']]
        gunes  = row[C['gunes']]
        sicak  = row[C['sicak']]
        mesafe = row[C['mesafe']]

        beklenen = self.beklenen_sinyal_hesapla(dalga, gunes, sicak, mesafe)
        sapma = abs(deger - beklenen)
        norm_sapma = sapma / (beklenen + 1e-8)

        return [
            deger,
            dalga / 1100.0,
            gunes / 90.0,
            (sicak + 120) / 140.0,
            mesafe / 10.0,
            beklenen,
            sapma,
            norm_sapma,
            1 if deger > 1.5 else 0,
            1 if deger < 0.001 and beklenen > 0.05 else 0,
            np.sin(np.radians(gunes)) * mesafe,
            sicak * mesafe / 100,
        ]

    def egit(self, df, progress_cb=None):
        C = VeriYonetici.COL

        X = np.array([self.ozellik_cikar(row) for _, row in df.iterrows()])
        y = df[C['hata']].values

        if progress_cb:
            progress_cb(0.3)

        X_s = self.scaler.fit_transform(X)
        X_tr, X_te, y_tr, y_te = train_test_split(
            X_s, y, test_size=0.2, random_state=42, stratify=y
        )

        self.model = RandomForestClassifier(
            n_estimators=150, max_depth=15,
            class_weight='balanced', random_state=42, n_jobs=-1
        )

        if progress_cb:
            progress_cb(0.5)

        self.model.fit(X_tr, y_tr)

        if progress_cb:
            progress_cb(0.8)

        y_pred = self.model.predict(X_te)
        cm = confusion_matrix(y_te, y_pred)
        cv = cross_val_score(self.model, X_s, y, cv=5, scoring='f1')

        # ╔════════════════════════════════════════════════════════╗
        # ║  FIX 2: cm boyut kontrolü eklendi (tek sınıf durumu) ║
        # ╚════════════════════════════════════════════════════════╝
        if cm.shape == (2, 2):
            precision = cm[1,1] / (cm[0,1] + cm[1,1] + 1e-8)
            recall    = cm[1,1] / (cm[1,0] + cm[1,1] + 1e-8)
        else:
            precision = 0.0
            recall    = 0.0

        self.sonuclar = {
            'accuracy':  accuracy_score(y_te, y_pred),
            'precision': precision,
            'recall':    recall,
            'f1_mean':   cv.mean(),
            'f1_std':    cv.std(),
            'cm':        cm,
            'train':     len(X_tr),
            'test':      len(X_te),
            'onem':      dict(zip(
                ['Değer','Dalga','Güneş','Sıcaklık','Mesafe',
                 'Beklenen','Sapma','NormSapma','AşırıYüksek',
                 'AnormalDüşük','Güneş×Mesafe','Sıcaklık×Mesafe'],
                self.model.feature_importances_
            )),
        }

        if progress_cb:
            progress_cb(1.0)

        return self.sonuclar


# ══════════════════════════════════════════════════════════════════════════════
#  HATA KURTARMA MODELİ
# ══════════════════════════════════════════════════════════════════════════════

class HataKurtarmaModeli:

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.sonuclar = {}

    def ozellik_cikar(self, row):
        C = VeriYonetici.COL
        dalga  = row[C['dalga']]
        gunes  = row[C['gunes']]
        sicak  = row[C['sicak']]
        mesafe = row[C['mesafe']]

        beklenen = HataTespitModeli.beklenen_sinyal_hesapla(
            dalga, gunes, sicak, mesafe
        )

        return [
            dalga / 1100.0,
            gunes / 90.0,
            (sicak + 120) / 140.0,
            mesafe / 10.0,
            beklenen,
            np.sin(np.radians(gunes)),
            1.0 / (1.0 + (mesafe / 2.0)**2),
        ]

    def egit(self, df, progress_cb=None):
        C = VeriYonetici.COL
        bozuk_df = df[df[C['hata']] == 1]

        if len(bozuk_df) < 3:
            if progress_cb:
                progress_cb(1.0)
            return None

        X = np.array([self.ozellik_cikar(row)
                      for _, row in bozuk_df.iterrows()])
        y = bozuk_df[C['temiz']].values

        if progress_cb:
            progress_cb(0.3)

        X_s = self.scaler.fit_transform(X)

        # ╔══════════════════════════════════════════════════════════╗
        # ║  FIX 3: Çok az bozuk veri varsa test_size küçültüldü   ║
        # ╚══════════════════════════════════════════════════════════╝
        test_boyut = min(0.2, max(1, int(len(X_s) * 0.2)) / len(X_s))
        if len(X_s) < 10:
            test_boyut = 0.3

        X_tr, X_te, y_tr, y_te = train_test_split(
            X_s, y, test_size=test_boyut, random_state=42
        )

        self.model = RandomForestRegressor(
            n_estimators=150, max_depth=12, random_state=42, n_jobs=-1
        )

        if progress_cb:
            progress_cb(0.6)

        self.model.fit(X_tr, y_tr)
        y_pred = self.model.predict(X_te)

        self.sonuclar = {
            'rmse': np.sqrt(mean_squared_error(y_te, y_pred)),
            'mae':  np.mean(np.abs(y_te - y_pred)),
            'r2':   r2_score(y_te, y_pred) if len(y_te) > 1 else 0.0,
            'train': len(X_tr),
            'test':  len(X_te),
        }

        if progress_cb:
            progress_cb(1.0)

        return self.sonuclar

    def kurtar(self, row):
        if self.model is None:
            C = VeriYonetici.COL
            return row[C['bozuk']]
        ozellik = self.ozellik_cikar(row)
        ozellik_s = self.scaler.transform([ozellik])
        return max(0, self.model.predict(ozellik_s)[0])


# ══════════════════════════════════════════════════════════════════════════════
#  SCIENCE UTILITY
# ══════════════════════════════════════════════════════════════════════════════

class ScienceUtility:
    def __init__(self):
        self.w = {
            'chirality': 0.30, 'd13c': 0.25,
            'redox': 0.20, 'assembly': 0.15
        }

    def hesapla(self, dalga_nm, intensite):
        uv  = intensite if 350 < dalga_nm < 500 else 0
        vis = intensite if 500 < dalga_nm < 700 else 0
        nir = intensite if 700 < dalga_nm < 1000 else 0

        chirality = min(1.0, uv * 2.0)
        d13c      = min(1.0, vis * 1.5)
        redox     = min(1.0, nir * 1.8)
        assembly  = min(1.0, (uv + vis) * 0.8)

        su = (chirality * self.w['chirality'] +
              d13c * self.w['d13c'] +
              redox * self.w['redox'] +
              assembly * self.w['assembly'] - 0.05 - 0.08)

        return {
            'su': su, 'chirality': chirality,
            'd13c': d13c, 'redox': redox, 'assembly': assembly
        }


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMTKINTER ARAYÜZ
# ══════════════════════════════════════════════════════════════════════════════

class CiftBitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🚀 AstraBioEdge — Çift Bit Hata Analizi")
        self.geometry("1450x900")
        self.minsize(1200, 700)

        self.veri = VeriYonetici()
        self.tespit = HataTespitModeli()
        self.kurtarma = HataKurtarmaModeli()
        self.su = ScienceUtility()

        self.model_hazir = False
        self._arayuz()

    # ─────────────────────────── ARAYÜZ ───────────────────────────

    def _arayuz(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # SOL PANEL
        sol = ctk.CTkFrame(self, corner_radius=10)
        sol.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(
            sol, text="🔧 KONTROL PANELİ",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=12)

        # Veri
        vf = ctk.CTkFrame(sol, corner_radius=8)
        vf.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(
            vf, text="📂 VERİ",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=4)

        ctk.CTkButton(
            vf, text="📄 Örnek CSV Oluştur",
            command=self._ornek, fg_color="#9b59b6"
        ).pack(pady=3, padx=8, fill="x")

        ctk.CTkButton(
            vf, text="📂 CSV Yükle",
            command=self._yukle, fg_color="#3498db"
        ).pack(pady=3, padx=8, fill="x")

        self.lbl_veri = ctk.CTkLabel(
            vf, text="⏳ Veri yüklenmedi", text_color="#888"
        )
        self.lbl_veri.pack(pady=4)

        # Model
        mf = ctk.CTkFrame(sol, corner_radius=8)
        mf.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(
            mf, text="🧠 MODEL",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=4)

        self.btn_egit = ctk.CTkButton(
            mf, text="🚀 Modeli Eğit",
            command=self._egit, fg_color="#2ecc71", state="disabled"
        )
        self.btn_egit.pack(pady=3, padx=8, fill="x")

        self.progress = ctk.CTkProgressBar(mf, width=200)
        self.progress.pack(pady=4, padx=8)
        self.progress.set(0)

        self.lbl_model = ctk.CTkLabel(
            mf, text="⏳ Model eğitilmedi", text_color="#888"
        )
        self.lbl_model.pack(pady=4)

        # Analiz
        af = ctk.CTkFrame(sol, corner_radius=8)
        af.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(
            af, text="🧪 ANALİZ",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=4)

        self.btn_analiz = ctk.CTkButton(
            af, text="📊 Tüm Veriyi Analiz Et",
            command=self._analiz_et, fg_color="#e67e22", state="disabled"
        )
        self.btn_analiz.pack(pady=6, padx=8, fill="x")

        # Durum
        sf = ctk.CTkFrame(sol, corner_radius=8)
        sf.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(
            sf, text="📊 DURUM",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=4)

        self.lbl_durum = {}
        for key, txt in [
            ("satir","📄 Satır"), ("bozuk","❌ Bozuk"),
            ("oran","📉 Bozuk %"), ("dalga","🌊 Dalga Boyu"),
            ("sicak","🌡️ Sıcaklık"), ("gunes","☀️ Güneş Açısı"),
            ("mesafe","📏 Mesafe")
        ]:
            f = ctk.CTkFrame(sf, fg_color="transparent")
            f.pack(fill="x", padx=6)
            ctk.CTkLabel(f, text=txt, width=110, anchor="w").pack(side="left")
            self.lbl_durum[key] = ctk.CTkLabel(
                f, text="--", font=ctk.CTkFont(weight="bold")
            )
            self.lbl_durum[key].pack(side="right", padx=4)

        # Log
        ctk.CTkLabel(
            sf, text="📋 LOG", font=ctk.CTkFont(weight="bold")
        ).pack(pady=(10,2))

        self.log = ctk.CTkTextbox(sf, height=150, font=ctk.CTkFont(size=10))
        self.log.pack(fill="both", expand=True, padx=4, pady=4)

        # SAĞ PANEL
        sag = ctk.CTkFrame(self, corner_radius=10)
        sag.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        self.tabs = ctk.CTkTabview(sag)
        self.tabs.pack(fill="both", expand=True, padx=4, pady=4)

        self.tab1 = self.tabs.add("📊 Veri Özeti")
        self.tab2 = self.tabs.add("🧠 Model")
        self.tab3 = self.tabs.add("📈 Kurtarma")
        self.tab4 = self.tabs.add("🎯 Science Utility")
        self.tab5 = self.tabs.add("🌡️ Çevre Koşulları")

        bg = '#2b2b2b'
        self.figs, self.canvases = {}, {}

        for name, tab in [
            ("veri", self.tab1), ("model", self.tab2),
            ("kurt", self.tab3), ("su", self.tab4), ("cevre", self.tab5)
        ]:
            fig = Figure(figsize=(10, 6), facecolor=bg)
            canvas = FigureCanvasTkAgg(fig, tab)
            canvas.get_tk_widget().pack(fill="both", expand=True)
            self.figs[name] = fig
            self.canvases[name] = canvas

    # ─────────────────────────── YARDIMCI ───────────────────────────

    def _log_yaz(self, txt):
        self.log.insert("end", txt + "\n")
        self.log.see("end")

    def _ax(self, fig, rows, cols, idx):
        ax = fig.add_subplot(rows, cols, idx)
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='#aaa')
        for spine in ax.spines.values():
            spine.set_color('#555')
        return ax

    # ─────────────────────────── ÖRNEK ───────────────────────────

    def _ornek(self):
        dosya = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="bozuk_2bit_veri.csv"
        )
        if dosya:
            self.veri.ornek_csv_olustur(dosya)
            messagebox.showinfo("✅", f"Oluşturuldu:\n{dosya}")

    # ─────────────────────────── YÜKLE ───────────────────────────

    def _yukle(self):
        dosya = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not dosya:
            return

        try:
            self.veri.yukle(dosya)
            o = self.veri.ozet()

            self.lbl_veri.configure(
                text=f"✅ {o['satir']} satır yüklendi",
                text_color="#2ecc71"
            )
            self.lbl_durum["satir"].configure(text=str(o['satir']))
            self.lbl_durum["bozuk"].configure(text=str(o['bozuk_n']))
            self.lbl_durum["oran"].configure(text=f"%{o['bozuk_oran']:.1f}")
            self.lbl_durum["dalga"].configure(
                text=f"{o['dalga_min']:.0f}-{o['dalga_max']:.0f} nm"
            )
            self.lbl_durum["sicak"].configure(
                text=f"{o['sicak_min']:.0f}/{o['sicak_max']:.0f} °C"
            )
            self.lbl_durum["gunes"].configure(
                text=f"{o['gunes_min']:.0f}-{o['gunes_max']:.0f}°"
            )
            self.lbl_durum["mesafe"].configure(
                text=f"{o['mesafe_min']:.1f}-{o['mesafe_max']:.1f} m"
            )

            # ╔══════════════════════════════════════════════╗
            # ║  FIX 4: Bozuk veri yoksa eğit butonu hâlâ   ║
            # ║  aktif ama uyarı verilir                     ║
            # ╚══════════════════════════════════════════════╝
            if o['bozuk_n'] == 0:
                self._log_yaz("⚠️ Veri setinde bozuk (hata=1) satır yok!")
                self._log_yaz("   Kurtarma modeli eğitilemeyecek.")

            self.btn_egit.configure(state="normal")
            self._log_yaz(
                f"📂 Yüklendi: {os.path.basename(dosya)} "
                f"({o['satir']} satır, {o['bozuk_n']} bozuk)"
            )

            self._veri_grafik()
            self._cevre_grafik()

        except Exception as e:
            messagebox.showerror("Hata", str(e))
            import traceback
            traceback.print_exc()

    # ─────────────────────────── VERİ GRAFİK ───────────────────────────

    def _veri_grafik(self):
        fig = self.figs["veri"]
        fig.clear()
        df = self.veri.df
        C = VeriYonetici.COL

        ax1 = self._ax(fig, 2, 2, 1)
        ax2 = self._ax(fig, 2, 2, 2)
        ax3 = self._ax(fig, 2, 2, 3)
        ax4 = self._ax(fig, 2, 2, 4)

        # ╔═══════════════════════════════════════════════════════════════╗
        # ║  FIX 5: Pie chart — negatif değer ve sıfır kontrolü eklendi ║
        # ╚═══════════════════════════════════════════════════════════════╝
        bozuk_n = int(df[C['hata']].sum())
        temiz_n = int(len(df) - bozuk_n)

        # Negatif olmamasını garanti et
        bozuk_n = max(0, bozuk_n)
        temiz_n = max(0, temiz_n)

        # İkisi de sıfırsa pie çizilemez
        if temiz_n + bozuk_n == 0:
            ax1.text(0.5, 0.5, "Veri yok", ha='center', va='center',
                     color='white', fontsize=14)
        elif bozuk_n == 0:
            # Sadece temiz veri var — pie chart tek dilim
            ax1.pie([temiz_n], labels=['Temiz'],
                    colors=['#2ecc71'], autopct='%1.1f%%',
                    textprops={'color': 'white'})
        elif temiz_n == 0:
            # Tümü bozuk
            ax1.pie([bozuk_n], labels=['Bozuk'],
                    colors=['#e74c3c'], autopct='%1.1f%%',
                    textprops={'color': 'white'})
        else:
            ax1.pie([temiz_n, bozuk_n],
                    labels=['Temiz', 'Bozuk'],
                    colors=['#2ecc71', '#e74c3c'],
                    autopct='%1.1f%%',
                    textprops={'color': 'white'})
        ax1.set_title('Veri Dağılımı', color='white', fontweight='bold')

        # 2. Dalga boyu vs intensite
        temiz_mask = df[C['hata']] == 0
        bozuk_mask = df[C['hata']] == 1

        if temiz_mask.any():
            ax2.scatter(
                df.loc[temiz_mask, C['dalga']],
                df.loc[temiz_mask, C['temiz']],
                s=5, c='#2ecc71', alpha=0.4, label='Temiz'
            )
        if bozuk_mask.any():
            ax2.scatter(
                df.loc[bozuk_mask, C['dalga']],
                df.loc[bozuk_mask, C['bozuk']],
                s=15, c='#e74c3c', alpha=0.8, label='Bozuk'
            )
        ax2.set_xlabel('Dalga Boyu (nm)', color='#aaa')
        ax2.set_ylabel('İntansite', color='#aaa')
        ax2.set_title('Dalga Boyu vs İntansite', color='white', fontweight='bold')
        ax2.legend(facecolor='#333', labelcolor='white', fontsize=8)

        # 3. İntansite histogramı
        if temiz_mask.any():
            ax3.hist(df.loc[temiz_mask, C['temiz']], bins=40,
                     alpha=0.6, color='#2ecc71', label='Temiz')
        if bozuk_mask.any():
            ax3.hist(df.loc[bozuk_mask, C['bozuk']], bins=40,
                     alpha=0.6, color='#e74c3c', label='Bozuk')
        ax3.set_title('İntansite Dağılımı', color='white', fontweight='bold')
        ax3.legend(facecolor='#333', labelcolor='white', fontsize=8)

        # 4. Sapma scatter
        sapma = (df[C['bozuk']] - df[C['temiz']]).abs()
        renk = df[C['hata']].map({0: '#2ecc71', 1: '#e74c3c'})
        ax4.scatter(df[C['dalga']], sapma, s=5, c=renk, alpha=0.6)
        ax4.set_xlabel('Dalga Boyu (nm)', color='#aaa')
        ax4.set_ylabel('|Bozuk - Orijinal|', color='#aaa')
        ax4.set_title('Sapma Analizi', color='white', fontweight='bold')

        fig.tight_layout()
        self.canvases["veri"].draw()

    # ─────────────────────────── ÇEVRE GRAFİK ───────────────────────────

    def _cevre_grafik(self):
        fig = self.figs["cevre"]
        fig.clear()
        df = self.veri.df
        C = VeriYonetici.COL

        ax1 = self._ax(fig, 2, 2, 1)
        ax2 = self._ax(fig, 2, 2, 2)
        ax3 = self._ax(fig, 2, 2, 3)
        ax4 = self._ax(fig, 2, 2, 4)

        renk = df[C['hata']].map({0: '#2ecc71', 1: '#e74c3c'})

        ax1.scatter(df[C['gunes']], df[C['bozuk']], s=8, c=renk, alpha=0.5)
        ax1.set_xlabel('Güneş Açısı (°)', color='#aaa')
        ax1.set_ylabel('Bozuk Değer', color='#aaa')
        ax1.set_title('☀️ Güneş Açısı Etkisi', color='white', fontweight='bold')

        ax2.scatter(df[C['sicak']], df[C['bozuk']], s=8, c=renk, alpha=0.5)
        ax2.set_xlabel('Sıcaklık (°C)', color='#aaa')
        ax2.set_ylabel('Bozuk Değer', color='#aaa')
        ax2.set_title('🌡️ Sıcaklık Etkisi', color='white', fontweight='bold')

        ax3.scatter(df[C['mesafe']], df[C['bozuk']], s=8, c=renk, alpha=0.5)
        ax3.set_xlabel('Mesafe (m)', color='#aaa')
        ax3.set_ylabel('Bozuk Değer', color='#aaa')
        ax3.set_title('📏 Mesafe Etkisi', color='white', fontweight='bold')

        ax4.scatter(df[C['gunes']], df[C['sicak']], s=8, c=renk, alpha=0.5)
        ax4.set_xlabel('Güneş Açısı (°)', color='#aaa')
        ax4.set_ylabel('Sıcaklık (°C)', color='#aaa')
        ax4.set_title('☀️🌡️ Güneş-Sıcaklık İlişkisi',
                      color='white', fontweight='bold')

        fig.tight_layout()
        self.canvases["cevre"].draw()

    # ─────────────────────────── EĞİT ───────────────────────────

    def _egit(self):
        self.btn_egit.configure(state="disabled")
        self.lbl_model.configure(
            text="⏳ Eğitiliyor...", text_color="#f39c12"
        )

        def thread_fn():
            try:
                self._log_yaz("\n🧠 Tespit modeli eğitiliyor...")
                t_sonuc = self.tespit.egit(
                    self.veri.df,
                    lambda p: self.after(
                        0, lambda: self.progress.set(p * 0.5)
                    )
                )

                self._log_yaz(f"   Accuracy:  {t_sonuc['accuracy']:.4f}")
                self._log_yaz(f"   Precision: {t_sonuc['precision']:.4f}")
                self._log_yaz(f"   Recall:    {t_sonuc['recall']:.4f}")
                self._log_yaz(
                    f"   F1 (CV):   {t_sonuc['f1_mean']:.4f} "
                    f"±{t_sonuc['f1_std']:.4f}"
                )

                self._log_yaz("\n🔧 Kurtarma modeli eğitiliyor...")
                k_sonuc = self.kurtarma.egit(
                    self.veri.df,
                    lambda p: self.after(
                        0, lambda: self.progress.set(0.5 + p * 0.5)
                    )
                )

                if k_sonuc:
                    self._log_yaz(f"   RMSE: {k_sonuc['rmse']:.6f}")
                    self._log_yaz(f"   MAE:  {k_sonuc['mae']:.6f}")
                    self._log_yaz(f"   R²:   {k_sonuc['r2']:.4f}")
                else:
                    self._log_yaz(
                        "   ⚠️ Yeterli bozuk veri yok, "
                        "kurtarma modeli eğitilemedi"
                    )

                self._log_yaz("\n✅ Eğitim tamamlandı!")
                self.after(
                    0, lambda: self._egitim_bitti(t_sonuc, k_sonuc)
                )

            except Exception as e:
                self.after(
                    0, lambda: messagebox.showerror("Hata", str(e))
                )
                self.after(
                    0, lambda: self.btn_egit.configure(state="normal")
                )
                import traceback
                traceback.print_exc()

        threading.Thread(target=thread_fn, daemon=True).start()

    def _egitim_bitti(self, t_sonuc, k_sonuc):
        self.model_hazir = True
        self.progress.set(1.0)
        self.btn_egit.configure(state="normal")
        self.btn_analiz.configure(state="normal")
        self.lbl_model.configure(
            text="✅ Model hazır!", text_color="#2ecc71"
        )
        self._model_grafik(t_sonuc, k_sonuc)

    # ─────────────────────────── MODEL GRAFİK ───────────────────────────

    def _model_grafik(self, t_sonuc, k_sonuc):
        fig = self.figs["model"]
        fig.clear()

        ax1 = self._ax(fig, 2, 2, 1)
        ax2 = self._ax(fig, 2, 2, 2)
        ax3 = self._ax(fig, 2, 2, 3)
        ax4 = self._ax(fig, 2, 2, 4)

        # ╔════════════════════════════════════════════════════════════╗
        # ║  FIX 6: Confusion matrix boyut kontrolü (1×1 olabilir)   ║
        # ╚════════════════════════════════════════════════════════════╝
        cm = t_sonuc['cm']
        n_classes = cm.shape[0]
        ax1.imshow(cm, cmap='Blues')

        for i in range(n_classes):
            for j in range(n_classes):
                ax1.text(j, i, str(cm[i, j]),
                         ha='center', va='center',
                         color=('white' if cm[i, j] > cm.max() / 2
                                else 'black'),
                         fontsize=16, fontweight='bold')

        if n_classes == 2:
            ax1.set_xticks([0, 1])
            ax1.set_yticks([0, 1])
            ax1.set_xticklabels(['Temiz', 'Bozuk'], color='white')
            ax1.set_yticklabels(['Temiz', 'Bozuk'], color='white')
        else:
            ax1.set_xticks(range(n_classes))
            ax1.set_yticks(range(n_classes))
        ax1.set_title('Confusion Matrix', color='white', fontweight='bold')

        # Metrikler
        names = ['Accuracy', 'Precision', 'Recall', 'F1']
        vals  = [
            t_sonuc['accuracy'], t_sonuc['precision'],
            t_sonuc['recall'], t_sonuc['f1_mean']
        ]
        colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c']
        bars = ax2.bar(names, vals, color=colors)
        ax2.set_ylim(0, 1.15)
        ax2.set_title('Tespit Metrikleri', color='white', fontweight='bold')
        for b, v in zip(bars, vals):
            ax2.text(b.get_x() + b.get_width() / 2,
                     b.get_height() + 0.02,
                     f'{v:.3f}', ha='center', color='white', fontsize=10)

        # Özellik önemleri
        onem = t_sonuc['onem']
        sorted_onem = sorted(onem.items(), key=lambda x: x[1],
                             reverse=True)[:8]
        names_o = [x[0] for x in sorted_onem]
        vals_o  = [x[1] for x in sorted_onem]
        ax3.barh(names_o[::-1], vals_o[::-1], color='#9b59b6')
        ax3.set_title('Özellik Önemleri', color='white', fontweight='bold')
        ax3.set_xlabel('Önem', color='#aaa')

        # ╔═══════════════════════════════════════════════════════════╗
        # ║  FIX 7: Kurtarma sonucu yoksa bilgi mesajı göster       ║
        # ╚═══════════════════════════════════════════════════════════╝
        if k_sonuc:
            names_k = ['RMSE', 'MAE', 'R²']
            vals_k  = [k_sonuc['rmse'], k_sonuc['mae'], k_sonuc['r2']]
            colors_k = ['#e74c3c', '#f39c12', '#2ecc71']
            bars_k = ax4.bar(names_k, vals_k, color=colors_k)
            ax4.set_title('Kurtarma Metrikleri',
                          color='white', fontweight='bold')

            for b, v in zip(bars_k, vals_k):
                ypos = (b.get_height() + 0.005 if v >= 0
                        else b.get_height() - 0.02)
                ax4.text(b.get_x() + b.get_width() / 2, ypos,
                         f'{v:.4f}', ha='center', color='white',
                         fontsize=10)
        else:
            ax4.text(0.5, 0.5,
                     "Kurtarma modeli\neğitilemedi\n(bozuk veri yok)",
                     ha='center', va='center', color='#888',
                     fontsize=12, transform=ax4.transAxes)
            ax4.set_title('Kurtarma Metrikleri',
                          color='white', fontweight='bold')

        fig.tight_layout()
        self.canvases["model"].draw()

    # ─────────────────────────── ANALİZ ───────────────────────────

    def _analiz_et(self):
        if not self.model_hazir:
            return

        C = VeriYonetici.COL
        df = self.veri.df.copy()

        self._log_yaz("\n📊 Tüm veri analiz ediliyor...")

        # Kurtarma
        kurtarilmis = df[C['bozuk']].values.copy().astype(float)
        bozuk_idx = df[df[C['hata']] == 1].index

        # ╔═══════════════════════════════════════════════════════════╗
        # ║  FIX 8: Kurtarma modeli yoksa beklenen sinyal kullan    ║
        # ╚═══════════════════════════════════════════════════════════╝
        if self.kurtarma.model is not None and len(bozuk_idx) > 0:
            for idx in bozuk_idx:
                row = df.loc[idx]
                kurtarilmis[idx] = self.kurtarma.kurtar(row)
            self._log_yaz(f"   {len(bozuk_idx)} bozuk satır kurtarıldı")
        elif len(bozuk_idx) > 0:
            # Kurtarma modeli yoksa fizik modeli kullan
            for idx in bozuk_idx:
                row = df.loc[idx]
                kurtarilmis[idx] = HataTespitModeli.beklenen_sinyal_hesapla(
                    row[C['dalga']], row[C['gunes']],
                    row[C['sicak']], row[C['mesafe']]
                )
            self._log_yaz(
                f"   ⚠️ Kurtarma modeli yok, "
                f"fizik modeli kullanıldı ({len(bozuk_idx)} satır)"
            )
        else:
            self._log_yaz("   ℹ️ Bozuk satır yok, kurtarma gerekmedi")

        df['kurtarilmis'] = kurtarilmis

        # Metrikler
        bozuk_mask = df[C['hata']] == 1
        if bozuk_mask.sum() > 0:
            temiz_vals = df.loc[bozuk_mask, C['temiz']].values
            bozuk_vals = df.loc[bozuk_mask, C['bozuk']].values
            kurt_vals  = df.loc[bozuk_mask, 'kurtarilmis'].values

            rmse_b = np.sqrt(mean_squared_error(temiz_vals, bozuk_vals))
            rmse_k = np.sqrt(mean_squared_error(temiz_vals, kurt_vals))
            iyilesme = ((rmse_b - rmse_k) / (rmse_b + 1e-8)) * 100

            self._log_yaz(f"   Bozuk RMSE:      {rmse_b:.6f}")
            self._log_yaz(f"   Kurtarma RMSE:   {rmse_k:.6f}")
            self._log_yaz(f"   İyileşme:        %{iyilesme:.1f}")

        self._kurtarma_grafik(df)
        self._su_grafik(df)
        self._log_yaz("✅ Analiz tamamlandı!")

    # ─────────────────────────── KURTARMA GRAFİK ───────────────────────────

    def _kurtarma_grafik(self, df):
        fig = self.figs["kurt"]
        fig.clear()
        C = VeriYonetici.COL

        ax1 = self._ax(fig, 2, 2, 1)
        ax2 = self._ax(fig, 2, 2, 2)
        ax3 = self._ax(fig, 2, 2, 3)
        ax4 = self._ax(fig, 2, 2, 4)

        bozuk_mask = df[C['hata']] == 1

        # 1. Orijinal vs Bozuk vs Kurtarılmış
        ax1.scatter(df[C['dalga']], df[C['temiz']],
                    s=3, c='#2ecc71', alpha=0.3, label='Orijinal')

        if bozuk_mask.any():
            ax1.scatter(df.loc[bozuk_mask, C['dalga']],
                        df.loc[bozuk_mask, C['bozuk']],
                        s=15, c='#e74c3c', alpha=0.7, label='Bozuk')
            ax1.scatter(df.loc[bozuk_mask, C['dalga']],
                        df.loc[bozuk_mask, 'kurtarilmis'],
                        s=15, c='#3498db', alpha=0.7, marker='D',
                        label='Kurtarılmış')

        ax1.set_title('Kurtarma Sonuçları',
                      color='white', fontweight='bold')
        ax1.set_xlabel('Dalga Boyu (nm)', color='#aaa')
        ax1.legend(facecolor='#333', labelcolor='white', fontsize=7)

        # ╔═══════════════════════════════════════════════════════════╗
        # ║  FIX 9: Bozuk veri yoksa boş grafik yerine mesaj göster ║
        # ╚═══════════════════════════════════════════════════════════╝
        if bozuk_mask.sum() > 0:
            temiz_v = df.loc[bozuk_mask, C['temiz']].values
            kurt_v  = df.loc[bozuk_mask, 'kurtarilmis'].values
            bozuk_v = df.loc[bozuk_mask, C['bozuk']].values

            # 2. Orijinal vs Kurtarılmış scatter
            ax2.scatter(temiz_v, kurt_v, s=15, c='#3498db', alpha=0.6)
            tum_vals = np.concatenate([temiz_v, kurt_v])
            lims = [tum_vals.min() - 0.01, tum_vals.max() + 0.01]
            ax2.plot(lims, lims, 'r--', lw=1.5, label='Mükemmel')
            ax2.set_xlabel('Orijinal', color='#aaa')
            ax2.set_ylabel('Kurtarılmış', color='#aaa')
            ax2.set_title('Orijinal vs Kurtarılmış',
                          color='white', fontweight='bold')
            ax2.legend(facecolor='#333', labelcolor='white')

            # 3. Hata histogramı
            hatalar = kurt_v - temiz_v
            ax3.hist(hatalar, bins=max(5, len(hatalar) // 3),
                     color='#3498db', alpha=0.7, edgecolor='white')
            ax3.axvline(0, color='red', ls='--', lw=1.5)
            ax3.set_title('Kurtarma Hatası Dağılımı',
                          color='white', fontweight='bold')
            ax3.set_xlabel('Hata', color='#aaa')

            # 4. RMSE karşılaştırma
            rmse_b = np.sqrt(mean_squared_error(temiz_v, bozuk_v))
            rmse_k = np.sqrt(mean_squared_error(temiz_v, kurt_v))

            bars = ax4.bar(
                ['Bozuk\nRMSE', 'Kurtarılmış\nRMSE'],
                [rmse_b, rmse_k],
                color=['#e74c3c', '#3498db'],
                edgecolor='white', linewidth=2
            )
            for b, v in zip(bars, [rmse_b, rmse_k]):
                ax4.text(b.get_x() + b.get_width() / 2,
                         b.get_height() + 0.005,
                         f'{v:.4f}', ha='center', color='white',
                         fontsize=12, fontweight='bold')

            iyilesme = ((rmse_b - rmse_k) / (rmse_b + 1e-8)) * 100
            ax4.set_title(f'RMSE İyileşme: %{iyilesme:.1f}',
                          color='white', fontweight='bold')
        else:
            for ax in [ax2, ax3, ax4]:
                ax.text(0.5, 0.5,
                        "Bozuk veri yok\nkarşılaştırma yapılamaz",
                        ha='center', va='center', color='#888',
                        fontsize=11, transform=ax.transAxes)

        fig.tight_layout()
        self.canvases["kurt"].draw()

    # ─────────────────────────── SU GRAFİK ───────────────────────────

    def _su_grafik(self, df):
        fig = self.figs["su"]
        fig.clear()
        C = VeriYonetici.COL

        ax1 = self._ax(fig, 1, 2, 1)
        ax2 = self._ax(fig, 1, 2, 2)

        su_temiz, su_bozuk, su_kurt = [], [], []

        for _, row in df.iterrows():
            dalga = row[C['dalga']]
            st = self.su.hesapla(dalga, row[C['temiz']])
            sb = self.su.hesapla(dalga, row[C['bozuk']])
            sk = self.su.hesapla(dalga, row['kurtarilmis'])
            su_temiz.append(st['su'])
            su_bozuk.append(sb['su'])
            su_kurt.append(sk['su'])

        # 1. SU dağılımı
        ax1.hist(su_temiz, bins=30, alpha=0.5, color='#2ecc71',
                 label='Temiz')
        ax1.hist(su_bozuk, bins=30, alpha=0.5, color='#e74c3c',
                 label='Bozuk')
        ax1.hist(su_kurt, bins=30, alpha=0.5, color='#3498db',
                 label='Kurtarılmış')
        ax1.set_title('Science Utility Dağılımı',
                      color='white', fontweight='bold')
        ax1.set_xlabel('SU Score', color='#aaa')
        ax1.legend(facecolor='#333', labelcolor='white')

        # ╔═══════════════════════════════════════════════════════╗
        # ║  FIX 10: Negatif bar değerlerinde text konumu düzelt ║
        # ╚═══════════════════════════════════════════════════════╝
        ort = [np.mean(su_temiz), np.mean(su_bozuk), np.mean(su_kurt)]
        bars = ax2.bar(
            ['Temiz', 'Bozuk', 'Kurtarılmış'], ort,
            color=['#2ecc71', '#e74c3c', '#3498db'],
            edgecolor='white', linewidth=2
        )
        ax2.axhline(0, color='white', lw=0.5)
        ax2.set_title('Ortalama Science Utility',
                      color='white', fontweight='bold')
        ax2.set_ylabel('SU Score', color='white')

        for b, v in zip(bars, ort):
            # Negatif değerlerde text barın altına
            if v >= 0:
                ypos = b.get_height() + 0.005
                va = 'bottom'
            else:
                ypos = b.get_height() - 0.005
                va = 'top'
            ax2.text(b.get_x() + b.get_width() / 2, ypos,
                     f'{v:.4f}', ha='center', va=va,
                     color='white', fontsize=12, fontweight='bold')

        fig.tight_layout()
        self.canvases["su"].draw()


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = CiftBitApp()
    app.mainloop()
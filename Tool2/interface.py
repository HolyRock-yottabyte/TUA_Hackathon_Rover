import pandas as pd
import numpy as np
import random

def generate_mars_dataset(n_rows=1000):
    np.random.seed(42)
    random.seed(42)

    sols = np.linspace(1, 100, n_rows, dtype=int)
    zaman_dilimleri = ["Gece", "Şafak", "Öğlen", "Akşam"]
    
    # Öğrenilmiş Dinamik Profil
    profil_sicakliklari = {"Gece": -80, "Şafak": -60, "Öğlen": -20, "Akşam": -50}

    data = []
    
    for i in range(n_rows):
        sol = sols[i]
        zaman = zaman_dilimleri[i % 4]
        profil = profil_sicakliklari[zaman]

        # --- 1. SİNYAL ÜRETİMİ VE OLASILIK DAĞILIMI ---
        rand_val = random.random()

        if rand_val < 0.85: 
            # %85 İhtimal: Her şey normal
            gelen_sicaklik = np.random.normal(profil, 3)
            sys_a = random.randint(10, 50)
            sys_b = sys_a + random.randint(-10, 10)
            ozel_durum = False
            
        elif rand_val < 0.94: 
            # %9 İhtimal: Şüpheli Sapma (10-30 arası)
            gelen_sicaklik = profil + random.choice([1, -1]) * random.uniform(15, 25)
            sys_a = random.randint(50, 80)
            sys_b = sys_a + random.randint(-15, 15)
            ozel_durum = False
            
        elif rand_val < 0.98: 
            # %4 İhtimal: Sensör Sorunu (>50 sapma)
            gelen_sicaklik = profil + random.choice([1, -1]) * random.uniform(55, 70)
            sys_a = random.randint(60, 90)
            sys_b = sys_a + random.randint(-20, 20)
            ozel_durum = False
            
        else: 
            # %2 İhtimal: ÖZEL DURUM (Hiç Görülmemiş Sinyal)
            gelen_sicaklik = np.random.normal(profil, 2) 
            sys_a = 0  # Statik sistem bunu tanımıyor
            sys_b = random.randint(92, 100) # Dinamik sistem "Bu çok farklı" diyor
            ozel_durum = True

        # --- 2. MEDA SENSÖR KARAR AĞACI ---
        sapma_miktari = abs(gelen_sicaklik - profil)
        # Örnekteki gibi 1 derece sapma = %1 sapma olarak oranlandı
        sapma_yuzdesi = round(sapma_miktari, 1)

        # Statik Limit Kontrolü (Örn: NASA Mars limits)
        fiziksel_limit_ihlali = "Evet" if (gelen_sicaklik < -130 or gelen_sicaklik > 30) else "Hayır"

        if sapma_yuzdesi < 10:
            meda_karar = "Normal Devam"
        elif sapma_yuzdesi < 50: # 10 ile 50 arası
            meda_karar = "Şüpheli - Teyit Ölçümü Planla"
        else: # 50 ve üstü
            meda_karar = "Sensör Sorunu - Yeniden Kalibrasyon"

        # --- 3. BİLİMSEL FİLTRE (SCIENCE FILTER) OTONOMİSİ ---
        sys_a = max(0, min(100, sys_a))
        sys_b = max(0, min(100, sys_b))

        if ozel_durum:
            final_skor = sys_b # Otonom olarak B'nin dediği kabul edilir
            bilimsel_karar = "P0 (Yüksek Belirsizlik - Teyit İste)"
            flag = 1
        else:
            final_skor = round((sys_a * 0.6) + (sys_b * 0.4), 1)
            flag = 0
            
            # Önceliklendirme (P1, P2)
            if final_skor >= 60:
                bilimsel_karar = "P1 (Yüksek Öncelik)"
            elif final_skor >= 35:
                bilimsel_karar = "P2 (Standart Analiz)"
            else:
                bilimsel_karar = "P3 (Rutin Veri)"

        data.append([
            sol, zaman, round(gelen_sicaklik, 1), profil, fiziksel_limit_ihlali,
            sapma_yuzdesi, meda_karar,
            sys_a, sys_b, final_skor, bilimsel_karar, flag
        ])

    df = pd.DataFrame(data, columns=[
        "Sol", "Zaman_Dilimi", "Olculen_Sicaklik_C", "Ogrenilen_Profil_C", "Fiziksel_Ihlal",
        "Sapma_Yuzdesi", "Otonom_Karar_MEDA",
        "Sistem_A_Skor", "Sistem_B_Skor", "Final_Skor", "Bilimsel_Karar", "Ozel_Durum_Flag"
    ])
    
    df.to_csv("mars_otonom_veri_seti_1000.csv", index=False)
    print("✅ 1000 satırlık otonom veri seti oluşturuldu: mars_otonom_veri_seti_1000.csv")
    return df

# Kodu çalıştırıp ilk 5 satırı görelim
df = generate_mars_dataset()
print(df.head(10))
import pandas as pd
import numpy as np

def excel_birebir_uret(satir_sayisi=1000):
    # 1. dalga_boyu_nm: 200'den başlar, ~800'e kadar gider
    dalga_boyu = np.linspace(200.0, 793.39, satir_sayisi)
    
    # 2. orijinal_intensite: 150 merkezli, sinüs dalgalı Mars sinyali
    # Excel'deki 150.43, 143.95 gibi değerleri üreten ana formül
    orijinal_intensite = 150 + 10 * np.sin(dalga_boyu / 10) + np.random.normal(0, 5, satir_sayisi)
    
    # 3. bozuk_2bit_deger: Veriyi 4 seviyeye (0, 1, 2, 3) indiren "Quantization" işlemi
    # Bu işlem Excel'deki o '1' ve '2' değerlerini oluşturur
    bins = np.linspace(orijinal_intensite.min(), orijinal_intensite.max(), 5)
    bozuk_2bit_deger = np.digitize(orijinal_intensite, bins) - 1
    bozuk_2bit_deger = np.clip(bozuk_2bit_deger, 0, 3) # 0,1,2,3 aralığına sabitle
    
    # 4. bozuk_hatali: Excel'deki 1.0 değerleri (Hata tespiti)
    # Eğer orijinal veri ile 2-bit basamağı arasında fark varsa '1' işaretle
    bozuk_hatali = np.where(np.abs(orijinal_intensite - (140 + bozuk_2bit_deger * 10)) > 5, 1.0, 0.0)
    
    # 5. DİĞER PARAMETRELER (Güneş açısı, Sıcaklık, Mesafe)
    gunes_acisi = 30 + 5 * np.cos(dalga_boyu / 50) + np.random.normal(0, 1, satir_sayisi)
    sicaklik_c = -20 + np.random.normal(0, 1, satir_sayisi)
    mesafe_m = 1.5 + 0.5 * np.random.random(satir_sayisi)
    
    # DATAFRAME OLUŞTURMA (Excel ile birebir aynı kolon isimleri)
    df = pd.DataFrame({
        'dalga_boyu_nm': dalga_boyu,
        'orijinal_intensite': orijinal_intensite,
        'bozuk_2bit_deger': bozuk_2bit_deger,
        'bozuk_hatali': bozuk_hatali,
        'gunes_acisi': gunes_acisi,
        'sicaklik_c': sicaklik_c,
        'mesafe_m': mesafe_m
    })
    
    return df

# Algoritmayı çalıştır ve dosyayı oluştur
df_yeni = excel_birebir_uret(1000)

# Excel ile aynı isimde kaydet (İstersen ismini değiştirebilirsin)
df_yeni.to_csv("bozuk_2bit_veri_YENI.csv", index=False)

print("Excel'deki verilerin birebir aynısını üreten algoritma çalıştırıldı.")
print(df_yeni.head()) # İlk 5 satırı kontrol et
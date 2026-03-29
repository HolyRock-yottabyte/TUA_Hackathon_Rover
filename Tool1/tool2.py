# Gerekli kütüphaneleri yükle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor  # Sayısal tahmin için Regressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score # Regresyon başarı metrikleri
import os

# 1. Veriyi Yükle
dosya_adi = "bozuk_2bit_veri.csv"
if not os.path.exists(dosya_adi):
    print("HATA: Veri dosyası bulunamadı!")
else:
    df = pd.read_csv(dosya_adi).dropna()

    # 2. Özellikleri (X) ve Hedefi (y) Belirle
    # Giriş: Bozuk sinyal ve çevresel veriler
    X = df[['dalga_boyu_nm', 'bozuk_2bit_deger', 'gunes_acisi', 'sicaklik_c']]
    # Hedef: Orijinal temiz intensite (tahmin etmek istediğimiz gerçek değer)
    y = df['orijinal_intensite']

    # 3. Veriyi Böl (Train-Test Split)
    # Verinin %20'sini modeli test etmek, %80'ini eğitmek için ayırıyoruz
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Random Forest Modeli (İstediğin parametrelerle)
    model = RandomForestRegressor(
        n_estimators=100,    # Kaç tane karar ağacı kullanılacak
        max_depth=10,        # Ağaçların maksimum derinliği
        random_state=42      # Sonuçların her seferinde aynı çıkması için
    )

    # 5. Eğit (Fit)
    model.fit(X_train, y_train)

    # 6. Tahmin Yap (Predict)
    tahminler = model.predict(X_test)

    # 7. Sonuç ve Raporlama
    # Regresyonda 'Accuracy' yerine 'R2 Skoru' (Doğruluk Oranı) kullanılır
    r2 = r2_score(y_test, tahminler)
    mae = mean_absolute_error(y_test, tahminler)

    print("--- SİNYAL ONARIM ANALİZ RAPORU ---")
    print(f"Model Başarı Oranı (R2 Skoru): {r2:.2%}")
    print(f"Ortalama Mutlak Hata (MAE): {mae:.4f}")
    print("\nModel Parametreleri:")
    print(f"Ağaç Sayısı: {model.n_estimators}")
    print(f"Maksimum Derinlik: {model.max_depth}")

    # Örnek Tahminleri Göster
    print("\nTest Setinden İlk 5 Tahmin ve Gerçek Değer:")
    karsilastirma = pd.DataFrame({'Gerçek': y_test, 'Tahmin': tahminler}).head()
    print(karsilastirma)
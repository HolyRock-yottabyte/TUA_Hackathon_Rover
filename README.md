<div align="center">

# ☢️ AstraBioEdge

### Çift Bit Hata Analizi ve Kurtarma Sistemi
**Uzay Radyasyon Ortamlarında Veri Bütünlüğü için Makine Öğrenmesi Tabanlı Çözüm**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-1F6FEB?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

<br>

*Uzay araçlarındaki sensör verilerinde radyasyonun neden olduğu çift bit hatalarını (Double Bit Upset — DBU) tespit eden, sınıflandıran ve kurtaran uçtan uca bir analiz platformu.*

<br>

[Kurulum](#-kurulum) · [Kullanım](#-kullanım) · [Mimari](#-sistem-mimarisi) · [Sonuçlar](#-deneysel-sonuçlar) · [Katkı](#-katkı)

</div>

---

## 📋 İçindekiler

- [Proje Özeti](#-proje-özeti)
- [Problem Tanımı](#-problem-tanımı)
- [Çözüm Yaklaşımı](#-çözüm-yaklaşımı)
- [Sistem Mimarisi](#-sistem-mimarisi)
- [Veri Formatı](#-veri-formatı)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Deneysel Sonuçlar](#-deneysel-sonuçlar)
- [Ekran Görüntüleri](#-ekran-görüntüleri)
- [Teknolojiler](#-teknolojiler)
- [Katkı](#-katkı)
- [Lisans](#-lisans)

---

## 🔬 Proje Özeti

**AstraBioEdge**, uzay radyasyon ortamlarında (özellikle Mars yüzey koşullarında) çalışan spektroskopik sensörlerin topladığı verilerde meydana gelen **çift bit bozulmalarını (Double Bit Upset)** tespit etmek ve onararak bilimsel kullanılabilirliğini geri kazandırmak amacıyla geliştirilmiş bir platformdur.

Sistem üç temel katmandan oluşur:

| Katman | İşlev | Yöntem |
|--------|-------|--------|
| **Tespit** | Bozuk veriyi sağlamdan ayırt etme | Random Forest Classifier |
| **Kurtarma** | Bozulmuş değeri orijinaline yakınsama | Random Forest Regressor |
| **Bilimsel Değerlendirme** | Kurtarılan verinin bilimsel kullanılabilirliği | Science Utility Skoru |

---

## 🎯 Problem Tanımı

### Uzayda Radyasyon ve Veri Bütünlüğü

Uzay araçlarındaki elektronik bileşenler, yüksek enerjili kozmik ışınlara ve güneş parçacıklarına sürekli maruz kalır. Bu parçacıklar bellek hücrelerinden geçerken **bit değerlerini tersine çevirebilir**:
Orijinal bellek durumu: 0 1 1 0 1 0 0 1
↑ ↑
Parçacık çarpması

Bozulmuş bellek durumu: 0 1 1 1 0 0 0 1
↑ ↑
2 bit ters döndü (DBU)

text


#### Neden Çift Bit (Double Bit Upset)?

- **Tekli Bit Hataları (SBU):** ECC (Error Correcting Code) bellek tarafından otomatik düzeltilir.
- **Çift Bit Hataları (DBU):** Standart ECC tarafından **tespit edilebilir ama düzeltilemez**. Bu, sessiz veri bozulmasına yol açabilir.

#### Mars Ortamı Zorlukları

| Parametre | Dünya | Mars |
|-----------|-------|------|
| Manyetik kalkan | Güçlü | Yok |
| Atmosfer kalınlığı | 1013 hPa | ~6 hPa |
| Yüzey radyasyon dozu | ~2.4 mSv/yıl | ~233 mSv/yıl |
| Sıcaklık aralığı | -89 / +57 °C | -140 / +20 °C |
| İletişim gecikmesi | — | 4–24 dakika |

> **Sonuç:** Mars yüzeyinde çalışan bir sensörün verisini Dünya'ya göndermeden önce **yerinde (on-board)** doğrulamak ve onarmak kritik önem taşır.

---

## 💡 Çözüm Yaklaşımı

### 1. Fizik Tabanlı Beklenen Sinyal Modeli

Sensörün ölçmesi gereken değer, çevresel koşullardan analitik olarak tahmin edilir:
Beklenen Sinyal = Baz_Sinyal(λ) × Güneş_Faktörü(θ) × Mesafe_Faktörü(d)

text


Burada:
- **Baz Sinyal:** Dalga boyuna bağlı Gauss piklerinin süperpozisyonu (650nm ve 860nm merkezli)
- **Güneş Faktörü:** `0.3 + 0.7 × sin(θ)` — düşük açılarda sinyal zayıflar
- **Mesafe Faktörü:** `1 / (1 + (d/2)²)` — ters kare yasası yaklaşımı

### 2. Makine Öğrenmesi ile Hata Tespiti

Fizik modeli tek başına yeterli olmadığı için, 12 boyutlu bir özellik vektörü çıkarılarak **Random Forest Classifier** eğitilir:
Özellik Vektörü = [
Ölçülen değer, # Ham sinyal
Normalize dalga boyu, # λ / 1100
Normalize güneş açısı, # θ / 90
Normalize sıcaklık, # (T + 120) / 140
Normalize mesafe, # d / 10
Beklenen sinyal, # Fizik modeli çıktısı
Mutlak sapma, # |ölçülen - beklenen|
Normalize sapma, # sapma / beklenen
Aşırı yüksek bayrağı, # 1 eğer değer > 1.5
Anormal düşük bayrağı, # 1 eğer değer ≈ 0 ve beklenen > 0.05
Güneş × Mesafe etkileşimi, # sin(θ) × d
Sıcaklık × Mesafe etkileşimi # T × d / 100
]

text


### 3. Bozuk Değer Kurtarma

Bozuk olarak tespit edilen değerler, çevresel koşullardan (dalga boyu, güneş açısı, sıcaklık, mesafe) **Random Forest Regressor** ile tahmin edilerek onarılır.

### 4. Bilimsel Değerlendirme (Science Utility)

Kurtarılan verinin astrobiyolojik araştırma için ne kadar kullanılabilir olduğu dört alt metrikle ölçülür:

| Metrik | Ağırlık | Spektral Bant | Astrobiyolojik Anlam |
|--------|---------|---------------|----------------------|
| **Chirality** | %30 | UV (350–500 nm) | Amino asit kiralite tespiti |
| **δ¹³C** | %25 | VIS (500–700 nm) | Biyolojik karbon izotopu oranı |
| **Redox** | %20 | NIR (700–1000 nm) | Oksidasyon-redüksiyon potansiyeli |
| **Assembly** | %15 | UV + VIS | Moleküler yapı karmaşıklığı |
Science Utility = Σ(metrik × ağırlık) - sistematik_düzeltme

text


---

## 🏗 Sistem Mimarisi
┌─────────────────────────────────────────────────────────────────┐
│ AstraBioEdge │
├─────────────────────────────────────────────────────────────────┤
│ │
│ ┌──────────┐ ┌──────────────┐ ┌───────────────────────┐ │
│ │ │ │ │ │ │ │
│ │ CSV │───▶│ VeriYonetici │───▶│ Veri Temizleme │ │
│ │ Girdi │ │ │ │ NaN/Aralık Kontrol │ │
│ │ │ │ │ │ Tip Dönüşümü │ │
│ └──────────┘ └──────┬───────┘ └───────────┬───────────┘ │
│ │ │ │
│ ▼ ▼ │
│ ┌──────────────────┐ ┌───────────────────────┐ │
│ │ │ │ │ │
│ │ HataTespitModeli │ │ 12-Boyutlu Özellik │ │
│ │ (RF Classifier) │◀───│ Çıkarımı │ │
│ │ │ │ │ │
│ └────────┬─────────┘ └───────────────────────┘ │
│ │ │
│ ▼ │
│ ┌──────────────────┐ │
│ │ │ ┌───────────────────────┐ │
│ │ HataKurtarma │───▶│ │ │
│ │ Modeli │ │ Science Utility │ │
│ │ (RF Regressor) │ │ Hesaplaması │ │
│ │ │ │ │ │
│ └──────────────────┘ └───────────┬───────────┘ │
│ │ │
│ ▼ │
│ ┌───────────────────────┐ │
│ │ CustomTkinter GUI │ │
│ │ 5 Sekmeli Görsel │ │
│ │ Analiz Paneli │ │
│ └───────────────────────┘ │
│ │
└─────────────────────────────────────────────────────────────────┘

text


### Sınıf Diyagramı
VeriYonetici
├── yukle(dosya_yolu) → DataFrame
├── ornek_csv_olustur(dosya_adi) → str
└── ozet() → dict

HataTespitModeli
├── ozellik_cikar(row) → List[float] (12 özellik)
├── beklenen_sinyal_hesapla(λ, θ, T, d) → float
└── egit(df, progress_cb) → dict

HataKurtarmaModeli
├── ozellik_cikar(row) → List[float] (7 özellik)
├── egit(df, progress_cb) → dict
└── kurtar(row) → float

ScienceUtility
└── hesapla(dalga_nm, intensite) → dict

CiftBitApp (CustomTkinter)
├── _arayuz()
├── _yukle() / _ornek()
├── _egit()
├── _analiz_et()
├── _veri_grafik() / _model_grafik()
├── _kurtarma_grafik() / _su_grafik()
└── _cevre_grafik()

text


---

## 📊 Veri Formatı

### CSV Sütun Yapısı

| Sütun | Tip | Aralık | Açıklama |
|-------|-----|--------|----------|
| `dalga_boyu_nm` | float | 200 – 1100 | Dalga boyu (nanometre) |
| `orijinal_intensite` | float | 0 – 2.0 | Temiz (bozulmamış) sinyal değeri |
| `bozuk_2bit_deger` | float | 0 – 2.0 | Çift bit hatası sonrası değer |
| `bozuk_hatali` | int | 0 / 1 | Hata bayrağı (0=Temiz, 1=Bozuk) |
| `gunes_acisi` | float | 5 – 85 | Güneş açısı (derece) |
| `sicaklik_c` | float | -120 – 20 | Yüzey sıcaklığı (°C) |
| `mesafe_m` | float | 0.1 – 10.0 | Hedefe mesafe (metre) |

### Örnek Veri

```csv
dalga_boyu_nm,orijinal_intensite,bozuk_2bit_deger,bozuk_hatali,gunes_acisi,sicaklik_c,mesafe_m
650.23,0.847321,0.847321,0,45.2,-30.5,2.100
862.10,0.612045,1.453872,1,72.8,-85.3,1.500
431.55,0.295110,0.295110,0,18.6,-110.2,5.800
Çift Bit Bozulma Simülasyonu
Python

# Orijinal değer → 16-bit tam sayıya dönüştürülür
int_val = int(orijinal / 2.0 * 65535)     # Örn: 0.847 → 27754

# İkili gösterim:  0110 1100 0101 1010
#                           ↑↑
#                     Rastgele 2 komşu bit çevrilir
int_val ^= (1 << bit_pozisyonu)
int_val ^= (1 << (bit_pozisyonu + 1))

# Bozulmuş:        0110 1100 0111 1010  → farklı bir değer
bozuk_deger = (int_val / 65535) * 2.0     # Örn: 1.453
🚀 Kurulum
Gereksinimler
Python 3.10 veya üzeri
İşletim sistemi: Windows / macOS / Linux
Adımlar
Bash

# 1. Depoyu klonlayın
git clone https://github.com/KULLANICI_ADI/AstraBioEdge.git
cd AstraBioEdge

# 2. Sanal ortam oluşturun (önerilen)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Uygulamayı başlatın
python astrabioedge.py
requirements.txt
text

numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
customtkinter>=5.2.0
📖 Kullanım
Hızlı Başlangıç
text

1.  Uygulamayı başlatın
2.  "📄 Örnek CSV Oluştur" ile test verisi üretin
3.  "📂 CSV Yükle" ile üretilen dosyayı yükleyin
4.  "🚀 Modeli Eğit" ile tespit ve kurtarma modellerini eğitin
5.  "📊 Tüm Veriyi Analiz Et" ile sonuçları inceleyin
Arayüz Sekmeleri
Sekme	İçerik
📊 Veri Özeti	Veri dağılımı, dalga boyu-intensite grafiği, sapma analizi
🧠 Model	Confusion matrix, precision/recall/F1, özellik önemleri
📈 Kurtarma	Orijinal vs bozuk vs kurtarılmış karşılaştırması, RMSE iyileşmesi
🎯 Science Utility	Bilimsel kullanılabilirlik skoru dağılımı ve ortalamaları
🌡️ Çevre Koşulları	Güneş açısı, sıcaklık, mesafe etkilerinin görselleştirilmesi
Kendi Verinizi Kullanma
CSV dosyanız aşağıdaki 7 sütunu içermelidir:

text

dalga_boyu_nm, orijinal_intensite, bozuk_2bit_deger,
bozuk_hatali, gunes_acisi, sicaklik_c, mesafe_m
Not: Sütun isimleri birebir eşleşmelidir. Uygulama yükleme sırasında eksik sütun kontrolü yapar ve hata mesajı verir.

📈 Deneysel Sonuçlar
Test Koşulları
Parametre	Değer
Veri seti boyutu	500 ölçüm
Bozulma oranı	%8 (40 satır)
Eğitim/Test oranı	80/20
Cross-validation	5-fold
Random seed	42
Hata Tespit Performansı
Metrik	Değer
Accuracy	0.9800
Precision	0.8889
Recall	1.0000
F1 Score (CV)	0.9310 ± 0.0540
Recall = 1.0 → Bozuk verilerin tamamı doğru tespit edilmektedir.

Kurtarma Performansı
Metrik	Değer
RMSE	0.0432
MAE	0.0298
R²	0.8750
RMSE İyileşmesi
text

Bozuk veri RMSE     :  0.3841
Kurtarılmış RMSE    :  0.0432
─────────────────────────────
İyileşme            :  %88.7
Özellik Önem Sıralaması (Tespit Modeli)
text

Normalize Sapma     ████████████████████████  0.31
Mutlak Sapma        ███████████████████       0.24
Beklenen Sinyal     ██████████████            0.18
Ölçülen Değer       ██████████                0.13
Aşırı Yüksek        ██████                    0.06
Güneş Açısı         ████                      0.04
Mesafe              ███                       0.02
Sıcaklık            ██                        0.02
Yorum: Fizik modeli ile hesaplanan "beklenen sinyal"den sapma, hata tespitinde en belirleyici özellik olarak öne çıkmaktadır. Bu, hibrit (fizik + ML) yaklaşımın geçerliliğini doğrulamaktadır.

🖼 Ekran Görüntüleri
Veri Özeti Sekmesi
text

┌─────────────────────────────────────────────────────────┐
│  📊 Veri Özeti                                          │
│  ┌─────────────┐  ┌──────────────────────────────────┐  │
│  │  Pie Chart  │  │  Dalga Boyu vs İntansite         │  │
│  │  Temiz %92  │  │  ● Temiz (yeşil)                 │  │
│  │  Bozuk %8   │  │  ● Bozuk (kırmızı)              │  │
│  └─────────────┘  └──────────────────────────────────┘  │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │  Histogram      │  │  Sapma Analizi               │  │
│  │  İntansite      │  │  |Bozuk - Orijinal|          │  │
│  │  Dağılımı       │  │  vs Dalga Boyu               │  │
│  └─────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
Model Performans Sekmesi
text

┌─────────────────────────────────────────────────────────┐
│  🧠 Model                                               │
│  ┌─────────────┐  ┌──────────────────────────────────┐  │
│  │  Confusion  │  │  Tespit Metrikleri               │  │
│  │  Matrix     │  │  Acc=0.98  Prec=0.89             │  │
│  │  TP FP      │  │  Rec=1.00  F1=0.93              │  │
│  │  FN TN      │  │                                  │  │
│  └─────────────┘  └──────────────────────────────────┘  │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │  Özellik        │  │  Kurtarma Metrikleri         │  │
│  │  Önemleri       │  │  RMSE=0.043  MAE=0.030      │  │
│  │  (Barh)         │  │  R²=0.875                    │  │
│  └─────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
🛠 Teknolojiler
Kategori	Teknoloji	Kullanım Amacı
Dil	Python 3.10+	Ana geliştirme dili
ML Framework	scikit-learn	Sınıflandırma ve regresyon modelleri
Veri İşleme	NumPy, Pandas	Sayısal hesaplama ve veri manipülasyonu
Görselleştirme	Matplotlib	Grafik ve chart oluşturma
Arayüz	CustomTkinter	Modern masaüstü GUI
Eşzamanlılık	threading	Model eğitiminde UI donmasını önleme
📁 Proje Yapısı
text

AstraBioEdge/
│
├── astrabioedge.py         # Ana uygulama (tek dosya, tüm modüller dahil)
├── requirements.txt        # Python bağımlılıkları
├── README.md               # Bu dosya
├── LICENSE                  # MIT Lisansı
│
├── bozuk_2bit_veri.csv     # Örnek veri seti (uygulama içinden üretilebilir)
│
└── docs/
    └── screenshots/        # Ekran görüntüleri
🔮 Gelecek Geliştirmeler
 EDAC Simülasyonu — Hamming, Reed-Solomon gibi hata düzeltme kodlarının entegrasyonu
 Çoklu Bit Hataları — 3-bit ve 4-bit upset senaryoları
 Gerçek Zamanlı Mod — Akan veri üzerinde anlık tespit ve kurtarma
 Deep Learning — LSTM/Transformer tabanlı zaman serisi anomali tespiti
 Rapor Dışa Aktarma — PDF formatında analiz raporu oluşturma
 API Modu — REST API ile uzaktan erişim desteği
🤝 Katkı
Katkılarınızı memnuniyetle karşılıyoruz.

Bash

# 1. Fork yapın
# 2. Feature branch oluşturun
git checkout -b feature/yeni-ozellik

# 3. Değişikliklerinizi commit edin
git commit -m "feat: yeni özellik eklendi"

# 4. Push yapın
git push origin feature/yeni-ozellik

# 5. Pull Request açın
📄 Lisans
Bu proje MIT Lisansı altında lisanslanmıştır.

📚 Referanslar
Normand, E. (1996). Single Event Upset at Ground Level. IEEE Transactions on Nuclear Science.
Baumann, R.C. (2005). Radiation-Induced Soft Errors in Advanced Semiconductor Technologies. IEEE Transactions on Device and Materials Reliability.
Hassler, D.M. et al. (2014). Mars' Surface Radiation Environment Measured with the Mars Science Laboratory's Curiosity Rover. Science, 343(6169).
Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5–32.
<div align="center">
AstraBioEdge — Uzayda veri bütünlüğü, yeryüzünde güvenilirlik.

Geliştirici: Hayalden Gerçeğe Delta Space Takımı | 2025

</div> ```

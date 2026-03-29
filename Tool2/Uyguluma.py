def otonom_karar_motoru(anlik_sicaklik, ogrenilmis_profil, sys_a_skor, sys_b_skor):
    """
    Mars rover'ının veya İHA'nın otonom karar verme algoritması.
    Statik (NASA) ve Dinamik (Öğrenilmiş) limitleri kıyaslayarak aksiyon üretir.
    """
    rapor = {}
    
    # ---------------------------------------------------------
    # 1. ADIM: FİZİKSEL LİMİT KONTROLÜ (STATİK GÜVENLİK)
    # NASA'nın asla değişmeyen donanım limitleri (-130°C ile +30°C arası)
    # ---------------------------------------------------------
    if anlik_sicaklik < -130 or anlik_sicaklik > 30:
        rapor["Donanim_Guvenligi"] = "KRİTİK İHLAL"
        rapor["Sistem_Tepkisi"] = "Sistemi Güvenli Moda Al (Safe Mode)"
        return rapor # Fiziksel limit aşıldıysa diğer analizleri beklemeden sistemi korumaya al.
    else:
        rapor["Donanim_Guvenligi"] = "GÜVENLİ"

    # ---------------------------------------------------------
    # 2. ADIM: PROFİL SAPMA ANALİZİ (DİNAMİK ÖĞRENME)
    # Sistemin o anki zaman dilimi için geçmişten öğrendiği değere göre sapması
    # ---------------------------------------------------------
    sapma_miktari = abs(anlik_sicaklik - ogrenilmis_profil)
    
    # Donanımsal Karar Ağacı (Karar: Normal, Şüpheli veya Hatalı)
    if sapma_miktari < 10:
        rapor["MEDA_Karar"] = "NORMAL"
        rapor["Donanim_Aksiyonu"] = "Rutin Veri Akışına Devam Et"
        
    elif sapma_miktari < 50: # %10 ile %50 arası sapma
        rapor["MEDA_Karar"] = "ŞÜPHELİ SİNYAL"
        rapor["Donanim_Aksiyonu"] = "Aynı Noktadan Teyit Ölçümü Planla (Double-Check)"
        
    else: # %50 ve üstü sapma
        rapor["MEDA_Karar"] = "SENSÖR SORUNU"
        rapor["Donanim_Aksiyonu"] = "Sensörü Yeniden Kalibre Et (Re-Calibration)"

    # ---------------------------------------------------------
    # 3. ADIM: BİLİMSEL OTONOMİ (SCIENCE FILTER) VE TERCİHLER
    # Sistem A (Sabit Eşik - %60) ve Sistem B (Dinamik Eşik - %40) çarpışması
    # ---------------------------------------------------------
    
    # ÖZEL DURUM (P0) TESPİTİ:
    # Eğer Statik sistem sinyali hiç tanımıyor (skor<10) ama 
    # Öğrenen sistem "Bu çok farklı bir şey!" (skor>90) diyorsa:
    if sys_a_skor <= 10 and sys_b_skor >= 90:
        rapor["Final_Skor"] = sys_b_skor # İnisiyatif Sistem B'ye (Yapay Zekaya) geçer
        rapor["Bilimsel_Karar"] = "P0 - BİLİNMEYEN ANOMALİ (Keşif Potansiyeli)"
        rapor["Bilimsel_Aksiyon"] = "Dünya'ya (Yer İstasyonuna) Acil Yüksek Öncelikli Veri Paketi Gönder"
        rapor["Ozel_Durum_Flag"] = 1 # Bayrak kaldırıldı
        
    # RUTİN İŞLEYİŞ (Ağırlıklı Ortalama):
    else:
        # Puanları katsayılarla birleştir (A: 0.6, B: 0.4)
        birlesik_skor = (sys_a_skor * 0.6) + (sys_b_skor * 0.4)
        rapor["Final_Skor"] = round(birlesik_skor, 1)
        rapor["Ozel_Durum_Flag"] = 0
        
        # Karar ve Tercih Ataması
        if birlesik_skor >= 60:
            rapor["Bilimsel_Karar"] = "P1 - YÜKSEK ÖNCELİK"
            rapor["Bilimsel_Aksiyon"] = "Veriyi sıkıştırmadan hemen ilet."
        elif birlesik_skor >= 35:
            rapor["Bilimsel_Karar"] = "P2 - STANDART ANALİZ"
            rapor["Bilimsel_Aksiyon"] = "Veriyi standart sıraya al."
        else:
            rapor["Bilimsel_Karar"] = "P3 - RUTİN VERİ"
            rapor["Bilimsel_Aksiyon"] = "Veriyi sıkıştır ve düşük öncelikle depola."

    return rapor
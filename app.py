import streamlit as st
import streamlit.components.v1 as components
import json
import random
import re
import os
import sys
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Yeni ve Eski SDK Uyumluluk Kontrolü
try:
    from google import genai
    from google.genai import types
    NEW_SDK_AVAILABLE = True
except ImportError:
    NEW_SDK_AVAILABLE = False

try:
    import google.generativeai as legacy_genai
    LEGACY_SDK_AVAILABLE = True
except ImportError:
    LEGACY_SDK_AVAILABLE = False

# Matplotlib çizim hızını artırmak için hızlı stil seçimi
plt.style.use('fast')

# --- RENDER / SAYFA AYARI ---
st.set_page_config(
    page_title="Soru Fabrikası Tablet Sınav Modülü",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN VE YÜKSEK OKUNABİLİR ÖZEL CSS ---
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .custom-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
    }
    .soru-metni-kutusu {
        font-size: 21px !important;
        font-weight: 600 !important;
        color: #0f172a !important;
        line-height: 1.6 !important;
        text-align: left !important;
    }
    .gorsel-sema-kutusu {
        background-color: #ffffff;
        color: #0f172a;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
        margin: 12px auto;
        border: 2px solid #cbd5e1;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        max-width: 100%;
    }
    .stRadio label {
        font-size: 19px !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }
    div.stButton > button {
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
    }
    /* Secondary (İkincil / Önceki-Sonraki) Buton Stili */
    div.stButton > button[data-testid="stBaseButton-secondary"] {
        background: linear-gradient(135deg, #f97316 0%, #ea580c) !important;
        border: none !important;
        color: #ffffff !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 16px -4px rgba(249, 115, 22, 0.4);
    }
    div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background: linear-gradient(135deg, #ea580c 0%, #c2410c) !important;
        box-shadow: 0 12px 20px -4px rgba(249, 115, 22, 0.6);
    }
    /* Primary (Ana) Buton Stili */
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        border: none !important;
        color: #ffffff !important;
        padding: 0.85rem 2rem;
        font-size: 19px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        box-shadow: 0 10px 20px -5px rgba(124, 58, 237, 0.4);
        border-radius: 14px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%) !important;
        box-shadow: 0 14px 24px -4px rgba(124, 58, 237, 0.6);
        transform: translateY(-3px);
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #4f46e5 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #0f172a;
        font-family: 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] .stExpander {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
    }
    section[data-testid="stSidebar"] .stExpander summary {
        font-weight: 700 !important;
        color: #1e293b !important;
    }
    div.row-widget.stCheckbox {
        background-color: #ffffff !important;
        padding: 10px 14px !important;
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        margin-bottom: 8px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    div.row-widget.stCheckbox label p {
        color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- KALICI GÜNLÜK SAYAC YÖNETİMİ ---
SAYAC_DOSYASI = "soru_sayac_veritabani.json"

def veritabani_yukle():
    if os.path.exists(SAYAC_DOSYASI):
        try:
            with open(SAYAC_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def veritabani_kaydet(veri):
    try:
        with open(SAYAC_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def bugunku_soru_sayisini_getir():
    bugun_str = datetime.now().strftime("%Y-%m-%d")
    db = veritabani_yukle()
    return db.get(bugun_str, 0)

def soru_sayisini_artir(eklenecek_adet):
    bugun_str = datetime.now().strftime("%Y-%m-%d")
    db = veritabani_yukle()
    mevcut = db.get(bugun_str, 0)
    db[bugun_str] = mevcut + eklenecek_adet
    veritabani_kaydet(db)

# --- DİNAMİK HARF ÇIKARICI ---
def get_custom_labels(etiketler, default_tuple=("A", "B", "C")):
    if not isinstance(etiketler, dict) or not etiketler:
        return default_tuple
    vertex_keys = [k for k in etiketler.keys() if isinstance(k, str) and len(k) == 1 and k.isupper()]
    if len(vertex_keys) >= 3:
        return (
            etiketler.get(vertex_keys[0], vertex_keys[0]), 
            etiketler.get(vertex_keys[1], vertex_keys[1]), 
            etiketler.get(vertex_keys[2], vertex_keys[2])
        )
    return default_tuple

# --- VEKTÖREL GÖRSEL ÇİZİCİ ---
@st.cache_data(show_spinner=False)
def ciz_vektorel_gorsel(gorsel_tipi="yok", etiketler=None):
    if not isinstance(etiketler, dict):
        etiketler = {}
        
    fig, ax = plt.subplots(figsize=(4.5, 3.3))
    ax.set_aspect('equal')
    ax.axis('off')
    
    tip = str(gorsel_tipi).lower()
    
    if tip == "yok":
        plt.close(fig)
        return None

    elif "gunes_dunya_ay" in tip or "astronomi" in tip:
        sun = plt.Circle((1.0, 2.5), 0.7, color='#f59e0b', ec='#d97706', linewidth=2)
        ax.add_patch(sun)
        ax.text(1.0, 2.5, etiketler.get("G", "GÜNEŞ"), fontsize=8, fontweight='bold', ha='center', va='center', color='#ffffff')
        
        earth = plt.Circle((3.0, 2.5), 0.45, color='#38bdf8', ec='#0284c7', linewidth=2)
        ax.add_patch(earth)
        ax.text(3.0, 2.5, etiketler.get("D", "DÜNYA"), fontsize=7, fontweight='bold', ha='center', va='center', color='#0f172a')
        
        moon = plt.Circle((4.1, 3.2), 0.2, color='#cbd5e1', ec='#64748b', linewidth=1.5)
        ax.add_patch(moon)
        ax.text(4.1, 3.2, etiketler.get("A", "AY"), fontsize=6, fontweight='bold', ha='center', va='center', color='#1e293b')
        
        theta = np.linspace(0, 2*np.pi, 60)
        ax.plot(3.0 + 1.1*np.cos(theta), 2.5 + 0.7*np.sin(theta), color='#94a3b8', linestyle='--', linewidth=1)
        ax.text(3.0, 3.4, etiketler.get("O", "Yörünge"), fontsize=8, color='#64748b', ha='center')

    elif "dinamometre" in tip or "kuvvet_hareket" in tip:
        ax.plot([3.0, 3.0], [4.4, 4.0], color='#475569', linewidth=3)
        ring = plt.Circle((3.0, 4.5), 0.15, color='#475569', fill=False, linewidth=2.5)
        ax.add_patch(ring)
        
        body = plt.Rectangle((2.6, 1.8), 0.8, 2.2, color='#e2e8f0', ec='#0f172a', linewidth=2, alpha=0.8)
        ax.add_patch(body)
        
        y_spring = np.linspace(3.9, 2.7, 10)
        x_spring = 3.0 + 0.15 * np.sin(np.linspace(0, 4*np.pi, 10))
        ax.plot(x_spring, y_spring, color='#f97316', linewidth=2)
        
        for y_tick in np.linspace(2.8, 3.8, 6):
            ax.plot([2.6, 2.8], [y_tick, y_tick], color='#0f172a', linewidth=1.2)
            
        ax.plot([3.0, 3.0], [1.8, 1.2], color='#475569', linewidth=2.5)
        weight_box = plt.Rectangle((2.5, 0.5), 1.0, 0.7, color='#cbd5e1', ec='#0f172a', linewidth=2)
        ax.add_patch(weight_box)
        ax.text(3.0, 0.85, etiketler.get("Y", "Yük"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')
        ax.text(3.6, 2.8, etiketler.get("N", "N"), fontsize=10, fontweight='bold', color='#dc2626')

    elif "grafik" in tip or "tablo" in tip or "veri" in tip:
        ax.bar([1.5, 3.0, 4.5], [3, 5, 2], width=0.8, color=['#38bdf8', '#f97316', '#a855f7'], ec='#0f172a', linewidth=1.5)
        ax.set_xlim(0.5, 5.5)
        ax.set_ylim(0, 6)
        ax.axhline(0, color='#0f172a', linewidth=1.5)
        ax.text(3.0, 5.5, etiketler.get("Baslik", "Veri Analizi Grafiği"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')

    elif "cember" in tip or "daire" in tip:
        cember = plt.Circle((3.0, 2.5), 1.5, color='#0f172a', fill=False, linewidth=2.2)
        ax.add_patch(cember)
        ax.plot(3.0, 2.5, 'ko', markersize=5)
        ax.text(3.1, 2.65, etiketler.get("M", "M"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.plot([3.0, 4.5], [2.5, 2.5], color='#dc2626', linewidth=1.8, linestyle='--')
        ax.text(3.75, 2.7, etiketler.get("r", "r"), fontsize=10, fontweight='bold', color='#dc2626')

    elif "dik_ucgen" in tip:
        lbl_a, lbl_b, lbl_c = get_custom_labels(etiketler, ("A", "B", "C"))
        bx, by = 1.2, 1.0
        cx, cy = 4.8, 1.0
        ax_val, ay_val = 1.2, 4.0
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        ax.plot([1.2, 1.5, 1.5, 1.2], [1.0, 1.0, 1.3, 1.3], color='#0f172a', linewidth=1.5)
        ax.text(ax_val - 0.25, ay_val + 0.1, lbl_a, fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, lbl_b, fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.15, cy - 0.25, lbl_c, fontsize=11, fontweight='bold', color='#0f172a')

    else:
        plt.close(fig)
        return None

    ax.set_xlim(0, 6)
    ax.set_ylim(0, 5.0)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=130, transparent=True)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_str}"

# --- MEB MÜFREDATI ---
MUGREDAT = {
    "4. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümle Bilgisi", "Paragraf Yorumlama", "Yazım Kuralları ve Noktalama", "Metin Türleri ve Söz Sanatları"],
        "Matematik": ["Doğal Sayılar ve İşlemler", "Geometrik Şekiller ve Cisimler", "Kesirler", "Zaman Ölçme", "Veri Toplama ve Değerlendirme"],
        "Fen Bilimleri": ["Yer Kabuğu ve Dünyamız", "Besinlerimiz", "Kuvvetin Etkileri", "Maddenin Özellikleri", "Aydınlatma ve Ses Teknolojileri"],
        "Sosyal Bilgiler": ["Birey ve Toplum", "Kültür ve Miras", "İnsanlar ve Yerler", "Üretim, Dağıtım ve Tüketim", "Etkin Vatandaşlık"],
        "Din Kültürü": ["Dinimiz Hayatımız", "İslam'ın İnanç Esasları", "Hz. Muhammed'i Tanıyalım", "Ahlaki Değerler"],
        "İngilizce": ["Classroom Rules", "Nationality", "Cartoon Characters", "Free Time", "My Day", "Body Parts"],
        "Almanca": ["Hallo!", "Sich vorstellen", "Zahlen und Farben", "Familie und Freunde"]
    },
    "5. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Metin Yorumlama ve Paragraf", "Yazım Kuralları", "Noktalama İşaretleri"],
        "Matematik": ["Doğal Sayılarla İşlemler", "Kesirler", "Ondalık Gösterimler", "Yüzdeler", "Üçgen ve Dörtgenler", "Veri İşleme", "Çember ve Daire", "Açı çeşitleri ve Dörtgende Açılar", "Temel Geometrik Kavramlar ve Doğrular"],
        "Fen Bilimleri": ["Güneş, Dünya ve Ay", "Canlılar Dünyası", "Kuvvetin Uygulanması ve Sürtünme", "Maddenin Hâl Değişimi ve Isı", "Kuvveti Tanıyalım", "Işığın Yayılması"],
        "Sosyal Bilgiler": ["Birey ve Toplum", "Kültür ve Miras", "İnsanlar, Yerler ve Çevre", "Bilim, Teknoloji ve Toplum", "Üretim, Dağıtım ve Tüketim"],
        "Din Kültürü": ["Allah İnancı ve İnsan", "Hz. Muhammed ve Aile Hayatı", "İslam'ın Temel İbadetleri", "Ahlaki Değerler"],
        "İngilizce": ["Hello!", "My Town", "Games and Hobbies", "My Daily Routine", "Health", "Movies"],
        "Almanca": ["Guten Tag!", "Hobbys", "Tagesablauf", "Essen und Trinken", "Wohnen"]
    },
    "6. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragraf Bilgisi", "Metin Türleri", "Fiiller"],
        "Matematik": ["Çarpanlar ve Katlar", "Kümeler", "Tam Sayılar", "Kesirlerle İşlemler", "Cebirsel İfadeler", "Açılar", "Üçgende Açılar ve Alan", "Çember ve Daire", "Dörtgende Çevre ve Alan"],
        "Fen Bilimleri": ["Güneş Sistemi ve Tutulmalar", "Vücudumuzdaki Sistemler", "Kuvvet ve Hareket", "Madde ve Isı", "Ses ve Özellikleri"],
        "Sosyal Bilgiler": ["Biz ve Toplum", "Yeryüzünde Yaşam", "Türklerin Tarihsel Yolculuğu", "Ussal Ekonomi", "Yönetimimiz ve Demokrasi"],
        "Din Kültürü": ["Peygamber ve İlahi Kitaplar", "Namaz İbadeti", "Hz. Muhammed'in Hayatı", "Ahlaki Tutum ve Davranışlar"],
        "İngilizce": ["Life", "Yummy Breakfast", "Downtown", "Weather and Emotions", "At the Fair", "Vacations"],
        "Almanca": ["Mein Körper und Gesundheit", "Kleidung", "Wetter und Jahreszeiten", "Freizeitaktivitäten", "Schule"]
    },
    "7. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Fiilimsiler"],
        "Matematik": ["Tam Sayılarla İşlemler", "Rasyonel Sayılar", "Eşitlik ve Denklem", "Açılar ve Çokgenler"],
        "Fen Bilimleri": ["Güneş Sistemi ve Ötesi", "Hücre ve Bölünmeler", "Kuvvet ve Enerji"],
        "Sosyal Bilgiler": ["Birlikte Yaşamak", "Ülkemizde Nüfus"],
        "Din Kültürü": ["Melek ve Ahiret İnancı", "Hac ve Kurban"],
        "İngilizce": ["Appearance and Personality", "Sports"],
        "Almanca": ["Reisen und Urlaub", "Berufe"]
    },
    "8. Sınıf": {
        "Türkçe": ["Fiilimsiler", "Cümlenin Ögeleri", "Sözel Mantık ve Muhakeme"],
        "Matematik": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Doğrusal Denklemler"],
        "Fen Bilimleri": ["Mevsimlerin Oluşumu ve İklim", "DNA ve Genetik Kod", "Basınç"],
        "Sosyal Bilgiler": ["Bir Demokrasi Kahramanı: Atatürk", "Milli Uyanış"],
        "Din Kültürü": ["Kader İnancı", "Zekat ve Sadaka"],
        "İngilizce": ["Friendship", "Teen Life"],
        "Almanca": ["Kommunikation", "Medien"]
    },
    "Genel Yetenek & Aktiviteler": {
        "Bilgi Yarışması": ["Genel Kültür", "Tarih", "Coğrafya", "Bilim ve Uzay", "Spor ve Sanat"],
        "Zihinden Dört İşlem": ["Hızlı Toplama ve Çıkarma", "Çarpım Tablosu Hakimiyeti"],
        "Almanca Pratik": ["Temel Kelimeler", "Günlük Diyaloglar"]
    },
    "LGS Hazırlık": {
        "Türkçe": ["Sözel Mantık ve Muhakeme", "Paragraf Analizi"],
        "Matematik": ["Yeni Nesil Beceri Temelli Sorular", "Geometri ve Üçgende Açılar"],
        "Fen Bilimleri": ["LGS Fen Bilimleri Kapsamlı Karma Denemeler"]
    }
}

# --- GÜVENLİ API ANAHTARI YÖNETİMİ ---
raw_keys = st.secrets.get("API_KEYS", [])
if isinstance(raw_keys, str):
    API_KEYS = [raw_keys.strip()]
elif isinstance(raw_keys, list):
    API_KEYS = [str(k).strip() for k in raw_keys if str(k).strip()]
else:
    API_KEYS = []

def temizle_latex_metin(text):
    if not isinstance(text, str):
        return str(text)
    text = re.sub(r'\\circ\b', '°', text)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', text)
    text = text.replace('\\%', '%').replace('$', '').strip()
    return text

def kararli_json_ayikla(raw_text):
    try:
        clean_text = re.sub(r'```(?:json)?\s*([\s\S]*?)\s*```', r'\1', raw_text).strip()
        match = re.search(r'(\[.*\]|\{.*\})', clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1)
        parsed = json.loads(clean_text)
        if isinstance(parsed, dict):
            return [parsed]
        elif isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    return []

# Hata Toleranslı Çoklu SDK Destekli Hızlandırılmış API Çağrısı
def güvenli_api_cagrisi_yap(api_key, prompt):
    # 1. Yöntem: Yeni SDK (google-genai) - Maksimum Hız Konfigürasyonu
    if NEW_SDK_AVAILABLE:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=2560
                )
            )
            if response and response.text:
                return response.text, None
        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "400" in err_msg or "401" in err_msg:
                return None, f"Geçersiz API Anahtarı ({api_key[:8]}...)"

    # 2. Yöntem: Eski/Klasik SDK Fallback (google-generativeai)
    if LEGACY_SDK_AVAILABLE:
        try:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel("gemini-3.6-flash")
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 2560}
            )
            if response and response.text:
                return response.text, None
        except Exception as e:
            return None, f"İstek Hatası: {str(e)}"

    return None, "Desteklenen Gemini SDK kütüphanesi yüklenemedi veya anahtar geçersiz."

# Paralele Yakın/Hızlı API Çağrısı Yöneticisi
def hizli_soru_uretimi_yap(prompt):
    if not API_KEYS:
        return None, ["API Anahtarı eksik!"]
    
    # Anahtar havuzunu paralelleştirilmiş biçimde dene
    with ThreadPoolExecutor(max_workers=min(len(API_KEYS), 4)) as executor:
        futures = [executor.submit(güvenli_api_cagrisi_yap, key, prompt) for key in API_KEYS]
        hata_kayitlari = []
        for future in futures:
            res_text, err_detay = future.result()
            if res_text:
                questions = kararli_json_ayikla(res_text)
                if questions:
                    return questions, None
            if err_detay:
                hata_kayitlari.append(err_detay)
    return None, hata_kayitlari

# SUNUCU YÜKÜ VE TAHMİNİ SÜRE HESAPLAYICI (Soru Sayısı + Sunucu Durumu + 6 Saniye)
def tahmini_uretim_suresi_hesapla(adet):
    # Temel soru başı ortalama üretme süresi (Hızlandırılmış model için ~0.75s)
    soru_basi_saniye = 0.75
    
    # Sunucu Yükü / Gecikme Gözlemi (Peak Saatler / Rastgele Yoğunluk Simülasyonu)
    saat = datetime.now().hour
    if 13 <= saat <= 22:
        sunucu_gecikme_faktoru = 1.3  # Yoğun saatler
        sunucu_durumu = "Orta / Yoğun"
    else:
        sunucu_gecikme_faktoru = 1.0  # Normal saatler
        sunucu_durumu = "Hızlı / Akıcı"
        
    hesaplanan_barem = (adet * soru_basi_saniye) * sunucu_gecikme_faktoru
    # İstediğiniz Sabit 6 Saniye Payı
    toplam_tahmin = int(np.ceil(hesaplanan_barem + 6))
    return max(toplam_tahmin, 8), sunucu_durumu

# --- SESSION STATE TANIMLARI ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "quiz_ready_to_start" not in st.session_state:
    st.session_state.quiz_ready_to_start = False
if "exam_started" not in st.session_state:
    st.session_state.exam_started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "total_duration" not in st.session_state:
    st.session_state.total_duration = None
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "performance_history" not in st.session_state:
    st.session_state.performance_history = []
if "yanlis_sorular_arsivi" not in st.session_state:
    st.session_state.yanlis_sorular_arsivi = []
if "secim_sifirla_tetikleyici" not in st.session_state:
    st.session_state.secim_sifirla_tetikleyici = 0

# URL Parametresi ile Zaman Aşımı Kontrolü
query_params = st.query_params
if "time_out" in query_params and query_params["time_out"] == "true":
    if st.session_state.exam_started and not st.session_state.quiz_submitted:
        st.session_state.quiz_submitted = True
        st.session_state.exam_started = False
        st.session_state.total_duration = int(time.time() - (st.session_state.start_time or time.time()))
        st.query_params.clear()
        st.rerun()

# --- KENAR ÇUBUĞU ---
with st.sidebar:
    st.markdown("### 🔮 Soru Fabrikası Soru Paneli")
    st.markdown("---")

    bugunku_toplam = bugunku_soru_sayisini_getir()
    st.metric(label="📅 Bugün Üretilen Toplam Soru", value=bugunku_toplam)
    st.markdown("---")

    if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
        st.warning("⚠️ `.streamlit/secrets.toml` dosyasına geçerli Gemini API anahtarınızı ekleyin.")

    secili_sinif = st.selectbox("Eğitim Seviyesi / Kategori:", list(MUGREDAT.keys()), key=f"sinif_secim_{st.session_state.secim_sifirla_tetikleyici}")
    
    sinav_turu = st.selectbox("Sınav Türü:", [
        "Genel Tarama Sınavı",
        "Konu Tarama Sınavı",
        "Yanlışlardan Üretilen Sorular",
        "Hazır Bulunuşluk Sınavı",
        "Yeni Nesil Sorular"
    ], key=f"tur_secim_{st.session_state.secim_sifirla_tetikleyici}")

    zorluk_seviyesi = st.selectbox("🎯 Soru Zorluk Seviyesi:", ["Kolay", "Orta", "Zor", "Karma / Dengeli"], key=f"zorluk_secim_{st.session_state.secim_sifirla_tetikleyici}")

    st.markdown("---")
    st.markdown("📚 **Dersler ve Üniteler**")

    mevcut_dersler = MUGREDAT.get(secili_sinif, {})
    secili_ders_unite_haritasi = {}

    for ders_adi, uniteler_listesi in mevcut_dersler.items():
        with st.expander(f"📘 {ders_adi}"):
            ders_secildi = st.checkbox(f"Tüm {ders_adi} Kategorisini Dahil Et", key=f"chk_ders_{st.session_state.secim_sifirla_tetikleyici}_{secili_sinif}_{ders_adi}")
            secili_alt_uniteler = []
            for unite in uniteler_listesi:
                if st.checkbox(unite, key=f"chk_unite_{secili_sinif}_{ders_adi}_{unite}"):
                    secili_alt_uniteler.append(unite)
            
            if ders_secildi or secili_alt_uniteler:
                secili_ders_unite_haritasi[ders_adi] = secili_alt_uniteler if secili_alt_uniteler else uniteler_listesi

    st.markdown("---")
    soru_sayisi = st.slider("🔢 Soru Sayısı:", 5, 25, 5, key=f"slider_soru_{st.session_state.secim_sifirla_tetikleyici}")

    if st.button("🚀 Soruları Üret", use_container_width=True, type="primary"):
        if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
            st.error("Geçerli bir API anahtarı bulunamadı!")
        elif not secili_ders_unite_haritasi:
            st.error("Lütfen en az bir ders veya ünite seçiniz!")
        else:
            ders_unite_detay = ""
            for d, u_list in secili_ders_unite_haritasi.items():
                ders_unite_detay += f"- Ders/Kategori: {d}, Alt Başlıklar/Üniteler: {', '.join(u_list)}\n"

            gorsel_talimati = """
            GEOMETRİK ÇİZİM VE GÖRSEL SORU KURALLARI:
            Uygun sorular için `gorsel_tipi` ataması yapın ("dik_ucgen", "eskenar_ucgen", "cember", "gunes_dunya_ay", "dinamometre", "grafik", "basinc"). 
            Görsel gerektirmeyen sorularda `gorsel_tipi` "yok" olmalıdır.
            """

            rastgele_tohum = random.randint(10000, 99999)

            prompt = f"""
Sen MEB müfredatına tam hakim profesyonel bir soru hazırlama yapay zekasısın.
{secili_sinif} seviyesinde, '{sinav_turu}' konseptinde, TOPLAM {soru_sayisi} adet nitelikli, özgün soru üret. (Varyasyon koda: {rastgele_tohum})

{gorsel_talimati}

Zorluk Seviyesi: {zorluk_seviyesi}
Seçilen Dersler:
{ders_unite_detay}

Yanıtı sadece şu JSON formatında ver (saf JSON dizisi döndür):
[
  {{
    "soru_metni": "Soru metni...",
    "secenekler": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "dogru_cevap": "A",
    "cozum_aciklamasi": "Çözüm açıklaması...",
    "ders": "Kategori/Ders Adı",
    "gorsel_tipi": "yok", 
    "etiketler": {{}}
  }}
]
"""
            # Tahmini Süre & Sunucu Durumu Hesaplaması (+ 6 Saniye dahil)
            tahmini_sure, sunucu_durumu = tahmini_uretim_suresi_hesapla(soru_sayisi)

            # TURUNCU RENKLİ DİNAMİK GERİ SAYIM SAYAÇ BİLEŞENİ (HTML / JS)
            countdown_html = f"""
            <div style="
                background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
                border: 2px solid #f97316;
                border-radius: 14px;
                padding: 18px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(249, 115, 22, 0.15);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin-bottom: 20px;">
                <div style="font-size: 16px; color: #c2410c; font-weight: 700; margin-bottom: 6px;">
                    ⚡ SORU FABRİKASI YAPAY ZEKA MOTORU
                </div>
                <div style="font-size: 13px; color: #9a3412; margin-bottom: 12px;">
                    📊 Sunucu Durumu: <b>{sunucu_durumu}</b> | Soru Adedi: <b>{soru_sayisi}</b> | Tolerans: <b>+6 sn</b>
                </div>
                <div style="
                    font-size: 34px;
                    font-weight: 900;
                    color: #ea580c;
                    letter-spacing: 1px;
                    text-shadow: 0 2px 4px rgba(234, 88, 12, 0.2);">
                    ⏳ <span id="gen-timer">{tahmini_sure:02d}</span> saniye
                </div>
                <div style="font-size: 13px; color: #ea580c; font-weight: 600; margin-top: 8px;">
                    Sorularınız hazırlanıyor, lütfen bekleyiniz...
                </div>
            </div>

            <script>
                var secondsLeft = {tahmini_sure};
                var timerSpan = document.getElementById('gen-timer');
                var timerInterval = setInterval(function() {{
                    secondsLeft--;
                    if (secondsLeft <= 0) {{
                        clearInterval(timerInterval);
                        timerSpan.innerHTML = "00";
                    }} else {{
                        timerSpan.innerHTML = (secondsLeft < 10 ? "0" : "") + secondsLeft;
                    }}
                }}, 1000);
            </script>
            """
            
            # Ekran Geri Sayım Widget'ı Render Et
            gen_counter_placeholder = st.empty()
            with gen_counter_placeholder.container():
                components.html(countdown_html, height=165)

            # Hızlandırılmış Paralel API Çağrısı
            questions, hata_kayitlari = hizli_soru_uretimi_yap(prompt)

            # İşlem Tamamlandı, Sayacı Temizle
            gen_counter_placeholder.empty()

            if questions:
                for q in questions:
                    q["soru_metni"] = temizle_latex_metin(q.get("soru_metni", ""))
                    if "secenekler" in q and isinstance(q["secenekler"], dict):
                        for k_sec, v_sec in q["secenekler"].items():
                            q["secenekler"][k_sec] = temizle_latex_metin(v_sec)
                    q["cozum_aciklamasi"] = temizle_latex_metin(q.get("cozum_aciklamasi", ""))
                
                st.session_state.quiz_data = questions
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.quiz_ready_to_start = True
                st.session_state.exam_started = False
                st.session_state.current_question = 0
                soru_sayisini_artir(len(questions))
                st.success("🎉 Sorular başarıyla üretildi! Sınava başlayabilirsiniz.")
                st.rerun()
            else:
                st.error("Sorular üretilirken bir hata oluştu.")
                if hata_kayitlari:
                    st.info(f"🔍 Alınan Hata Detayı: {hata_kayitlari[0]}")

# --- ANA EKRAN / SINAV YÖNETİMİ ---
st.title("🎓 Soru Fabrikası Tablet Sınav Modülü")

if st.session_state.quiz_ready_to_start and not st.session_state.exam_started and not st.session_state.quiz_submitted:
    toplam_sure_saniye = len(st.session_state.quiz_data) * 80
    dakika_hesap = toplam_sure_saniye // 60
    saniye_hesap = toplam_sure_saniye % 60
    
    st.markdown(f"""
    <div class="custom-card" style="text-align: center;">
        <h2>📋 Sınavınız Hazır!</h2>
        <p style="font-size: 18px; color: #475569;">Sorularınız özenle oluşturuldu. Her soru için <b>80 saniye</b> olmak üzere toplam süreniz <b>{dakika_hesap:02d}:{saniye_hesap:02d}</b> olarak belirlenmiştir.</p>
        <p style="font-size: 16px; color: #64748b;">Hazır olduğunuzda aşağıdaki butona basarak sınavı başlatabilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Sınavı Başlat", type="primary", use_container_width=True):
            st.session_state.exam_started = True
            st.session_state.start_time = time.time()
            st.session_state.total_duration = len(st.session_state.quiz_data) * 80
            st.rerun()

elif st.session_state.exam_started and not st.session_state.quiz_submitted:
    quiz_data = st.session_state.quiz_data
    total_q = len(quiz_data)
    curr_idx = st.session_state.current_question
    
    # Toplam Süre Hesaplama (Soru Sayısı * 80 saniye)
    if st.session_state.total_duration is None:
        st.session_state.total_duration = total_q * 80

    toplam_sure_saniye = st.session_state.total_duration
    gecen_sure = time.time() - st.session_state.start_time
    kalan_sure = int(toplam_sure_saniye - gecen_sure)

    if kalan_sure <= 0:
        st.session_state.quiz_submitted = True
        st.session_state.exam_started = False
        st.rerun()

    st.progress((curr_idx + 1) / total_q)
    
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        st.markdown(f"**Soru:** {curr_idx + 1} / {total_q}")
    with c2:
        st.markdown(f"**Ders:** {quiz_data[curr_idx].get('ders', 'Genel')}")
    with c3:
        # Dinamik Gerçek Zamanlı HTML/JS Sınav Sayaç Bileşeni
        timer_code = f"""
        <div id="timer-box" style="
            font-size: 20px; 
            font-weight: bold; 
            color: #dc2626; 
            background-color: #fef2f2; 
            padding: 8px 16px; 
            border-radius: 10px; 
            border: 1px solid #fca5a5;
            display: inline-block;
            text-align: center;
            font-family: sans-serif;">
            ⏱️ Kalan Süre: <span id="countdown">{kalan_sure // 60:02d}:{kalan_sure % 60:02d}</span>
        </div>
        <script>
            var timeLeft = {kalan_sure};
            var timerElement = document.getElementById('countdown');
            var interval = setInterval(function() {{
                timeLeft--;
                if (timeLeft <= 0) {{
                    clearInterval(interval);
                    timerElement.innerHTML = "00:00";
                    window.parent.postMessage({{type: 'streamlit:setComponentValue', value: true}}, '*');
                    var currentUrl = window.parent.location.href.split('?')[0];
                    window.parent.location.href = currentUrl + '?time_out=true';
                }} else {{
                    var minutes = Math.floor(timeLeft / 60);
                    var seconds = timeLeft % 60;
                    timerElement.innerHTML = (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                }}
            }}, 1000);
        </script>
        """
        components.html(timer_code, height=55)
    
    st.markdown("---")
    
    q = quiz_data[curr_idx]
    
    st.markdown(f"""
    <div class="custom-card">
        <div class="soru-metni-kutusu">{curr_idx + 1}. {q.get('soru_metni', '')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    gorsel_tipi = q.get("gorsel_tipi", "yok")
    etiketler = q.get("etiketler", {})
    if gorsel_tipi and gorsel_tipi != "yok":
        img_base64 = ciz_vektorel_gorsel(gorsel_tipi, etiketler)
        if img_base64:
            st.markdown(f"""
            <div class="gorsel-sema-kutusu">
                <img src="{img_base64}" style="max-width: 100%; height: auto;" />
            </div>
            """, unsafe_allow_html=True)
            
    secenekler = q.get("secenekler", {})
    options = [f"{k}) {v}" for k, v in secenekler.items()]
    
    current_ans = st.session_state.user_answers.get(curr_idx, None)
    default_idx = None
    if current_ans:
        for idx, opt in enumerate(options):
            if opt.startswith(current_ans):
                default_idx = idx
                break
                
    # Şıkların varsayılan olarak seçimsiz (boş) gelmesi sağlandı
    selected_opt = st.radio(
        "Cevabınızı Seçiniz:",
        options,
        index=default_idx if default_idx is not None else None,
        key=f"radio_q_{curr_idx}"
    )
    
    if selected_opt:
        st.session_state.user_answers[curr_idx] = selected_opt[0]
        
    st.markdown("---")
    
    nav_col1, nav_col2, nav_col3 = st.columns([2, 2, 2])
    
    with nav_col1:
        if curr_idx > 0:
            if st.button("⬅️ Önceki Soru", type="secondary", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()
                
    with nav_col2:
        if curr_idx < total_q - 1:
            if st.button("Sonraki Soru ➡️", type="secondary", use_container_width=True):
                st.session_state.current_question += 1
                st.rerun()
                
    with nav_col3:
        if st.button("🏁 Sınavı Bitir", type="primary", use_container_width=True):
            st.session_state.quiz_submitted = True
            st.session_state.exam_started = False
            st.session_state.total_duration = int(time.time() - st.session_state.start_time)
            st.rerun()

elif st.session_state.quiz_submitted:
    quiz_data = st.session_state.quiz_data
    total_q = len(quiz_data)
    dogru_sayisi = 0
    yanlis_sayisi = 0
    bos_sayisi = 0
    
    for i, q in enumerate(quiz_data):
        user_ans = st.session_state.user_answers.get(i, None)
        correct_ans = q.get("dogru_cevap", "")
        if not user_ans:
            bos_sayisi += 1
        elif user_ans == correct_ans:
            dogru_sayisi += 1
        else:
            yanlis_sayisi += 1
            st.session_state.yanlis_sorular_arsivi.append(q)
            
    toplam_sure = st.session_state.total_duration or 0
    dakika = toplam_sure // 60
    saniye = toplam_sure % 60
    puan = int((dogru_sayisi / total_q) * 100) if total_q > 0 else 0
    
    st.markdown("""
    <div class="custom-card" style="text-align: center;">
        <h2>🎉 Sınav Tamamlandı!</h2>
        <p style="font-size: 18px; color: #475569;">Sonuçlarınız aşağıda detaylandırılmıştır.</p>
    </div>
    """, unsafe_allow_html=True)
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Puan", f"{puan} / 100")
    m2.metric("Doğru", dogru_sayisi)
    m3.metric("Yanlış", yanlis_sayisi)
    m4.metric("Boş", bos_sayisi)
    m5.metric("Süre", f"{dakika:02d}:{saniye:02d}")
    
    st.markdown("---")
    st.markdown("### 📝 Soru Detayları ve Çözümler")
    
    for i, q in enumerate(quiz_data):
        user_ans = st.session_state.user_answers.get(i, "Boş")
        correct_ans = q.get("dogru_cevap", "")
        
        durum_metin = "✅ Doğru" if user_ans == correct_ans else ("❌ Yanlış" if user_ans != "Boş" else "⚠️ Boş")
        
        with st.expander(f"Soru {i+1}: {durum_metin} (Sizin Cevabınız: {user_ans} | Doğru Cevap: {correct_ans})"):
            st.markdown(f"**Soru:** {q.get('soru_metni', '')}")
            
            gorsel_tipi = q.get("gorsel_tipi", "yok")
            etiketler = q.get("etiketler", {})
            if gorsel_tipi and gorsel_tipi != "yok":
                img_base64 = ciz_vektorel_gorsel(gorsel_tipi, etiketler)
                if img_base64:
                    st.markdown(f"""
                    <div class="gorsel-sema-kutusu">
                        <img src="{img_base64}" style="max-width: 100%; height: auto;" />
                    </div>
                    """, unsafe_allow_html=True)
                    
            secenekler = q.get("secenekler", {})
            for k_s, v_s in secenekler.items():
                prefix = ""
                if k_s == correct_ans:
                    prefix = "✅ "
                elif k_s == user_ans:
                    prefix = "❌ "
                st.markdown(f"{prefix}**{k_s})** {v_s}")
                
            st.markdown("---")
            st.markdown(f"**💡 Çözüm Açıklaması:** {q.get('cozum_aciklamasi', '')}")
            
    st.markdown("---")
    if st.button("🔄 Yeni Sınav Oluştur", type="primary", use_container_width=True):
        st.session_state.quiz_data = None
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.quiz_ready_to_start = False
        st.session_state.exam_started = False
        st.session_state.current_question = 0
        st.session_state.secim_sifirla_tetikleyici += 1
        st.rerun()
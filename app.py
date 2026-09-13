import streamlit as st
import json
import random
import re
import os
import sys
import time
from datetime import datetime
from google import genai
from google.genai import types
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import threading

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
        text-align: center;
    }
    .soru-metni-kutusu {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #0f172a !important;
        line-height: 1.6 !important;
        text-align: left !important;
    }
    .gorsel-sema-kutusu {
        background-color: #ffffff;
        color: #0f172a;
        padding: 12px;
        border-radius: 12px;
        text-align: center;
        margin: 12px auto;
        border: 2px solid #cbd5e1;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        max-width: 420px;
    }
    .stRadio label {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.2);
    }
    .stButton>button[kind="primary"] {
        background-color: #f97316 !important;
        border-color: #f97316 !important;
        color: #ffffff !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #ea580c !important;
        border-color: #ea580c !important;
    }
    div[data-testid="stProgress"] > div > div > div {
        background-color: #9333ea !important;
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #dc2626 !important;
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

# --- DÜZELTİLMİŞ VE GÜÇLENDİRİLMİŞ GEOMETRİ ÇİZİCİ ---
def ciz_vektorel_geometri(geometri_tipi="ucgen", etiketler=None):
    if not isinstance(etiketler, dict):
        etiketler = {}
        
    fig, ax = plt.subplots(figsize=(3.8, 2.6))
    ax.set_aspect('equal')
    ax.axis('off')
    
    tip = str(geometri_tipi).lower()
    
    if "dik_ucgen" in tip or "dik üçgen" in tip:
        bx, by = 1.0, 1.0
        cx, cy = 5.0, 1.0
        ax_val, ay_val = 1.0, 4.2
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round', solid_joinstyle='round')
        ax.plot([1.0, 1.4, 1.4, 1.0], [1.0, 1.0, 1.4, 1.4], color='#0f172a', linewidth=1.5)
        
        ax.text(ax_val - 0.2, ay_val + 0.15, etiketler.get("A", "A"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(bx - 0.2, by - 0.2, etiketler.get("B", "B"), fontsize=10, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.2, etiketler.get("C", "C"), fontsize=10, fontweight='bold', color='#0f172a')
        
    elif "ikizkenar" in tip:
        bx, by = 1.0, 1.0
        cx, cy = 5.0, 1.0
        ax_val, ay_val = 3.0, 4.5
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round', solid_joinstyle='round')
        ax.text(ax_val, ay_val + 0.15, etiketler.get("A", "A"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(bx - 0.2, by - 0.15, etiketler.get("B", "B"), fontsize=10, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.15, etiketler.get("C", "C"), fontsize=10, fontweight='bold', color='#0f172a')
        ax.plot([2.0, 1.9], [2.75, 2.95], color='#dc2626', linewidth=2)
        ax.plot([4.0, 4.1], [2.75, 2.95], color='#dc2626', linewidth=2)
        
    elif "paralelkenar" in tip:
        x_coords = [1.2, 4.2, 5.2, 2.2, 1.2]
        y_coords = [3.5, 3.5, 1.2, 1.2, 3.5]
        ax.plot(x_coords, y_coords, color='#0f172a', linewidth=2.2, solid_capstyle='round', solid_joinstyle='round')
        ax.text(1.0, 3.7, etiketler.get("A", "A"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(4.3, 3.7, etiketler.get("B", "B"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(5.4, 1.0, etiketler.get("C", "C"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(2.0, 1.0, etiketler.get("D", "D"), fontsize=11, fontweight='bold', color='#0f172a')
        
    elif "yamuk" in tip:
        x_coords = [1.8, 4.2, 5.2, 0.8, 1.8]
        y_coords = [3.5, 3.5, 1.2, 1.2, 3.5]
        ax.plot(x_coords, y_coords, color='#0f172a', linewidth=2.2, solid_capstyle='round', solid_joinstyle='round')
        ax.text(1.6, 3.7, etiketler.get("A", "A"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(4.3, 3.7, etiketler.get("B", "B"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(5.4, 1.0, etiketler.get("C", "C"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(0.6, 1.0, etiketler.get("D", "D"), fontsize=11, fontweight='bold', color='#0f172a')
        
    elif "cember" in tip or "daire" in tip:
        circle = plt.Circle((3, 2.5), 1.8, color='#0f172a', fill=False, linewidth=2.2)
        ax.add_patch(circle)
        ax.plot([3, 4.8], [2.5, 2.5], color='#0f172a', linewidth=1.8)
        ax.text(3.9, 2.7, etiketler.get("r", "r"), fontsize=10, fontweight='bold', color='#0f172a')
        ax.text(3, 2.5, etiketler.get("M", "M"), fontsize=10, fontweight='bold', ha='center', va='center', color='#0f172a')
        
    else:
        bx, by = 1.0, 1.0
        cx, cy = 5.0, 1.0
        ax_val, ay_val = 3.2, 4.2
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round', solid_joinstyle='round')
        ax.text(ax_val, ay_val + 0.15, etiketler.get("A", "A"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(bx - 0.2, by - 0.15, etiketler.get("B", "B"), fontsize=10, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.15, etiketler.get("C", "C"), fontsize=10, fontweight='bold', color='#0f172a')

    ax.set_xlim(0, 6)
    ax.set_ylim(0, 5.0)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=180, transparent=True)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_str}"

# --- MEB MÜFREDATI VE ÖZEL MODÜLLER ---
MUGREDAT = {
    "4. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümle Bilgisi", "Paragraf Yorumlama", "Yazım Kuralları ve Noktalama", "Metin Türleri ve Söz Sanatları"],
        "Matematik": ["Doğal Sayılar ve İşlemler", "Geometrik Şekiller ve Cisimler", "Kesirler", "Zaman Ölçme", "Veri Toplama ve Değerlendirme"],
        "Fen Bilimleri": ["Yer Kabuğu ve Dünyamız", "Besinlerimiz", "Kuvvetin Etkileri", "Maddenin Özellikleri", "Aydınlatma ve Ses Teknolojileri"],
        "Sosyal Bilgiler": ["Birey ve Toplum", "Kültür ve Miras", "İnsanlar ve Yerler", "Üretim, Dağıtım ve Tüketim", "Etkin Vatandaşlık"],
        "Din Kültürü": ["Dinimiz Hayatımız", "İslam'ın İnanç Esasları", "Hz. Muhammed'i Tanıyalım", "Ahlaki Değerler"],
        "İngilizce": ["Classroom Rules", "Nationality", "Cartoon Characters", "Free Time", "My Day", "Body Parts"]
    },
    "5. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Metin Yorumlama ve Paragraf", "Yazım Kuralları", "Noktalama İşaretleri"],
        "Matematik": ["Doğal Sayılarla İşlemler", "Kesirler", "Ondalık Gösterimler", "Yüzdeler", "Üçgen ve Dörtgenler", "Veri İşleme", "Çember ve Daire", "Açı çeşitleri ve Dörtgende Açılar", "Temel Geometrik Kavramlar ve Doğrular"],
        "Fen Bilimleri": ["Güneş, Dünya ve Ay", "Canlılar Dünyası", "Kuvvetin Uygulanması ve Sürtünme", "Maddenin Hâl Değişimi ve Isı", "Kuvveti Tanıyalım", "Işığın Yayılması"],
        "Sosyal Bilgiler": ["Birey ve Toplum", "Kültür ve Miras", "İnsanlar, Yerler ve Çevre", "Bilim, Teknoloji ve Toplum", "Üretim, Dağıtım ve Tüketim"],
        "Din Kültürü": ["Allah İnancı ve İnsan", "Hz. Muhammed ve Aile Hayatı", "İslam'ın Temel İbadetleri", "Ahlaki Değerler"],
        "İngilizce": ["Hello!", "My Town", "Games and Hobbies", "My Daily Routine", "Health", "Movies"],
        "Almanca": ["Hallo!", "Sich vorstellen", "Zahlen und Farben", "Familie und Freunde", "Schulsachen"]
    },
    "6. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragraf Bilgisi", "Metin Türleri", "Fiiller"],
        "Matematik": ["Çarpanlar ve Katlar", "Kümeler", "Tam Sayılar", "Kesirlerle İşlemler", "Cebirsel İfadeler", "Açılar", "Üçgende Açılar ve Alan", "Çember ve Daire", "Dörtgende Çevre og Alan"],
        "Fen Bilimleri": ["Güneş Sistemi ve Tutulmalar", "Vücudumuzdaki Sistemler", "Kuvvet ve Hareket", "Madde ve Isı", "Ses ve Özellikleri"],
        "Sosyal Bilgiler": ["Biz ve Toplum", "Yeryüzünde Yaşam", "Türklerin Tarihsel Yolculuk", "Ussal Ekonomi", "Yönetimimiz ve Demokrasi"],
        "Din Kültürü": ["Peygamber ve İlahi Kitaplar", "Namaz İbadeti", "Hz. Muhammed'in Hayatı", "Ahlaki Tutum ve Davranışlar"],
        "İngilizce": ["Life", "Yummy Breakfast", "Downtown", "Weather and Emotions", "At the Fair", "Vacations"],
        "Almanca": ["Guten Tag!", "Hobbys", "Tagesablauf", "Essen und Trinken", "Wohnen"]
    },
    "7. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Cümlenin Ögeleri", "Fiilimsiler", "Anlatım Bozuklukları"],
        "Matematik": ["Tam Sayılarla İşlemler", "Rasyonel Sayılar", "Cebirsel İfadeler", "Eşitlik ve Denklem", "Oran ve Orantı", "Açılar ve Çokgenler", "Üçgende Açılar", "Çemberde Açı ve Alan", "Dörtgenler ve Çevre"],
        "Fen Bilimleri": ["Güneş Sistemi ve Ötesi", "Hücre ve Bölünmeler", "Kuvvet ve Enerji", "Saf Madde ve Karışımlar", "Işığın Soğurulması"],
        "Sosyal Bilgiler": ["Birlikte Yaşamak", "Ülkemizde Nüfus", "Tarihte Yolculuk", "Ekonomi ve Sosyal Hayat", "Yaşayan Demokrasi"],
        "Din Kültürü": ["Melek ve Ahiret İnancı", "Hac ve Kurban", "Ahlaki Davranışlar", "İslam Düşüncesinde Yorumlar"],
        "İngilizce": ["Appearance and Personality", "Sports", "Biographies", "Wild Animals", "Television", "Celebrations"],
        "Almanca": ["Mein Körper und Gesundheit", "Kleidung", "Wetter und Jahreszeiten", "Freizeitaktivitäten"]
    },
    "8. Sınıf": {
        "Türkçe": ["Fiilimsiler", "Cümlenin Ögeleri", "Cümle Türleri", "Yazım Kuralları", "Sözel Mantık ve Muhakeme", "Paragraf Analizi"],
        "Matematik": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Basit Olayların Olma Olasılığı", "Doğrusal Denklemler", "Üçgenler ve Üçgende Açılar", "Çember ve Daire", "Dörtgenler ve Çevre Bağıntıları"],
        "Fen Bilimleri": ["Mevsimlerin Oluşumu ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler", "Enerji Dönüşümleri"],
        "Sosyal Bilgiler": ["Bir Demokrasi Kahramanı: Atatürk", "Milli Uyanış", "Ya İstiklal Ya Ölüm", "Atatürkçülük ve Çağdaşlaşan Türkiye"],
        "Din Kültürü": ["Kader İnancı", "Zekat ve Sadaka", "Din ve Hayat", "Hz. Muhammed'in Örnekliği"],
        "İngilizce": ["Friendship", "Teen Life", "In the Kitchen", "On the Phone", "The Internet", "Adventures"],
        "Almanca": ["Reisen und Urlaub", "Berufe", "Technologie", "Umwelt und Natur"]
    },
    "Genel Yetenek & Aktiviteler": {
        "Bilgi Yarışması": ["Genel Kültür ve Tarih", "Dünya Coğrafyası", "Bilim ve Sanat", "Doğa ve Uzay", "Eğlenceli Trivia"],
        "Zihinden Dört İşlem": ["Hızlı Toplama ve Çıkarma", "Çarpım Tablosu Hakimiyeti", "Kademeli Zincir İşlemler", "Zihinden Bölme ve Kat Problemleri"]
    },
    "LGS Hazırlık": {
        "Türkçe": ["Sözel Mantık ve Muhakeme", "Paragraf Analizi", "Dil Bilgisi Karma Denemeleri"],
        "Matematik": ["LGS Pro Matematik Karma", "Yeni Nesil Beceri Temelli Sorular", "Geometri ve Üçgende Açılar Denemeleri", "Çember, Daire ve Çevre Problemleri"],
        "Fen Bilimleri": ["LGS Fen Bilimleri Kapsamlı Karma Denemeler", "Mevsimler, DNA ve Basınç Tekrarı"],
        "Sosyal Bilgiler": ["T.C. İnkılap Tarihi ve Atatürkçülük Karma Tekrar"],
        "Din Kültürü": ["LGS Din Kültürü Karma Denemeleri ve Yorum Soruları"],
        "İngilizce": ["LGS İngilizce Vocabulary & Reading Comprehension Testleri"],
        "Almanca": ["LGS Almanca Kelime ve Paragraf Soruları"]
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

class APIKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.current_index = 0

    def get_next_key(self):
        if not self.keys:
            return None
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key

api_manager = APIKeyManager(API_KEYS)

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

# --- SESSION STATE TANIMLARI ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
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

# --- KENAR ÇUBUĞU ---
with st.sidebar:
    st.markdown("### 🔮 Sınav Fabrikası Soru Paneli")
    st.markdown("---")

    if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
        st.warning("⚠️ `.streamlit/secrets.toml` dosyasına geçerli Gemini API anahtarınızı ekleyin.")

    secili_sinif = st.selectbox("Eğitim Seviyesi / Kategori:", list(MUGREDAT.keys()))
    sinav_turu = st.selectbox("Sınav Türü:", [
        "Konu Tarama Soruları",
        "Yeni Nesil ve Karma Soru Çeşitleri",
        "Genel Değerlendirme Soruları",
        "LGS Hazırlık Soruları",
        "Yanlışlardan Üretilen Sorular"
    ])

    zorluk_seviyesi = st.selectbox("🎯 Soru Zorluk Seviyesi:", ["Kolay", "Orta", "Zor", "Karma / Dengeli"])

    st.markdown("---")
    st.markdown("📚 **Dersler ve Üniteler**")

    mevcut_dersler = MUGREDAT.get(secili_sinif, {})
    secili_ders_unite_haritasi = {}

    for ders_adi, uniteler_listesi in mevcut_dersler.items():
        with st.expander(f"📘 {ders_adi}"):
            ders_secildi = st.checkbox(f"Tüm {ders_adi} Kategorisini Dahil Et", key=f"chk_ders_{secili_sinif}_{ders_adi}")
            secili_alt_uniteler = []
            for unite in uniteler_listesi:
                if st.checkbox(unite, key=f"chk_unite_{secili_sinif}_{ders_adi}_{unite}"):
                    secili_alt_uniteler.append(unite)
            
            if ders_secildi or secili_alt_uniteler:
                secili_ders_unite_haritasi[ders_adi] = secili_alt_uniteler if secili_alt_uniteler else uniteler_listesi

    st.markdown("---")
    soru_sayisi = st.slider("🔢 Soru Sayısı:", 1, 100, 3)

    if st.button("🚀 Soru Üretimini Başlat", use_container_width=True, type="primary"):
        if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
            st.error("Geçerli bir API anahtarı bulunamadı!")
        elif not secili_ders_unite_haritasi:
            st.error("Lütfen en az bir ders veya ünite seçiniz!")
        else:
            ek_baglam = ""
            if sinav_turu == "Yanlışlardan Üretilen Sorular":
                ilgili_yanlislar = [y for y in st.session_state.yanlis_sorular_arsivi if y['ders'] in secili_ders_unite_haritasi.keys()]
                if ilgili_yanlislar:
                    ek_baglam = "Öğrencinin geçmişte hata yaptığı benzer soru örnekleri üzerinden benzer nitelikte sorular üret.\n"

            ders_unite_detay = ""
            aktif_dersler_listesi = list(secili_ders_unite_haritasi.keys())
            for d, u_list in secili_ders_unite_haritasi.items():
                ders_unite_detay += f"- Ders/Kategori: {d}, İstenen Alt Başlıklar: {', '.join(u_list)}\n"

            prompt = f"""
Sen MEB müfredatına ve zeka/bilgi yarışması formatlarına tam hakim profesyonel bir soru hazırlama yapay zekasısın.
{secili_sinif} seviyesinde, {sinav_turu} kapsamında, TOPLAM {soru_sayisi} adet son derece nitelikli, özgün, birbirini tekrar etmeyen ve değişken senaryolara sahip çoktan seçmeli soru üret. 

ÖZEL TALİMATLAR:
- Eğer seçilen kategori "Bilgi Yarışması" ise; genel kültür, tarih, sanat veya bilim odaklı, şaşırtıcı ve eğlenceli trivia soruları hazırla.
- Eğer seçilen kategori "Zihinden Dört İşlem" ise; zihinden hızlıca yapılabilecek, pratik kural gerektiren veya kademeli işlem becerisini ölçen sayısal sorular üret (geometri_tipi='yok' olsun).
- Metin içerisindeki derece ifadeleri için LaTeX komutu (`\\circ`) yerine doğrudan derece sembolü (°) kullan (Örn: 70°).

ÇOK ÖNEMLİ - GEOMETRİ VE ŞEKİL KİMLİĞİ KURALLARI:
1. Sorularda paralelkenar, yamuk gibi dörtgen türleri seçildiğinde `geometri_tipi` alanını kesinlikle uygun değere (`paralelkenar`, `yamuk` vb.) ayarla.
2. Soru metninde geçen köşe harfleri (örn. A, B, C, D) şemadaki köşe etiketleriyle (`etiketler` sözlüğü) tam olarak örtüşmelidir.
3. Geometri dışı sorularda `geometri_tipi` değerini "yok" yap.

Zorluk Seviyesi: {zorluk_seviyesi}
Seçilen Alanlar ve Alt Başlıklar:
{ders_unite_detay}
{ek_baglam}

Yanıtı kesinlikle ve sadece şu JSON formatında ver (başka hiçbir markdown veya metin ekleme, doğrudan saf JSON dizisi döndür):
[
  {{
    "soru_metni": "Soru metni...",
    "secenekler": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "dogru_cevap": "A",
    "cozum_aciklamasi": "Çözüm açıklaması...",
    "ders": "Kategori/Ders Adı",
    "geometri_tipi": "paralelkenar", 
    "etiketler": {{"A": "A", "B": "B", "C": "C", "D": "D"}}
  }}
]
"""
            class WorkerContext:
                def __init__(self):
                    self.quiz_data = []
                    self.basarili = False
                    self.hata_mesaji = None
                    self.api_tamamlandi = False

            ctx = WorkerContext()
            tahmini_sure_sn = int((soru_sayisi * 1.5) + 5)
            
            progress_bar = st.progress(0.0)
            status_placeholder = st.empty()
            
            baslangic_zamani = time.time()
            current_key = api_manager.get_next_key()
            
            def api_cagirici():
                try:
                    client = genai.Client(api_key=current_key)
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.85,
                            response_mime_type="application/json"
                        )
                    )
                    if response and response.text:
                        parsed = kararli_json_ayikla(response.text)
                        if parsed:
                            ctx.quiz_data = parsed
                            for idx, item in enumerate(ctx.quiz_data):
                                item["soru_no"] = idx + 1
                                if "ders" not in item:
                                    item["ders"] = aktif_dersler_listesi[0]
                                if "geometri_tipi" not in item:
                                    item["geometri_tipi"] = "yok"
                                if "etiketler" not in item:
                                    item["etiketler"] = {}
                            ctx.basarili = True
                except Exception as e:
                    ctx.hata_mesaji = str(e)
                finally:
                    ctx.api_tamamlandi = True

            t = threading.Thread(target=api_cagirici)
            t.start()

            while not ctx.api_tamamlandi:
                gecen_sure = time.time() - baslangic_zamani
                kalan_tahmin = max(0, tahmini_sure_sn - int(gecen_sure))
                
                oran = min(0.95, gecen_sure / tahmini_sure_sn)
                progress_bar.progress(oran)
                status_placeholder.markdown(f"⏳ **Sorular üretiliyor...** Tahmini kalan süre: **{kalan_tahmin} saniye** (Soru Sayısı: {soru_sayisi})")
                time.sleep(0.1)

            t.join()

            progress_bar.progress(1.0)
            status_placeholder.empty()

            if ctx.basarili and ctx.quiz_data:
                st.session_state.quiz_data = ctx.quiz_data
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.exam_started = False
                st.session_state.start_time = None
                st.session_state.total_duration = None
                st.session_state.current_question = 0
                st.success(f"{len(ctx.quiz_data)} adet soru başarıyla üretildi!")
                st.rerun()
            else:
                st.error(f"Hata oluştu: {ctx.hata_mesaji or 'Geçerli veri alınamadı.'}")

    if st.session_state.performance_history:
        st.markdown("---")
        with st.expander("📈 Geçmiş Sınav Karne Arşivi"):
            for i, p in enumerate(st.session_state.performance_history[::-1]):
                st.markdown(f"**Sınav #{len(st.session_state.performance_history)-i}** ({p['tarih']})")
                st.markdown(f"Seviye: {p['sinif']} | D: {p['dogru']} | ❌ Y: {p['yanlis']} | ⏱️ {p['sure']}")
                st.markdown("---")

# --- ANA İÇERİK EKRANI ---
st.title("🎓 Soru Fabrikası & Tablet Sınav Modülü")
st.markdown("---")

if st.session_state.quiz_data is None:
    st.info("Sol panelden kategori/ders ve ünite seçimlerinizi yapıp **'Soru Üretimini Başlat'** butonuna tıklayarak sınavınızı oluşturun.")

elif not st.session_state.exam_started:
    toplam_soru_sayisi = len(st.session_state.quiz_data)
    toplam_sure_sn = toplam_soru_sayisi * 80
    dakika_gosterim = toplam_sure_sn // 60

    st.markdown(f"""
    <div class="custom-card">
        <h2>✨ Zenginleştirilmiş Sınavınız Hazır!</h2>
        <p style="color: #64748b; font-size: 16px;">Üretilen Soru Sayısı: <b>{toplam_soru_sayisi}</b> | Süre: <b>{dakika_gosterim} Dakika</b></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Sınavı Şimdi Başlat", use_container_width=True, type="primary"):
            st.session_state.exam_started = True
            st.session_state.start_time = time.time()
            st.rerun()

elif not st.session_state.quiz_submitted:
    quiz_data = st.session_state.quiz_data
    toplam_soru = len(quiz_data)
    curr_idx = st.session_state.current_question

    toplam_izin_verilen_sure = toplam_soru * 80
    gecen_sn = int(time.time() - st.session_state.start_time)
    kalan_sn = toplam_izin_verilen_sure - gecen_sn

    if kalan_sn <= 0:
        st.session_state.quiz_submitted = True
        st.session_state.total_duration = f"{toplam_izin_verilen_sure // 60:02d}:00"
        st.rerun()

    kalan_dakika = kalan_sn // 60
    kalan_saniye = kalan_sn % 60

    col_time, col_progress = st.columns([1, 3])
    with col_time:
        st.metric(label="⏳ Kalan Süre", value=f"{kalan_dakika:02d}:{kalan_saniye:02d}")
    with col_progress:
        st.write(f"**Soru {curr_idx + 1} / {toplam_soru}**")
        st.progress((curr_idx + 1) / toplam_soru)

    st.markdown("<br>", unsafe_allow_html=True)

    q = quiz_data[curr_idx]
    
    with st.container(border=True):
        st.markdown(f"### Soru {curr_idx + 1} &nbsp;&nbsp;|&nbsp;&nbsp; *{q.get('ders', 'Genel')}*")
        st.markdown("<br>", unsafe_allow_html=True)
        
        soru_metni_str = temizle_latex_metin(q.get("soru_metni", ""))
        st.markdown(f'<div class="soru-metni-kutusu">{soru_metni_str}</div>', unsafe_allow_html=True)
        
        geometri_tipi = q.get("geometri_tipi", "yok")
        etiketler = q.get("etiketler", {})
        
        if geometri_tipi and geometri_tipi.lower() != "yok":
            img_data_uri = ciz_vektorel_geometri(geometri_tipi=geometri_tipi, etiketler=etiketler)
            st.markdown(f'''
                <div class="gorsel-sema-kutusu">
                    <img src="{img_data_uri}" style="max-width: 65%; height: auto;" />
                </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        secenekler = q.get("secenekler", {})
        keys_list = sorted(secenekler.keys())
        options_list = [f"{k}) {temizle_latex_metin(secenekler[k])}" for k in keys_list]

        widget_key = f"radio_q_{curr_idx}"

        # Kullanıcının bu soruya daha önce verdiği cevabı hafızadan bul
        kayitli_harf = st.session_state.user_answers.get(curr_idx, None)
        default_opt_index = None
        if kayitli_harf:
            for idx_opt, opt in enumerate(options_list):
                if opt.startswith(kayitli_harf + ")"):
                    default_opt_index = idx_opt
                    break

        # Her soru değişiminde Streamlit state widget çakışmasını önlemek için anlık indexi ayarlıyoruz
        if widget_key not in st.session_state:
            st.session_state[widget_key] = options_list[default_opt_index] if default_opt_index is not None else None

        def handle_radio_change():
            val = st.session_state.get(widget_key)
            if val:
                harf = val.split(")")[0].strip()
                st.session_state.user_answers[curr_idx] = harf
            else:
                if curr_idx in st.session_state.user_answers:
                    del st.session_state.user_answers[curr_idx]

        secim = st.radio(
            label="Cevabınızı seçin:",
            options=options_list,
            index=default_opt_index,
            key=widget_key,
            on_change=handle_radio_change
        )

        if secim:
            harf = secim.split(")")[0].strip()
            st.session_state.user_answers[curr_idx] = harf

    with st.expander("✍️ Çözüm / Karalama Tahtası (Aç / Kapat)"):
        col1, col2 = st.columns([2, 1])
        with col1:
            pen_color = st.color_picker("Kalem Rengi", "#f97316", key=f"color_q_{curr_idx}")
        with col2:
            pen_width = st.slider("Kalem Kalınlığı", 1, 15, 3, key=f"width_q_{curr_idx}")

        st_canvas(
            fill_color="rgba(249, 115, 22, 0.3)",
            stroke_width=pen_width,
            stroke_color=pen_color,
            background_color="#FFFFFF",
            height=220,
            width=700,
            drawing_mode="freedraw",
            key=f"canvas_q_{curr_idx}",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_prev, col_spacer, col_next = st.columns([1, 2, 1])

    with col_prev:
        if st.button("⬅️ Önceki Soru", disabled=(curr_idx == 0), use_container_width=True):
            st.session_state.current_question -= 1
            st.rerun()

    with col_next:
        if curr_idx < toplam_soru - 1:
            if st.button("Sonraki Soru ➡️", use_container_width=True):
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("📊 Sınavı Tamamla", type="primary", use_container_width=True):
                gecen = int(time.time() - st.session_state.start_time)
                st.session_state.total_duration = f"{gecen // 60:02d}:{gecen % 60:02d}"
                st.session_state.quiz_submitted = True
                
                d_say = 0
                y_say = 0
                b_say = 0
                for idx_q, q_item in enumerate(quiz_data):
                    dogru_c = q_item.get("dogru_cevap")
                    ogrenci_c = st.session_state.user_answers.get(idx_q)
                    if not ogrenci_c:
                        b_say += 1
                    elif ogrenci_c == dogru_c:
                        d_say += 1
                    else:
                        y_say += 1
                        st.session_state.yanlis_sorular_arsivi.append({
                            "soru_metni": q_item.get("soru_metni"),
                            "cozum": q_item.get("cozum_aciklamasi"),
                            "ders": q_item.get("ders")
                        })
                
                yeni_kayit = {
                    "tarih": datetime.now().strftime("%d-%m-%Y %H:%M"),
                    "sinif": secili_sinif,
                    "dersler": "Seçilen Alanlar",
                    "dogru": d_say,
                    "yanlis": y_say,
                    "bos": b_say,
                    "sure": st.session_state.total_duration
                }
                st.session_state.performance_history.append(yeni_kayit)
                st.rerun()

else:
    quiz_data = st.session_state.quiz_data
    dogru_sayisi = 0
    yanlis_sayisi = 0
    bos_sayisi = 0

    for idx, q in enumerate(quiz_data):
        dogru = q.get("dogru_cevap")
        ogrenci = st.session_state.user_answers.get(idx)
        if not ogrenci:
            bos_sayisi += 1
        elif ogrenci == dogru:
            dogru_sayisi += 1
        else:
            yanlis_sayisi += 1

    st.balloons()
    st.subheader("🎯 Sınav Sonuç Karnesi")
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Doğru", dogru_sayisi)
    c2.metric("❌ Yanlış", yanlis_sayisi)
    c3.metric("⚪ Boş", bos_sayisi)
    c4.metric("⏱️ Süre", st.session_state.total_duration or "00:00")

    st.markdown("---")
    st.markdown("### 📋 Soru Detayları ve Çözümler")

    for idx, q in enumerate(quiz_data):
        dogru = q.get("dogru_cevap")
        ogrenci = st.session_state.user_answers.get(idx, "Boş")

        renk = "🟢" if ogrenci == dogru else ("⚪" if ogrenci == "Boş" else "🔴")
        with st.container(border=True):
            with st.expander(f"{renk} Soru {idx + 1} | Senin Cevabın: **{ogrenci}** — Doğru Cevap: **{dogru}**"):
                soru_m = temizle_latex_metin(q.get("soru_metni", ""))
                st.write(soru_m)
                
                g_tip = q.get("geometri_tipi", "yok")
                g_etiket = q.get("etiketler", {})
                if g_tip and g_tip.lower() != "yok":
                    img_data_uri = ciz_vektorel_geometri(geometri_tipi=g_tip, etiketler=g_etiket)
                    st.markdown(f'''
                        <div class="gorsel-sema-kutusu">
                            <img src="{img_data_uri}" style="max-width: 65%; height: auto;" />
                        </div>
                    ''', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"**Doğru Cevap Seçenek:** `{dogru}`")
                st.markdown(f"**Çözüm Açıklaması:** {temizle_latex_metin(q.get('cozum_aciklamasi', 'Açıklama bulunmuyor.'))}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_yeniden1, col_yeniden2, col_yeniden3 = st.columns([1, 2, 1])
    with col_yeniden2:
        if st.button("🔄 Yeni Sınav Oluştur / Başa Dön", use_container_width=True, type="primary"):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.exam_started = False
            st.session_state.start_time = None
            st.session_state.total_duration = None
            st.session_state.current_question = 0
            st.rerun()
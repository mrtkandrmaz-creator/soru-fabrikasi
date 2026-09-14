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
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import threading
import numpy as np

# --- RENDER / SAYFA AYARI ---
st.set_page_config(
    page_title="Soru Fabrikası Tablet Sınav Modülü",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN VE STABİL ÖZEL CSS (HTML BASMA RİSKİNİ ORTADAN KALDIRAN YAPI) ---
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
    .ders-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
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
        max-width: 480px;
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

# --- GELİŞMİŞ FEN VE MATEMATİK GÖRSEL ÇİZİCİ ---
def ciz_vektorel_gorsel(gorsel_tipi="yok", etiketler=None):
    if not isinstance(etiketler, dict):
        etiketler = {}
        
    fig, ax = plt.subplots(figsize=(4.5, 3.3))
    ax.set_aspect('equal')
    ax.axis('off')
    
    tip = str(gorsel_tipi).lower()
    
    if "gunes_dunya_ay" in tip or "astronomi" in tip:
        sun = plt.Circle((1.0, 2.5), 0.7, color='#f59e0b', ec='#d97706', linewidth=2)
        ax.add_patch(sun)
        ax.text(1.0, 2.5, etiketler.get("G", "GÜNEŞ"), fontsize=8, fontweight='bold', ha='center', va='center', color='#ffffff')
        
        earth = plt.Circle((3.0, 2.5), 0.45, color='#38bdf8', ec='#0284c7', linewidth=2)
        ax.add_patch(earth)
        ax.text(3.0, 2.5, etiketler.get("D", "DÜNYA"), fontsize=7, fontweight='bold', ha='center', va='center', color='#0f172a')
        
        moon = plt.Circle((4.1, 3.2), 0.2, color='#cbd5e1', ec='#64748b', linewidth=1.5)
        ax.add_patch(moon)
        ax.text(4.1, 3.2, etiketler.get("A", "AY"), fontsize=6, fontweight='bold', ha='center', va='center', color='#1e293b')
        
        theta = np.linspace(0, 2*np.pi, 100)
        ax.plot(3.0 + 1.1*np.cos(theta), 2.5 + 0.7*np.sin(theta), color='#94a3b8', linestyle='--', linewidth=1)
        ax.text(3.0, 3.4, etiketler.get("O", "Ay'ın Yörüngesi"), fontsize=8, color='#64748b', ha='center')

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
        ax.text(3.0, 0.85, etiketler.get("Y", "Yük (G)"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')
        ax.text(3.6, 2.8, etiketler.get("N", "N"), fontsize=10, fontweight='bold', color='#dc2626')

    elif "dunya_katmanlari" in tip:
        k_dis = plt.Circle((3.0, 2.5), 1.9, color='#38bdf8', alpha=0.4, ec='#0284c7', linewidth=2)
        k_manto = plt.Circle((3.0, 2.5), 1.3, color='#f97316', alpha=0.6, ec='#c2410c', linewidth=2)
        k_cekirdek = plt.Circle((3.0, 2.5), 0.6, color='#dc2626', ec='#991b1b', linewidth=2)
        ax.add_patch(k_dis)
        ax.add_patch(k_manto)
        ax.add_patch(k_cekirdek)
        ax.text(3.0, 4.0, etiketler.get("K1", "Hava Küre (Atmosfer)"), fontsize=8, fontweight='bold', ha='center', color='#0369a1')
        ax.text(3.0, 2.5, etiketler.get("K2", "Çekirdek"), fontsize=8, fontweight='bold', ha='center', color='#ffffff')

    elif "cember" in tip or "daire" in tip:
        cember = plt.Circle((3.0, 2.5), 1.6, color='#0f172a', fill=False, linewidth=2.2)
        ax.add_patch(cember)
        
        ax.plot(3.0, 2.5, 'ko', markersize=5)
        ax.text(3.1, 2.65, etiketler.get("M", "M"), fontsize=10, fontweight='bold', color='#0f172a')
        
        ax.plot([3.0, 4.6], [2.5, 2.5], color='#dc2626', linewidth=1.8, linestyle='--')
        ax.text(3.8, 2.7, etiketler.get("r", "r"), fontsize=10, fontweight='bold', color='#dc2626')
        
        ax.text(3.0, 0.4, etiketler.get("Aciklama", "Çember ve Daire Geometrisi"), fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "isitma_kababi" in tip or "hal_degisimi" in tip:
        ax.plot([2.0, 2.0, 4.0, 4.0], [1.0, 3.5, 3.5, 1.0], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        rect = plt.Rectangle((2.05, 1.05), 1.9, 1.6, color='#38bdf8', alpha=0.5)
        ax.add_patch(rect)
        ax.plot([3.0, 3.0], [1.2, 4.3], color='#dc2626', linewidth=2.5)
        circle_term = plt.Circle((3.0, 1.2), 0.16, color='#dc2626', fill=True)
        ax.add_patch(circle_term)
        rect_ocak = plt.Rectangle((1.5, 0.6), 3.0, 0.3, color='#475569', ec='#0f172a', linewidth=1.5)
        ax.add_patch(rect_ocak)
        ax.text(3.3, 3.9, etiketler.get("T", "Termometre"), fontsize=9, fontweight='bold', color='#dc2626')
        ax.text(2.2, 1.9, etiketler.get("S", "Sıvı"), fontsize=9, fontweight='bold', color='#0369a1')
        ax.text(3.0, 0.3, etiketler.get("K", "Isıtıcı Kaynak"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')

    elif "basinc" in tip:
        rect_blok = plt.Rectangle((1.5, 2.0), 3.0, 1.2, color='#cbd5e1', ec='#0f172a', linewidth=2)
        ax.add_patch(rect_blok)
        ax.arrow(3.0, 4.0, 0.0, -0.8, head_width=0.3, head_length=0.2, fc='#dc2626', ec='#dc2626')
        ax.text(3.0, 4.25, etiketler.get("F", "Kuvvet (F)"), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(3.0, 2.6, etiketler.get("G", "Ağırlık (G)"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(3.0, 1.4, etiketler.get("S", "Yüzey Alanı (S)"), fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "devre" in tip or "elektrik" in tip:
        ax.plot([1.2, 4.8, 4.8, 1.2, 1.2], [1.5, 1.5, 3.6, 3.6, 1.5], color='#0f172a', linewidth=2, linestyle='--')
        circle_ampul = plt.Circle((3.0, 3.6), 0.38, color='#f59e0b', fill=True, ec='#0f172a', linewidth=2)
        ax.add_patch(circle_ampul)
        ax.text(3.0, 3.6, etiketler.get("A", "💡"), fontsize=12, ha='center', va='center')
        ax.text(3.0, 1.15, etiketler.get("P", "Güç Kaynağı / Pil"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')

    elif "dik_ucgen" in tip:
        bx, by = 1.0, 1.0
        cx, cy = 5.0, 1.0
        ax_val, ay_val = 1.0, 4.2
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        ax.plot([1.0, 1.4, 1.4, 1.0], [1.0, 1.0, 1.4, 1.4], color='#0f172a', linewidth=1.5)
        ax.text(ax_val - 0.2, ay_val + 0.15, etiketler.get("A", "A"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(bx - 0.2, by - 0.2, etiketler.get("B", "B"), fontsize=10, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.2, etiketler.get("C", "C"), fontsize=10, fontweight='bold', color='#0f172a')
        
    else:
        circle_def = plt.Circle((3, 2.5), 1.5, color='#0f172a', fill=False, linewidth=2.2)
        ax.add_patch(circle_def)
        ax.text(3, 2.5, etiketler.get("Genel", "Soru Şeması"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')

    ax.set_xlim(0, 6)
    ax.set_ylim(0, 5.0)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=180, transparent=True)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_str}"

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
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Cümlenin Ögeleri", "Fiilimsiler", "Anlatım Bozuklukları"],
        "Matematik": ["Tam Sayılarla İşlemler", "Rasyonel Sayılar", "Cebirsel İfadeler", "Eşitlik ve Denklem", "Oran ve Orantı", "Açılar ve Çokgenler", "Üçgende Açılar", "Çemberde Açı ve Alan", "Dörtgenler ve Çevre"],
        "Fen Bilimleri": ["Güneş Sistemi ve Ötesi", "Hücre ve Bölünmeler", "Kuvvet ve Enerji", "Saf Madde ve Karışımlar", "Işığın Soğurulması"],
        "Sosyal Bilgiler": ["Birlikte Yaşamak", "Ülkemizde Nüfus", "Tarihte Yolculuk", "Ekonomi ve Sosyal Hayat", "Yaşayan Demokrasi"],
        "Din Kültürü": ["Melek ve Ahiret İnancı", "Hac ve Kurban", "Ahlaki Davranışlar", "İslam Düşüncesinde Yorumlar"],
        "İngilizce": ["Appearance and Personality", "Sports", "Biographies", "Wild Animals", "Television", "Celebrations"],
        "Almanca": ["Reisen und Urlaub", "Berufe", "Technologie", "Umwelt und Natur", "Feste und Traditionen"]
    },
    "8. Sınıf": {
        "Türkçe": ["Fiilimsiler", "Cümlenin Ögeleri", "Cümle Türleri", "Yazım Kuralları", "Sözel Mantık ve Muhakeme", "Paragraf Analizi"],
        "Matematik": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Basit Olayların Olma Olasılığı", "Doğrusal Denklemler", "Üçgenler ve Üçgende Açılar", "Çember ve Daire", "Dörtgenler ve Çevre Bağıntıları"],
        "Fen Bilimleri": ["Mevsimlerin Oluşumu ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler", "Enerji Dönüşümleri"],
        "Sosyal Bilgiler": ["Bir Demokrasi Kahramanı: Atatürk", "Milli Uyanış", "Ya İstiklal Ya Ölüm", "Atatürkçülük ve Çağdaşlaşan Türkiye"],
        "Din Kültürü": ["Kader İnancı", "Zekat ve Sadaka", "Din ve Hayat", "Hz. Muhammed'in Örnekliği"],
        "İngilizce": ["Friendship", "Teen Life", "In the Kitchen", "On the Phone", "The Internet", "Adventures"],
        "Almanca": ["Kommunikation", "Medien", "Zukunftspläne", "Freizeit und Hobbys"]
    },
    "Genel Yetenek & Aktiviteler": {
        "Bilgi Yarışması": ["Genel Kültür ve Tarih", "Dünya Coğrafyası", "Bilim ve Sanat", "Doğa ve Uzay", "Eğlenceli Trivia"],
        "Zihinden Dört İşlem": ["Hızlı Toplama ve Çıkarma", "Çarpım Tablosu Hakimiyeti", "Kademeli Zincir İşlemler", "Zihinden Bölme ve Kat Problemleri"],
        "Almanca Pratik": ["Temel Kelimeler", "Günlük Diyaloglar", "Grammatik Grundlagen"]
    },
    "LGS Hazırlık": {
        "LGS Çıkmış Sorular": ["MEB LGS Çıkmış Türkçe Soruları", "MEB LGS Çıkmış Matematik Soruları", "MEB LGS Çıkmış Fen Bilimleri Soruları", "MEB LGS Çıkmış T.C. İnkılap Tarihi Soruları", "MEB LGS Çıkmış Din Kültürü Soruları", "MEB LGS Çıkmış İngilizce Soruları", "MEB LGS Çıkmış Almanca Örnek ve Beceri Temelli Sorular"],
        "Türkçe": ["Sözel Mantık ve Muhakeme", "Paragraf Analizi", "Dil Bilgisi Karma Denemeleri"],
        "Matematik": ["LGS Pro Matematik Karma", "Yeni Nesil Beceri Temelli Sorular", "Geometri ve Üçgende Açılar Denemeleri", "Çember, Daire ve Çevre Problemleri"],
        "Fen Bilimleri": ["LGS Fen Bilimleri Kapsamlı Karma Denemeler", "Mevsimler, DNA ve Basınç Tekrarı"],
        "Sosyal Bilgiler": ["T.C. İnkılap Tarihi ve Atatürkçülük Karma Tekrar"],
        "Din Kültürü": ["LGS Din Kültürü Karma Denemeleri ve Yorum Soruları"],
        "İngilizce": ["LGS İngilizce Vocabulary & Reading Comprehension Testleri"],
        "Almanca": ["LGS Almanca Kelime, Cümle Yapısı ve Paragraf Soruları"]
    }
}

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
        "MEB LGS Çıkmış Soru Tarzı / Benzerleri",
        "Yeni Nesil ve Karma Soru Çeşitleri",
        "Genel Değerlendirme Soruları",
        "LGS Hazırlık Soruları",
        "Yanlışlardan Üretilen Sorular"
    ])

    zorluk_seviyesi = st.selectbox("🎯 Soru Zorluk Seviyesi:", ["Kolay", "Orta", "Zor", "Karma / Dengeli"])

    st.markdown("---")
    st.markdown("📚 **Dersler, Üniteler ve LGS Çıkmış Sorular**")

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
    soru_sayisi = st.slider("🔢 Soru Sayısı (Toplam):", 1, 100, 5)

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
            elif "LGS Çıkmış" in sinav_turu or "LGS Çıkmış Sorular" in secili_ders_unite_haritasi.keys():
                ek_baglam = "Bu sorular MEB tarafından LGS'de sorulmuş gerçek çıkmış soru mantığına, soru köklerine ve beceri temelli (mantık-muhakeme) yapıya birebir uygun olmalıdır.\n"

            ders_unite_detay = ""
            aktif_dersler_listesi = list(secili_ders_unite_haritasi.keys())
            for d, u_list in secili_ders_unite_haritasi.items():
                ders_unite_detay += f"- Ders/Kategori: {d}, İstenen Alt Başlıklar/Kapsam: {', '.join(u_list)}\n"

            gorsel_talimati = """
            ÇOK ÖNEMLİ KURAL (SCIENCE VISUAL WIDGET & ÇEMBER GÖRSEL UYUMU):
            Eğer soru ilgili fen ünitesine veya matematik çember konusuna aitse, `gorsel_tipi` alanını tam olarak şu değerlerden biriyle seçmelisin:
            - Güneş, Dünya, Ay ve Uzay sistemleri ile ilgiliyse: `gunes_dunya_ay`
            - Kuvvet, yay, yük ve dinamometre ile ilgiliyse: `dinamometre`
            - Dünya'nın katmanları ile ilgiliyse: `dunya_katmanlari`
            - Matematik çember, daire, yarıçap, merkez açılarla ilgiliyse: `cember`
            - Isı, hal değişimi, kaynama ile ilgiliyse: `isitma_kababi`
            - Basınç ile ilgiliyse: `basinc`
            - Elektrik devreleri ile ilgiliyse: `devre`
            - Geometrik şekiller (dik üçgen vb.) ise: `dik_ucgen`
            - Görsel gerektirmeyen durumlar için: `yok`
            Soru metninde geçen kavram ile `gorsel_tipi` kesinlikle birebir örtüşmelidir!
            """

            prompt = f"""
Sen MEB müfredatına ve LGS sınav sistemine tam hakim profesyonel bir soru hazırlama yapay zekasısın.
{secili_sinif} seviyesinde, {sinav_turu} kapsamında, TOPLAM {soru_sayisi} adet son derece nitelikli, özgün ve birbirini tekrar etmeyen çoktan seçmeli soru üret. 

{gorsel_talimati}

GENEL KURALLAR:
- Derece ifadeleri için LaTeX (`\\circ`) yerine doğrudan derece sembolü (°) kullan.
- Almanca sorular için Almanca dil kurallarına ve kelime dağarcığına tam uygunluk sağla.
- Soruları üretirken seçilen her bir ders için dengeli dağılım yap ve sonuçta her sorunun JSON objesinde ait olduğu `ders` adını açıkça belirt.

Zorluk Seviyesi: {zorluk_seviyesi}
Seçilen Alanlar ve Alt Başlıklar:
{ders_unite_detay}
{ek_baglam}

Yanıtı kesinlikle ve sadece şu JSON formatında ver (başka hiçbir metin ekleme, saf JSON dizisi döndür):
[
  {{
    "soru_metni": "Soru metni...",
    "secenekler": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "dogru_cevap": "A",
    "cozum_aciklamasi": "Çözüm açıklaması...",
    "ders": "Kategori/Ders Adı",
    "gorsel_tipi": "cember", 
    "etiketler": {{"M": "M", "r": "r", "Aciklama": "O Merkezli Çember"}}
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
                            temperature=0.75,
                            response_mime_type="application/json"
                        )
                    )
                    if response and response.text:
                        parsed = kararli_json_ayikla(response.text)
                        if parsed:
                            ctx.quiz_data = parsed
                            for idx, item in enumerate(ctx.quiz_data):
                                if "ders" not in item:
                                    item["ders"] = aktif_dersler_listesi[0]
                                if "gorsel_tipi" not in item:
                                    item["gorsel_tipi"] = "cember" if "Matematik" in str(item.get("ders")) else "yok"
                                if "etiketler" not in item:
                                    item["etiketler"] = {}
                            
                            ctx.quiz_data = sorted(ctx.quiz_data, key=lambda x: str(x.get("ders", "Genel")))
                            
                            for idx, item in enumerate(ctx.quiz_data):
                                item["soru_no"] = idx + 1

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
                status_placeholder.markdown(f"⏳ **Sorular ders ders gruplanarak üretiliyor...** Tahmini kalan süre: **{kalan_tahmin} saniye**")
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
                st.success(f"{len(ctx.quiz_data)} adet ders bazlı gruplanmış soru başarıyla hazırlandı!")
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
    st.info("Sol panelden kategori/ders ve ünite seçimlerinizi yapıp **'Soru Üretimini Başlat'** butonuna tıklayarak sınavınızı oluşturun. Sorularınız otomatik olarak ders ders gruplanacaktır.")

elif not st.session_state.exam_started:
    toplam_soru_sayisi = len(st.session_state.quiz_data)
    toplam_sure_sn = toplam_soru_sayisi * 80
    dakika_gosterim = toplam_sure_sn // 60

    st.markdown(f"""
    <div class="custom-card">
        <h2>✨ Ders Bazlı Gruplanmış Sınavınız Hazır!</h2>
        <p style="color: #64748b; font-size: 16px;">Toplam Soru: <b>{toplam_soru_sayisi}</b> | Önerilen Süre: <b>{dakika_gosterim} Dakika</b></p>
        <p style="color: #334155; font-size: 14px; margin-top: 5px;"><i>Sorular her dersin tüm soruları bitince sıradaki derse geçecek şekilde düzenlenmiştir.</i></p>
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
        st.session_state.total_duration = int(time.time() - st.session_state.start_time)
        st.rerun()

    kalan_dak = kalan_sn // 60
    kalan_saniye = kalan_sn % 60

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.markdown(f"### Soru **{curr_idx + 1}** / {toplam_soru}")
    with c2:
        st.markdown(f"### ⏳ Kalan Süre: :red[{kalan_dak:02d}:{kalan_saniye:02d}]")
    with c3:
        if st.button("Sınavı Bitir", type="secondary"):
            st.session_state.quiz_submitted = True
            st.session_state.total_duration = int(time.time() - st.session_state.start_time)
            st.rerun()

    st.progress((curr_idx + 1) / toplam_soru)
    st.markdown("---")

    q = quiz_data[curr_idx]
    ders_adi = q.get("ders", "Genel")
    
    st.markdown(f"""
    <div class="ders-banner">
        <span>📘 Ders / Kategori: {ders_adi}</span>
        <span>Soru #{curr_idx + 1}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="custom-card">
        <div class="soru-metni-kutusu">{temizle_latex_metin(q.get("soru_metni", ""))}</div>
    </div>
    """, unsafe_allow_html=True)

    gorsel_tipi = q.get("gorsel_tipi", "yok")
    etiketler = q.get("etiketler", {})
    if gorsel_tipi and gorsel_tipi != "yok":
        img_data_uri = ciz_vektorel_gorsel(gorsel_tipi, etiketler)
        st.markdown(f"""
        <div class="gorsel-sema-kutusu">
            <img src="{img_data_uri}" style="max-width: 100%; height: auto; border-radius: 8px;" />
        </div>
        """, unsafe_allow_html=True)

    secenekler = q.get("secenekler", {})
    secenek_anahtarlari = ["A", "B", "C", "D"]
    secenek_listesi = [f"{k}) {temizle_latex_metin(secenekler.get(k, ''))}" for k in secenek_anahtarlari if k in secenekler]

    secilen_cevap = st.session_state.user_answers.get(curr_idx, None)
    secilen_index = None
    if secilen_cevap in secenek_anahtarlari:
        secilen_index = secenek_anahtarlari.index(secilen_cevap)

    verilen_secenek = st.radio(
        "Lütfen cevabınızı seçiniz:",
        secenek_listesi,
        index=secilen_index,
        key=f"radio_soru_{curr_idx}"
    )

    if verilen_secenek:
        secilen_harf = verilen_secenek.split(")")[0].strip()
        st.session_state.user_answers[curr_idx] = secilen_harf

    st.markdown("---")
    
    # 1. ANA NAVİGASYON SATIRI
    col_sol, col_sag = st.columns([1, 1])

    with col_sol:
        if curr_idx > 0:
            if st.button("⬅️ Önceki Soru", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()

    with col_sag:
        if curr_idx < toplam_soru - 1:
            if st.button("Sonraki Soru ➡", use_container_width=True, type="primary"):
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("🏁 Sınavı Tamamla ve Gönder", use_container_width=True, type="primary"):
                st.session_state.quiz_submitted = True
                st.session_state.total_duration = int(time.time() - st.session_state.start_time)
                st.rerun()

    # 2. HIZLI ATLAMA PANELİ (STREAMLIT NATIVE BUTTON GRID - HTML HATASINI KESİN OLARAK ENGELLER)
    st.markdown("<p style='font-size: 15px; font-weight: 700; color: #1e293b; margin-top: 15px; margin-bottom: 5px;'>🗺️ Hızlı Soru Atlama Paneli</p>", unsafe_allow_html=True)
    
    # Soruları sütunlara bölerek kararlı ve şık buton matrisi oluşturalım
    cols_per_row = min(toplam_soru, 10)
    if cols_per_row > 0:
        jump_cols = st.columns(cols_per_row)
        for idx_h in range(toplam_soru):
            col_idx = idx_h % cols_per_row
            q_num = idx_h + 1
            durum_isareti = "✅" if idx_h in st.session_state.user_answers else "⭕"
            buton_etiketi = f"S{q_num} {durum_isareti}"
            
            with jump_cols[col_idx]:
                # Aktif soru için farklı bir stil/buton tetikleyicisi
                if st.button(buton_etiketi, key=f"native_jump_{idx_h}", use_container_width=True):
                    st.session_state.current_question = idx_h
                    st.rerun()

else:
    quiz_data = st.session_state.quiz_data
    user_answers = st.session_state.user_answers

    dogru_sayisi = 0
    yanlis_sayisi = 0
    bos_sayisi = 0

    yeni_yanlislar = []

    for idx, q in enumerate(quiz_data):
        dogru = q.get("dogru_cevap", "").strip().upper()
        verilen = user_answers.get(idx, "").strip().upper()

        if not verilen:
            bos_sayisi += 1
        elif verilen == dogru:
            dogru_sayisi += 1
        else:
            yanlis_sayisi += 1
            yeni_yanlislar.append({
                "ders": q.get("ders", "Genel"),
                "soru_metni": q.get("soru_metni"),
                "dogru_cevap": dogru,
                "verilen_cevap": verilen,
                "cozum_aciklamasi": q.get("cozum_aciklamasi")
            })

    for yn in yeni_yanlislar:
        if yn not in st.session_state.yanlis_sorular_arsivi:
            st.session_state.yanlis_sorular_arsivi.append(yn)

    toplam_puan = int((dogru_sayisi / len(quiz_data)) * 100) if quiz_data else 0

    sure_sn = st.session_state.total_duration or 0
    sure_dk_str = f"{sure_sn // 60} dakika {sure_sn % 60} saniye"

    p_kayit = {
        "tarih": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "sinif": secili_sinif,
        "dogru": dogru_sayisi,
        "yanlis": yanlis_sayisi,
        "bos": bos_sayisi,
        "puan": toplam_puan,
        "sure": sure_dk_str
    }
    if p_kayit not in st.session_state.performance_history:
        st.session_state.performance_history.append(p_kayit)

    st.markdown("---")
    st.markdown("## 📊 Sınav Sonuç ve Karne Değerlendirmesi")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Puan", f"{toplam_puan} / 100")
    m2.metric("Doğru Sayısı", f"{dogru_sayisi}", delta=f"{dogru_sayisi} D")
    m3.metric("Yanlış Sayısı", f"{yanlis_sayisi}", delta=f"-{yanlis_sayisi} Y", delta_color="inverse")
    m4.metric("Toplam Süre", f"{sure_sn // 60} dk {sure_sn % 60} sn")

    st.markdown("---")
    st.markdown("### 📝 Soru Detaylı Çözüm Analizi")

    for idx, q in enumerate(quiz_data):
        dogru = q.get("dogru_cevap", "").strip().upper()
        verilen = user_answers.get(idx, "BOŞ").strip().upper()
        durum_ikonu = "✅" if verilen == dogru else ("⭕" if verilen == "BOŞ" else "❌")

        with st.expander(f"{durum_ikonu} Soru {idx + 1} ({q.get('ders', 'Genel')}) - Öğrencinin Cevabı: {verilen} | Doğru Cevap: {dogru}"):
            st.markdown(f"**Soru Metni:** {temizle_latex_metin(q.get('soru_metni'))}")
            
            secenekler = q.get("secenekler", {})
            for k in ["A", "B", "C", "D"]:
                if k in secenekler:
                    isaret = "🎯 " if k == dogru else ("👉 " if k == verilen else "   ")
                    st.markdown(f"{isaret} **{k})** {temizle_latex_metin(secenekler[k])}")

            st.markdown(f"💡 **Çözüm Açıklaması:** {temizle_latex_metin(q.get('cozum_aciklamasi', 'Açıklama bulunmuyor.'))}")

    st.markdown("---")
    c_yenile1, c_yenile2 = st.columns(2)
    with c_yenile1:
        if st.button("🔄 Yeni Sınav Başlat", use_container_width=True, type="primary"):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.exam_started = False
            st.session_state.start_time = None
            st.session_state.total_duration = None
            st.session_state.current_question = 0
            st.rerun()

    with c_yenile2:
        if st.button("❌ Yanlış Sorulardan Yeni Sınav Üret", use_container_width=True):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.exam_started = False
            st.session_state.start_time = None
            st.session_state.total_duration = None
            st.session_state.current_question = 0
            st.success("Sol panelden sınav türünü 'Yanlışlardan Üretilen Sorular' olarak seçip yeni test oluşturabilirsiniz!")
            st.rerun()
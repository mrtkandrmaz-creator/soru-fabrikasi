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
import numpy as np

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

# --- GELİŞMİŞ FEN VE MATEMATİK GÖRSEL ÇİZİCİ (ScienceVisualWidget) ---
def ciz_vektorel_gorsel(gorsel_tipi="yok", etiketler=None):
    if not isinstance(etiketler, dict):
        etiketler = {}
        
    fig, ax = plt.subplots(figsize=(4.5, 3.3))
    ax.set_aspect('equal')
    ax.axis('off')
    
    tip = str(gorsel_tipi).lower()
    
    # 1. DÜNYA, GÜNEŞ, AY VE UZAY SİSTEMLERİ
    if "gunes_dunya_ay" in tip or "astronomi" in tip:
        # Güneş (Sol)
        sun = plt.Circle((1.0, 2.5), 0.7, color='#f59e0b', ec='#d97706', linewidth=2)
        ax.add_patch(sun)
        ax.text(1.0, 2.5, etiketler.get("G", "GÜNEŞ"), fontsize=8, fontweight='bold', ha='center', va='center', color='#ffffff')
        
        # Dünya (Orta)
        earth = plt.Circle((3.0, 2.5), 0.45, color='#38bdf8', ec='#0284c7', linewidth=2)
        ax.add_patch(earth)
        ax.text(3.0, 2.5, etiketler.get("D", "DÜNYA"), fontsize=7, fontweight='bold', ha='center', va='center', color='#0f172a')
        
        # Ay (Sağ üst)
        moon = plt.Circle((4.1, 3.2), 0.2, color='#cbd5e1', ec='#64748b', linewidth=1.5)
        ax.add_patch(moon)
        ax.text(4.1, 3.2, etiketler.get("A", "AY"), fontsize=6, fontweight='bold', ha='center', va='center', color='#1e293b')
        
        # Yörünge çizgileri
        theta = np.linspace(0, 2*np.pi, 100)
        ax.plot(3.0 + 1.1*np.cos(theta), 2.5 + 0.7*np.sin(theta), color='#94a3b8', linestyle='--', linewidth=1)
        ax.text(3.0, 3.4, etiketler.get("O", "Ay'ın Yörüngesi"), fontsize=8, color='#64748b', ha='center')

    # 2. DİNAMOMETRE VE KUVVET ÖLÇÜM DÜZENEĞİ
    elif "dinamometre" in tip or "kuvvet_hareket" in tip:
        # Üst askı halkası
        ax.plot([3.0, 3.0], [4.4, 4.0], color='#475569', linewidth=3)
        ring = plt.Circle((3.0, 4.5), 0.15, color='#475569', fill=False, linewidth=2.5)
        ax.add_patch(ring)
        
        # Silindirik gövde (Dinamometre dış kabuğu)
        body = plt.Rectangle((2.6, 1.8), 0.8, 2.2, color='#e2e8f0', ec='#0f172a', linewidth=2, alpha=0.8)
        ax.add_patch(body)
        
        # İç yay çizgileri (Zikzak)
        y_spring = np.linspace(3.9, 2.7, 10)
        x_spring = 3.0 + 0.15 * np.sin(np.linspace(0, 4*np.pi, 10))
        ax.plot(x_spring, y_spring, color='#f97316', linewidth=2)
        
        # Ölçek çizgileri
        for y_tick in np.linspace(2.8, 3.8, 6):
            ax.plot([2.6, 2.8], [y_tick, y_tick], color='#0f172a', linewidth=1.2)
            
        # Alt çengel ve ağırlık
        ax.plot([3.0, 3.0], [1.8, 1.2], color='#475569', linewidth=2.5)
        weight_box = plt.Rectangle((2.5, 0.5), 1.0, 0.7, color='#cbd5e1', ec='#0f172a', linewidth=2)
        ax.add_patch(weight_box)
        ax.text(3.0, 0.85, etiketler.get("Y", "Yük (G)"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')
        ax.text(3.6, 2.8, etiketler.get("N", "N"), fontsize=10, fontweight='bold', color='#dc2626')

    # 3. DÜNYA'NIN KATMANLARI
    elif "dunya_katmanlari" in tip:
        k_dis = plt.Circle((3.0, 2.5), 1.9, color='#38bdf8', alpha=0.4, ec='#0284c7', linewidth=2)
        k_manto = plt.Circle((3.0, 2.5), 1.3, color='#f97316', alpha=0.6, ec='#c2410c', linewidth=2)
        k_cekirdek = plt.Circle((3.0, 2.5), 0.6, color='#dc2626', ec='#991b1b', linewidth=2)
        ax.add_patch(k_dis)
        ax.add_patch(k_manto)
        ax.add_patch(k_cekirdek)
        ax.text(3.0, 4.0, etiketler.get("K1", "Hava Küre (Atmosfer)"), fontsize=8, fontweight='bold', ha='center', color='#0369a1')
        ax.text(3.0, 2.5, etiketler.get("K2", "Çekirdek"), fontsize=8, fontweight='bold', ha='center', color='#ffffff')

    # 4. MATEMATİK: ÇEMBER VE DAİRE (KİRİŞ, ÇAP, YARIÇAP, MERKEZİ AÇI)
    elif "cember" in tip or "daire" in tip:
        # Ana Çember
        cember = plt.Circle((3.0, 2.5), 1.6, color='#0f172a', fill=False, linewidth=2.2)
        ax.add_patch(cember)
        
        # Merkez Noktası M
        ax.plot(3.0, 2.5, 'ko', markersize=5)
        ax.text(3.1, 2.65, etiketler.get("M", "M"), fontsize=10, fontweight='bold', color='#0f172a')
        
        # Yarıçap (r)
        ax.plot([3.0, 4.6], [2.5, 2.5], color='#dc2626', linewidth=1.8, linestyle='--')
        ax.text(3.8, 2.7, etiketler.get("r", "r"), fontsize=10, fontweight='bold', color='#dc2626')
        
        # Kiriş veya ikinci yarıçap ile açı oluşturma
        ax.plot([3.0, 1.8], [2.5, 3.8], color='#2563eb', linewidth=1.8)
        ax.text(2.3, 3.3, etiketler.get("R2", ""), fontsize=9, color='#2563eb')
        
        ax.text(3.0, 0.4, etiketler.get("Aciklama", "Çember ve Daire Geometrisi"), fontsize=9, fontweight='bold', ha='center', color='#475569')

    # 5. ISITMA / HAL DEĞİŞTİRME / ISI
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

    # 6. BASINÇ (KATI / SIVI BASINCI)
    elif "basinc" in tip:
        rect_blok = plt.Rectangle((1.5, 2.0), 3.0, 1.2, color='#cbd5e1', ec='#0f172a', linewidth=2)
        ax.add_patch(rect_blok)
        ax.arrow(3.0, 4.0, 0.0, -0.8, head_width=0.3, head_length=0.2, fc='#dc2626', ec='#dc2626')
        ax.text(3.0, 4.25, etiketler.get("F", "Kuvvet (F)"), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(3.0, 2.6, etiketler.get("G", "Ağırlık (G)"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(3.0, 1.4, etiketler.get("S", "Yüzey Alanı (S)"), fontsize=9, fontweight='bold', ha='center', color='#475569')

    # 7. ELEKTRİK DEVRELERİ
    elif "devre" in tip or "elektrik" in tip:
        ax.plot([1.2, 4.8, 4.8, 1.2, 1.2], [1.5, 1.5, 3.6, 3.6, 1.5], color='#0f172a', linewidth=2, linestyle='--')
        circle_ampul = plt.Circle((3.0, 3.6), 0.38, color='#f59e0b', fill=True, ec='#0f172a', linewidth=2)
        ax.add_patch(circle_ampul)
        ax.text(3.0, 3.6, etiketler.get("A", "💡"), fontsize=12, ha='center', va='center')
        ax.text(3.0, 1.15, etiketler.get("P", "Güç Kaynağı / Pil"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')

    # 8. GEOMETRİ: DİK ÜÇGEN / PARALELKENAR
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
        # Varsayılan geometrik form
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
Sen MEB müfredatına tam hakim profesyonel bir soru hazırlama yapay zekasısın.
{secili_sinif} seviyesinde, {sinav_turu} kapsamında, TOPLAM {soru_sayisi} adet son derece nitelikli, özgün ve birbirini tekrar etmeyen çoktan seçmeli soru üret. 

{gorsel_talimati}

GENEL KURALLAR:
- Derece ifadeleri için LaTeX (`\\circ`) yerine doğrudan derece sembolü (°) kullan.

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
                                item["soru_no"] = idx + 1
                                if "ders" not in item:
                                    item["ders"] = aktif_dersler_listesi[0]
                                if "gorsel_tipi" not in item:
                                    item["gorsel_tipi"] = "cember" if "Matematik" in str(item.get("ders")) else "yok"
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
                st.success(f"{len(ctx.quiz_data)} adet gelişmiş fen ve çember görseli içeren soru başarıyla üretildi!")
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
        <h2>✨ Gelişmiş Fen ve Çember Sınavınız Hazır!</h2>
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
        
        gorsel_tipi = q.get("gorsel_tipi", "yok")
        etiketler = q.get("etiketler", {})
        
        if gorsel_tipi and gorsel_tipi.lower() != "yok":
            img_data_uri = ciz_vektorel_gorsel(gorsel_tipi=gorsel_tipi, etiketler=etiketler)
            st.markdown(f'''
                <div class="gorsel-sema-kutusu">
                    <img src="{img_data_uri}" style="max-width: 80%; height: auto;" />
                </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        secenekler = q.get("secenekler", {})
        keys_list = sorted(secenekler.keys())
        options_list = [f"{k}) {temizle_latex_metin(secenekler[k])}" for k in keys_list]

        widget_key = f"radio_q_{curr_idx}"

        kayitli_harf = st.session_state.user_answers.get(curr_idx, None)
        default_opt_index = None
        if kayitli_harf:
            for idx_opt, opt in enumerate(options_list):
                if opt.startswith(kayitli_harf + ")"):
                    default_opt_index = idx_opt
                    break

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
            st.session_state.current_question = max(0, curr_idx - 1)
            st.rerun()

    with col_next:
        if curr_idx < toplam_soru - 1:
            if st.button("Sonraki Soru ➡️", use_container_width=True, type="primary"):
                st.session_state.current_question = min(toplam_soru - 1, curr_idx + 1)
                st.rerun()
        else:
            if st.button("🏁 Sınavı Tamamla ve Bitir", use_container_width=True, type="primary"):
                st.session_state.quiz_submitted = True
                gecen_sure_toplam = int(time.time() - st.session_state.start_time)
                dakika = gecen_sure_toplam // 60
                saniye = gecen_sure_toplam % 60
                st.session_state.total_duration = f"{dakika:02d}:{saniye:02d}"
                st.rerun()

else:
    # --- SINAV SONUÇ EKRANI VE KARNE ---
    quiz_data = st.session_state.quiz_data
    user_answers = st.session_state.user_answers
    toplam_soru = len(quiz_data)

    dogru_sayisi = 0
    yanlis_sayisi = 0
    bos_sayisi = 0
    yeni_yanlislar = []

    for idx, q in enumerate(quiz_data):
        dogru_harf = str(q.get("dogru_cevap", "")).strip().upper()
        verilen_harf = str(user_answers.get(idx, "")).strip().upper()

        if not verilen_harf:
            bos_sayisi += 1
        elif verilen_harf == dogru_harf:
            dogru_sayisi += 1
        else:
            yanlis_sayisi += 1
            yeni_yanlislar.append({
                "ders": q.get("ders", "Genel"),
                "soru_metni": q.get("soru_metni", ""),
                "dogru_cevap": dogru_harf,
                "verilen_cevap": verilen_harf,
                "cozum": q.get("cozum_aciklamasi", "")
            })

    # Yanlış arşivine ekle (tekrarları önleyerek)
    for y in yeni_yanlislar:
        if y not in st.session_state.yanlis_sorular_arsivi:
            st.session_state.yanlis_sorular_arsivi.append(y)

    basari_orani = (dogru_sayisi / toplam_soru) * 100 if toplam_soru > 0 else 0

    # Performans geçmişine kaydet
    mevcut_tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
    karne_kaydi = {
        "tarih": mevcut_tarih,
        "sinif": f"{dogru_sayisi} Doğru, {yanlis_sayisi} Yanlış, {bos_sayisi} Boş",
        "dogru": dogru_sayisi,
        "yanlis": yanlis_sayisi,
        "sure": st.session_state.total_duration or "Bilinmiyor"
    }
    if karne_kaydi not in st.session_state.performance_history:
        st.session_state.performance_history.append(karne_kaydi)

    st.markdown("""
    <div class="custom-card">
        <h2>🎉 Sınav Tamamlandı! Karne Raporunuz</h2>
        <p style="color: #64748b; font-size: 16px;">Performans özetiniz ve soru detaylı çözüm analiziniz aşağıdadır.</p>
    </div>
    """, unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="🎯 Başarı Oranı", value=f"%{basari_orani:.1f}")
    with col_m2:
        st.metric(label="✅ Doğru Sayısı", value=str(dogru_sayisi))
    with col_m3:
        st.metric(label="❌ Yanlış Sayısı", value=str(yanlis_sayisi))
    with col_m4:
        st.metric(label="⏱️ Toplam Süre", value=str(st.session_state.total_duration or "00:00"))

    st.markdown("---")
    st.markdown("### 📋 Soru Detayları ve Çözüm Analizleri")

    for idx, q in enumerate(quiz_data):
        dogru_harf = str(q.get("dogru_cevap", "")).strip().upper()
        verilen_harf = str(user_answers.get(idx, "")).strip().upper()
        
        durum_ikonu = "⚪ Boş"
        border_renk = "#cbd5e1"
        if verilen_harf:
            if verilen_harf == dogru_harf:
                durum_ikonu = "✅ Doğru"
                border_renk = "#22c55e"
            else:
                durum_ikonu = "❌ Yanlış"
                border_renk = "#ef4444"

        with st.container(border=True):
            st.markdown(f"**Soru {idx + 1}** &nbsp;|&nbsp; *{q.get('ders', 'Genel')}* &nbsp;|&nbsp; Durum: **{durum_ikonu}**")
            st.markdown(f"<div style='font-size: 16px; font-weight: 600; margin: 10px 0;'>{temizle_latex_metin(q.get('soru_metni', ''))}</div>", unsafe_allow_html=True)

            secenekler = q.get("secenekler", {})
            for sec_key in sorted(secenekler.keys()):
                sec_metin = temizle_latex_metin(secenekler[sec_key])
                isaret = ""
                if sec_key == dogru_harf:
                    isaret = " 🟢 *(Doğru Cevap)*"
                elif sec_key == verilen_harf and sec_key != dogru_harf:
                    isaret = " 🔴 *(Seçtiğiniz Cevap)*"
                elif sec_key == verilen_harf and sec_key == dogru_harf:
                    isaret = " ⭐ *(Seçtiğiniz ve Doğru Cevap)*"
                
                st.markdown(f"- **{sec_key})** {sec_metin}{isaret}")

            st.markdown("---")
            st.markdown(f"💡 **Çözüm Açıklaması:**\n{temizle_latex_metin(q.get('cozum_aciklamasi', 'Açıklama bulunmuyor.'))}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Yeni Sınav Başlat", use_container_width=True, type="primary"):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.exam_started = False
            st.session_state.start_time = None
            st.session_state.total_duration = None
            st.session_state.current_question = 0
            st.rerun()

    with col_btn2:
        if st.button("❌ Yanlış Sorulardan Deneme Oluştur", use_container_width=True):
            if st.session_state.yanlis_sorular_arsivi:
                donusturulen_sorular = []
                for idx_y, y_item in enumerate(st.session_state.yanlis_sorular_arsivi):
                    donusturulen_sorular.append({
                        "soru_no": idx_y + 1,
                        "soru_metni": y_item["soru_metni"],
                        "secenekler": {"A": "Seçenekler arşivden yeniden yapılandırılıyor...", "B": "Seçenek 2", "C": "Seçenek 3", "D": "Seçenek 4"},
                        "dogru_cevap": y_item["dogru_cevap"],
                        "cozum_aciklamasi": y_item.get("cozum", "Geçmiş yanlış çözümünden tekrar."),
                        "ders": y_item["ders"],
                        "gorsel_tipi": "yok",
                        "etiketler": {}
                    })
                st.session_state.quiz_data = donusturulen_sorular
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.exam_started = False
                st.session_state.start_time = None
                st.session_state.total_duration = None
                st.session_state.current_question = 0
                st.success("Yanlış yapılan sorulardan oluşan tekrar sınavı hazırlandı!")
                st.rerun()
            else:
                st.warning("Arşivinizde henüz kaydedilmiş yanlış soru bulunmuyor!")
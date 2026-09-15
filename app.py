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
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(249, 115, 22, 0.25);
    }
    div.stButton > button[kind="primary"] {
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
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%) !important;
        box-shadow: 0 14px 24px -4px rgba(124, 58, 237, 0.6);
        transform: translateY(-3px);
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

# --- DİNAMİK ÜÇGEN HARF ÇIKARICI ---
def get_triangle_labels(etiketler):
    vertex_keys = [k for k in etiketler.keys() if isinstance(k, str) and len(k) == 1 and k.isupper()]
    if len(vertex_keys) >= 3:
        return etiketler.get(vertex_keys[0], vertex_keys[0]), etiketler.get(vertex_keys[1], vertex_keys[1]), etiketler.get(vertex_keys[2], vertex_keys[2])
    return etiketler.get("A", "A"), etiketler.get("B", "B"), etiketler.get("C", "C")

# --- GELİŞMİŞ VE DİNAMİK ÜÇGEN / FEN / GRAFİK GÖRSEL ÇİZİCİ (UYUM KONTROLLÜ) ---
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
        ax.text(1.5, 0.3, etiketler.get("X1", "A"), fontsize=9, fontweight='bold', ha='center', color='#ffffff')
        ax.text(3.0, 0.3, etiketler.get("X2", "B"), fontsize=9, fontweight='bold', ha='center', color='#ffffff')
        ax.text(4.5, 0.3, etiketler.get("X3", "C"), fontsize=9, fontweight='bold', ha='center', color='#ffffff')

    elif "cember" in tip or "daire" in tip:
        cember = plt.Circle((3.0, 2.5), 1.5, color='#0f172a', fill=False, linewidth=2.2)
        ax.add_patch(cember)
        ax.plot(3.0, 2.5, 'ko', markersize=5)
        ax.text(3.1, 2.65, etiketler.get("M", "M"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.plot([3.0, 4.5], [2.5, 2.5], color='#dc2626', linewidth=1.8, linestyle='--')
        ax.text(3.75, 2.7, etiketler.get("r", "r"), fontsize=10, fontweight='bold', color='#dc2626')
        ax.text(3.0, 0.4, etiketler.get("Aciklama", "Çember Geometrisi"), fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "dik_ucgen" in tip:
        lbl_a, lbl_b, lbl_c = get_triangle_labels(etiketler)
        bx, by = 1.2, 1.0
        cx, cy = 4.8, 1.0
        ax_val, ay_val = 1.2, 4.0
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        ax.plot([1.2, 1.5, 1.5, 1.2], [1.0, 1.0, 1.3, 1.3], color='#0f172a', linewidth=1.5)
        
        ax.text(ax_val - 0.25, ay_val + 0.1, lbl_a, fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, lbl_b, fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.15, cy - 0.25, lbl_c, fontsize=11, fontweight='bold', color='#0f172a')
        
        ax.text(2.0, 2.7, etiketler.get("c", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(3.0, 0.7, etiketler.get("a", ""), fontsize=10, fontweight='bold', color='#dc2626')
        ax.text(1.4, 2.5, etiketler.get("b", ""), fontsize=10, fontweight='bold', color='#16a34a')
        ax.text(3.0, 0.3, "Dik Üçgen", fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "eskenar_ucgen" in tip:
        lbl_a, lbl_b, lbl_c = get_triangle_labels(etiketler)
        bx, by = 1.5, 1.0
        cx, cy = 4.5, 1.0
        ax_val, ay_val = 3.0, 1.0 + 1.5 * np.sqrt(3)
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        
        ax.text(ax_val, ay_val + 0.15, lbl_a, fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, lbl_b, fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.25, lbl_c, fontsize=11, fontweight='bold', color='#0f172a')
        
        ax.text(3.0, 2.2, etiketler.get("aci", "60°"), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(3.0, 0.3, "Eşkenar Üçgen", fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "ikizkenar_ucgen" in tip:
        lbl_a, lbl_b, lbl_c = get_triangle_labels(etiketler)
        bx, by = 1.3, 1.0
        cx, cy = 4.7, 1.0
        ax_val, ay_val = 3.0, 4.2
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        
        ax.text(ax_val, ay_val + 0.15, lbl_a, fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, lbl_b, fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.25, lbl_c, fontsize=11, fontweight='bold', color='#0f172a')
        
        ax.text(2.0, 2.8, etiketler.get("kenar1", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(4.0, 2.8, etiketler.get("kenar2", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(3.0, 0.7, etiketler.get("taban", ""), fontsize=10, fontweight='bold', color='#dc2626')
        ax.text(3.0, 0.3, "İkizkenar Üçgen", fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "cesitkenar_ucgen" in tip or "ucgen" in tip:
        lbl_a, lbl_b, lbl_c = get_triangle_labels(etiketler)
        bx, by = 1.0, 1.0
        cx, cy = 5.0, 1.2
        ax_val, ay_val = 2.2, 4.0
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        
        ax.text(ax_val - 0.2, ay_val + 0.15, lbl_a, fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, lbl_b, fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.25, lbl_c, fontsize=11, fontweight='bold', color='#0f172a')
        
        ax.text(1.5, 2.6, etiketler.get("c", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(3.6, 2.7, etiketler.get("b", ""), fontsize=10, fontweight='bold', color='#16a34a')
        ax.text(3.0, 0.9, etiketler.get("a", ""), fontsize=10, fontweight='bold', color='#dc2626')
        ax.text(3.0, 0.3, "Çeşitkenar Üçgen", fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "basinc" in tip:
        rect_blok = plt.Rectangle((1.5, 2.0), 3.0, 1.2, color='#cbd5e1', ec='#0f172a', linewidth=2)
        ax.add_patch(rect_blok)
        ax.arrow(3.0, 4.0, 0.0, -0.8, head_width=0.3, head_length=0.2, fc='#dc2626', ec='#dc2626')
        ax.text(3.0, 4.25, etiketler.get("F", "Kuvvet"), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(3.0, 2.6, etiketler.get("G", "Ağırlık"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(3.0, 1.4, etiketler.get("S", "Yüzey"), fontsize=9, fontweight='bold', ha='center', color='#475569')

    else:
        circle_def = plt.Circle((3, 2.5), 1.5, color='#0f172a', fill=False, linewidth=2.2)
        ax.add_patch(circle_def)
        ax.text(3, 2.5, etiketler.get("Genel", "Yeni Nesil Soru Şeması"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')

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
    
    # İstenen 6 Sınav Türü
    sinav_turu = st.selectbox("Sınav Türü:", [
        "Genel Tarama Sınavı",
        "Konu Tarama Sınavı",
        "Yanlışlardan Üretilen Sorular",
        "LGS Geçmiş Yıllar Çıkmış Sorular",
        "Hazır Bulunuşluk Sınavı",
        "Yeni Nesil Sorular"
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
    soru_sayisi = st.slider("🔢 Soru Sayısı:", 1, 100, 9)

    if st.button("🚀 Soru Üretimini Başlat", use_container_width=True, type="primary"):
        if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
            st.error("Geçerli bir API anahtarı bulunamadı!")
        elif not secili_ders_unite_haritasi:
            st.error("Lütfen en az bir ders veya ünite seçiniz!")
        else:
            # Sınav türüne özel bağlam ve prompt kuralı türetme
            ek_baglam = ""
            if sinav_turu == "Yanlışlardan Üretilen Sorular":
                ilgili_yanlislar = [y for y in st.session_state.yanlis_sorular_arsivi if y.get('ders') in secili_ders_unite_haritasi.keys()]
                if ilgili_yanlislar:
                    ek_baglam = "Öğrencinin geçmişte hata yaptığı benzer soru örnekleri üzerinden aynı konsepti farklı açılardan ele alan pekiştirici benzer nitelikte sorular üret.\n"
                else:
                    ek_baglam = "Öğrencinin yanlış arşivinde soru bulunmuyor; bu nedenle seçilen alanlarda öğrencinin en çok zorlandığı kritik kazanımlardan oluşan pekiştirici sorular üret.\n"
            elif sinav_turu == "Genel Tarama Sınavı":
                ek_baglam = "Bu sınav seçilen tüm ders ve üniteleri kapsayan, öğrencinin genel bilgi düzeyini ve kazanım hakimiyetini ölçen dengeli bir genel tarama sınavı olmalıdır.\n"
            elif sinav_turu == "Konu Tarama Sınavı":
                ek_baglam = "Bu sınav seçilen alt başlıkları ve konuları derinlemesine irdeleyen, kavram yanılgılarını hedefleyen detaylı bir konu tarama sınavı olmalıdır.\n"
            elif sinav_turu == "LGS Geçmiş Yıllar Çıkmış Sorular":
                ek_baglam = "Bu sorular MEB LGS'de çıkmış gerçek soruların mantığına, zorluk derecesine, kazanım odaklılığına ve beceri temelli yapısına birebir uygun özgün benzer sorular olmalıdır.\n"
            elif sinav_turu == "Hazır Bulunuşluk Sınavı":
                ek_baglam = "Bu sınav, öğrencinin yeni döneme veya konulara başlarken bilmesi gereken ön koşul temel kavramları ve temel becerileri ölçen bir hazır bulunuşluk sınavı olmalıdır.\n"
            elif sinav_turu == "Yeni Nesil Sorular":
                ek_baglam = "Bu sorular günlük yaşam problemleri içeren, grafik, tablo, şema veya görsel yorumlama becerisini ölçen, analitik düşünceye dayalı yeni nesil beceri temelli sorular olmalıdır.\n"

            ders_unite_detay = ""
            aktif_dersler_listesi = list(secili_ders_unite_haritasi.keys())
            for d, u_list in secili_ders_unite_haritasi.items():
                ders_unite_detay += f"- Ders/Kategori: {d}, Alt Başlıklar: {', '.join(u_list)}\n"

            gorsel_talimati = """
            KESİN UYUM VE GÖRSEL TUTARLILIK KURALLARI (ÇOK ÖNEMLİ):
            1. Soru metninde anlatılan olay, kavram, şekil veya geometrik yapı ile `gorsel_tipi` kesinlikle birbiriyle UYUŞMALIDIR. 
               - Metin dik üçgenden bahsediyorsa `gorsel_tipi` kesinlikle "dik_ucgen" olmalıdır.
               - Metin çember / daireden bahsediyorsa `gorsel_tipi` kesinlikle "cember" olmalıdır.
               - Metin grafik veya veriden bahsediyorsa `gorsel_tipi` kesinlikle "grafik" olmalıdır.
               - Metin Güneş-Dünya-Ay olayından bahsediyorsa `gorsel_tipi` kesinlikle "gunes_dunya_ay" olmalıdır.
               - Metin basınç veya kuvvetten bahsediyorsa `gorsel_tipi` kesinlikle "basinc" veya "dinamometre" olmalıdır.
               - Hiçbir görsel gerektirmeyen sorularda `gorsel_tipi` "yok" olmalıdır.
            2. Soru metninde hangi harfler (Örn: KLM, ABC, PRS) veya değerler verildiyse, `etiketler` sözlüğünde de eksiksiz olarak yer almalıdır. Soru metni ile görsel asla çelişmemelidir.
            """

            prompt = f"""
Sen MEB müfredatına, LGS sistemine ve yeni nesil soru hazırlama tekniklerine tam hakim profesyonel bir soru hazırlama yapay zekasısın.
{secili_sinif} seviyesinde, '{sinav_turu}' konsepti ve formatında, TOPLAM {soru_sayisi} adet nitelikli, özgün sorular üret. 
Matematik ve geometri sorularında dik üçgen, eşkenar üçgen, ikizkenar üçgen ve çeşitkenar üçgen türlerinin tamamından dengeli ve harf uyumlu sorular hazırlamaya özen göster.

{gorsel_talimati}

GENEL KURALLAR:
- Derece ifadeleri için LaTeX yerine doğrudan derece sembolü (°) kullan.
- Almanca sorular için dil kurallarına tam uyum sağla.

Zorluk Seviyesi: {zorluk_seviyesi}
Sınav Türü Hedefi: {sinav_turu}
Seçilen Alanlar:
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
    "gorsel_tipi": "dik_ucgen", 
    "etiketler": {{"K": "K", "L": "L", "M": "M", "a": "8 cm", "b": "6 cm", "c": "10 cm"}}
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
            
            def api_cagirici():
                max_deneme = len(API_KEYS) * 2 if API_KEYS else 3
                deneme = 0
                
                while deneme < max_deneme and not ctx.basarili:
                    current_key = api_manager.get_next_key()
                    if not current_key:
                        ctx.hata_mesaji = "Kullanılabilir API anahtarı bulunamadı."
                        break
                        
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
                                        item["gorsel_tipi"] = "yok"
                                    if "etiketler" not in item:
                                        item["etiketler"] = {}
                                ctx.basarili = True
                                break
                    except Exception as e:
                        err_str = str(e)
                        ctx.hata_mesaji = err_str
                        if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
                            time.sleep(2)
                        else:
                            time.sleep(1)
                    deneme += 1
                
                ctx.api_tamamlandi = True

            t = threading.Thread(target=api_cagirici)
            t.start()

            while not ctx.api_tamamlandi:
                gecen_sure = time.time() - baslangic_zamani
                kalan_tahmin = max(0, tahmini_sure_sn - int(gecen_sure))
                oran = min(0.95, gecen_sure / tahmini_sure_sn)
                progress_bar.progress(oran)
                status_placeholder.markdown(f"⏳ **{sinav_turu} için sorular hazırlanıyor...** Tahmini kalan süre: **{kalan_tahmin} saniye**")
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
                st.success(f"'{sinav_turu}' konseptine uygun {len(ctx.quiz_data)} adet soru başarıyla üretildi!")
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

    if st.session_state.yanlis_sorular_arsivi:
        if st.button("🗑️ Yanlış Arşivini Temizle"):
            st.session_state.yanlis_sorular_arsivi = []
            st.rerun()

# --- ANA İÇERİK VE TABLET SINAV EKRANI ---
st.markdown("<h1 style='text-align: center; color: #0f172a;'>🎓 Soru Fabrikası Tablet Sınav & Eğitim Modülü</h1>", unsafe_allow_html=True)

if not st.session_state.quiz_data:
    st.markdown("""
        <div class="custom-card">
            <h2>Hoş Geldiniz!</h2>
            <p style='font-size: 16px; color: #475569;'>
                Sol menüden eğitim seviyenizi, sınav türünüzü, ders ve ünitelerinizi seçerek 
                <b>"Soru Üretimini Başlat"</b> butonuna tıklayınız. Yapay zeka seçtiğiniz sınav formatına 
                ve metin uyumuna kusursuz uyan sorular hazırlayacaktır.
            </p>
        </div>
    """, unsafe_allow_html=True)
else:
    quiz = st.session_state.quiz_data
    toplam_soru = len(quiz)
    
    hesaplanan_toplam_sure_sn = toplam_soru * 80
    hesaplanan_dk = hesaplanan_toplam_sure_sn // 60
    hesaplanan_sn = hesaplanan_toplam_sure_sn % 60
    sure_aciklama_metni = f"Sınav toplam **{toplam_soru} soru** içermektedir. Her soru için 80 saniye hesaplanarak toplam sınav süreniz **{hesaplanan_dk} dakika {hesaplanan_sn} saniye** olarak ayarlanmıştır." if hesaplanan_sn > 0 else f"Sınav toplam **{toplam_soru} soru** içermektedir. Her soru için 80 saniye hesaplanarak toplam sınav süreniz **{hesaplanan_dk} dakika** olarak ayarlanmıştır."

    if not st.session_state.exam_started:
        st.markdown(f"""
            <div class="custom-card">
                <h3>📝 Sınav Hazır ({toplam_soru} Soru)</h3>
                <p style='color: #475569; font-size: 16px;'>{sure_aciklama_metni}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Sınavı Şimdi Başlat", type="primary", use_container_width=True):
                st.session_state.exam_started = True
                st.session_state.start_time = time.time()
                st.session_state.total_duration = toplam_soru * 80
                st.rerun()
    
    else:
        @st.fragment(run_every=1)
        def render_live_timer_and_metrics():
            gecen_zaman = time.time() - st.session_state.start_time
            kalan_saniye = int(st.session_state.total_duration - gecen_zaman)
            
            if kalan_saniye <= 0:
                st.session_state.quiz_submitted = True
                st.warning("⏰ Süre doldu! Sınavınız otomatik olarak sonlandırıldı.")
                st.rerun()
            else:
                dk = kalan_saniye // 60
                sn = kalan_saniye % 60
                kalan_sure_str = f"{dk:02d}:{sn:02d}"

            col_u1, col_u2, col_u3 = st.columns([2, 2, 2])
            with col_u1:
                st.metric("📊 Soru İlerlemesi", f"{st.session_state.current_question + 1} / {toplam_soru}")
            with col_u2:
                st.metric("⏳ Kalan Süre", kalan_sure_str)
            with col_u3:
                cevaplanan_sayisi = len(st.session_state.user_answers)
                st.metric("✍️ Cevaplanan", f"{cevaplanan_sayisi} / {toplam_soru}")

        render_live_timer_and_metrics()

        st.progress((st.session_state.current_question + 1) / toplam_soru)
        st.markdown("---")

        q_idx = st.session_state.current_question
        q = quiz[q_idx]

        st.markdown(f"""
            <div class="custom-card" style="text-align: left;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="background-color: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 14px;">
                        {q.get('ders', 'Genel')}
                    </span>
                    <span style="color: #64748b; font-weight: 600; font-size: 14px;">
                        Soru #{q.get('soru_no', q_idx + 1)}
                    </span>
                </div>
                <div class="soru-metni-kutusu">
                    {temizle_latex_metin(q.get('soru_metni', ''))}
                </div>
            </div>
        """, unsafe_allow_html=True)

        g_tipi = q.get('gorsel_tipi', 'yok')
        g_etiketleri = q.get('etiketler', {})
        if g_tipi and g_tipi != "yok":
            base64_img = ciz_vektorel_gorsel(g_tipi, g_etiketleri)
            st.markdown(f"""
                <div class="gorsel-sema-kutusu">
                    <img src="{base64_img}" style="max-width: 100%; height: auto; border-radius: 8px;" />
                </div>
            """, unsafe_allow_html=True)

        with st.expander("✏️ Dijital Karalama ve Çizim Tahtası (Tablet Çizim Alanı)"):
            st.markdown("Bu alanda parmağınızla veya kaleminizle işlem yapabilirsiniz.")
            st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=3,
                stroke_color="#0f172a",
                background_color="#ffffff",
                height=220,
                width=650,
                drawing_mode="freedraw",
                key=f"canvas_soru_{q_idx}"
            )

        secenekler = q.get('secenekler', {})
        secenek_anahtarlari = sorted(list(secenekler.keys()))
        
        mevcut_cevap = st.session_state.user_answers.get(q_idx, None)
        secilen_index = secenek_anahtarlari.index(mevcut_cevap) if mevcut_cevap in secenek_anahtarlari else None

        secim_formatli = [f"{k}) {temizle_latex_metin(v)}" for k, v in secenekler.items()]
        
        secilen_radyo = st.radio(
            f"Soru #{q.get('soru_no', q_idx + 1)} için cevap seçiniz:",
            secim_formatli,
            index=secilen_index,
            key=f"radio_q_{q_idx}"
        )

        if secilen_radyo:
            harf = secilen_radyo.split(")")[0].strip()
            st.session_state.user_answers[q_idx] = harf

        st.markdown("---")

        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        with col_nav1:
            if q_idx > 0:
                if st.button("⬅️ Önceki Soru", use_container_width=True):
                    st.session_state.current_question -= 1
                    st.rerun()
        with col_nav2:
            if not st.session_state.quiz_submitted:
                if st.button("📋 Sınavı Tamamla ve Karneni Gör", type="primary", use_container_width=True):
                    st.session_state.quiz_submitted = True
                    st.rerun()
        with col_nav3:
            if q_idx < toplam_soru - 1:
                if st.button("Sonraki Soru ➡️", use_container_width=True):
                    st.session_state.current_question += 1
                    st.rerun()

    if st.session_state.quiz_submitted:
        st.markdown("---")
        st.markdown("<h2 style='text-align: center; color: #0f172a;'>🎯 Sınav Değerlendirme ve Çözüm Karnesi</h2>", unsafe_allow_html=True)

        dogru_sayisi = 0
        yanlis_sayisi = 0
        bos_sayisi = 0

        yeni_yanlislar = []

        for idx, item in enumerate(quiz):
            ogrenci_cvp = st.session_state.user_answers.get(idx, None)
            dogru_cvp = item.get('dogru_cevap', '').strip().upper()

            if not ogrenci_cvp:
                bos_sayisi += 1
            elif ogrenci_cvp == dogru_cvp:
                dogru_sayisi += 1
            else:
                yanlis_sayisi += 1
                yeni_yanlislar.append(item)

        simdi_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        sure_bilgisi = f"{toplam_soru} Soru x 80 Sn ({toplam_soru * 80 // 60} Dk)"
        
        karne_ozet = {
            "tarih": simdi_str,
            "sinif": f"D: {dogru_sayisi} Y: {yanlis_sayisi} B: {bos_sayisi}",
            "dogru": dogru_sayisi,
            "yanlis": yanlis_sayisi,
            "sure": sure_bilgisi
        }
        if not st.session_state.performance_history or st.session_state.performance_history[-1] != karne_ozet:
            st.session_state.performance_history.append(karne_ozet)
            for y_item in yeni_yanlislar:
                if y_item not in st.session_state.yanlis_sorular_arsivi:
                    st.session_state.yanlis_sorular_arsivi.append(y_item)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("✅ Doğru Sayısı", dogru_sayisi, delta=None)
        with m2:
            st.metric("❌ Yanlış Sayısı", yanlis_sayisi, delta=None)
        with m3:
            st.metric("📌 Boş Sayısı", bos_sayisi, delta=None)
        with m4:
            basari_orani = int((dogru_sayisi / toplam_soru) * 100) if toplam_soru > 0 else 0
            st.metric("🏆 Başarı Puanı", f"%{basari_orani}")

        st.markdown("---")
        st.markdown("### 💡 Soru Soru Çözüm Analizleri")

        for idx, item in enumerate(quiz):
            ogrenci_cvp = st.session_state.user_answers.get(idx, "Boş")
            dogru_cvp = item.get('dogru_cevap', '').strip().upper()
            durum_ikonu = "✅" if ogrenci_cvp == dogru_cvp else ("❌" if ogrenci_cvp != "Boş" else "⚠️")

            with st.expander(f"{durum_ikonu} Soru #{item.get('soru_no', idx + 1)} - {item.get('ders', 'Genel')} (Senin Cevabın: {ogrenci_cvp} | Doğru: {dogru_cvp})"):
                st.markdown(f"**Soru:** {temizle_latex_metin(item.get('soru_metni', ''))}")
                
                secenekler = item.get('secenekler', {})
                for k, v in secenekler.items():
                    isaret = ""
                    if k == dogru_cvp:
                        isaret = " ⭐ (Doğru Cevap)"
                    elif k == ogrenci_cvp:
                        isaret = " 👈 (Senin Cevabın)"
                    st.markdown(f"- **{k})** {temizle_latex_metin(v)}{isaret}")

                st.markdown(f"**📖 Çözüm Açıklaması:**\n{temizle_latex_metin(item.get('cozum_aciklamasi', 'Açıklama bulunmuyor.'))}")

        st.markdown("---")
        if st.button("🔄 Yeni Sınav Oluştur / Başa Dön", type="primary", use_container_width=True):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.exam_started = False
            st.rerun()
import streamlit as st
import streamlit.components.v1 as components
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
from concurrent.futures import ThreadPoolExecutor

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
        box-shadow: 0 6px 16px rgba(249, 115, 22, 0.35);
    }
    /* Sınav İçi Navigasyon Butonları (Turuncu Dolgulu ve Büyük) */
    div.stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #f97316 0%, #ea580c) !important;
        border: none !important;
        color: #ffffff !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 16px -4px rgba(249, 115, 22, 0.4);
    }
    div.stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #ea580c 0%, #c2410c) !important;
        box-shadow: 0 12px 20px -4px rgba(249, 115, 22, 0.6);
    }
    /* Birincil Butonlar (Mor/Gradient) */
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

# --- KALICI GÜNLÜK SAYAC YÖNETİMİ (DOSYA BAZLI) ---
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

# --- VEKTÖREL GÖRSEL ÇİZİCİ (HIZLANDIRILMIŞ) ---
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
        lbl_a, lbl_b, lbl_c = get_custom_labels(etiketler, ("A", "B", "C"))
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
        lbl_a, lbl_b, lbl_c = get_custom_labels(etiketler, ("A", "B", "C"))
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
        lbl_a, lbl_b, lbl_c = get_custom_labels(etiketler, ("A", "B", "C"))
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

    elif "benzer_ucgen" in tip or "benzerlik" in tip:
        lbl_a, lbl_b, lbl_c = get_custom_labels(etiketler, ("A", "B", "C"))
        lbl_d, lbl_e, lbl_f = etiketler.get("D", "D"), etiketler.get("E", "E"), etiketler.get("F", "F")
        
        bx1, by1 = 0.8, 1.0
        cx1, cy1 = 2.4, 1.0
        ax1, ay1 = 1.6, 3.2
        ax.plot([bx1, cx1, ax1, bx1], [by1, cy1, ay1, by1], color='#2563eb', linewidth=2)
        ax.text(ax1, ay1 + 0.15, lbl_a, fontsize=10, fontweight='bold', ha='center', color='#2563eb')
        ax.text(bx1 - 0.15, by1 - 0.2, lbl_b, fontsize=10, fontweight='bold', ha='center', color='#2563eb')
        ax.text(cx1 + 0.15, by1 - 0.2, lbl_c, fontsize=10, fontweight='bold', ha='center', color='#2563eb')
        
        ax.text(1.6, 0.5, etiketler.get("oran1", "~"), fontsize=9, fontweight='bold', ha='center', color='#2563eb')

        ax.text(3.0, 2.1, "∼", fontsize=18, fontweight='bold', ha='center', color='#0f172a')

        bx2, by2 = 3.6, 1.0
        cx2, cy2 = 5.4, 1.0
        ax2, ay2 = 4.5, 3.8
        ax.plot([bx2, cx2, ax2, bx2], [by2, cy2, ay2, by2], color='#dc2626', linewidth=2)
        ax.text(ax2, ay2 + 0.15, lbl_d, fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(bx2 - 0.15, by2 - 0.2, lbl_e, fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(cx2 + 0.15, cy2 - 0.2, lbl_f, fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        
        ax.text(4.5, 0.5, etiketler.get("oran2", ""), fontsize=9, fontweight='bold', ha='center', color='#dc2626')
        ax.text(3.0, 0.1, "Benzer Üçgenler", fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "cesitkenar_ucgen" in tip or "ucgen" in tip:
        lbl_a, lbl_b, lbl_c = get_custom_labels(etiketler, ("A", "B", "C"))
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
        ax.text(3.0, 0.3, "Üçgen Geometrisi", fontsize=9, fontweight='bold', ha='center', color='#475569')

    elif "basinc" in tip:
        rect_blok = plt.Rectangle((1.5, 2.0), 3.0, 1.2, color='#cbd5e1', ec='#0f172a', linewidth=2)
        ax.add_patch(rect_blok)
        ax.arrow(3.0, 4.0, 0.0, -0.8, head_width=0.3, head_length=0.2, fc='#dc2626', ec='#dc2626')
        ax.text(3.0, 4.25, etiketler.get("F", "Kuvvet"), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(3.0, 2.6, etiketler.get("G", "Ağırlık"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(3.0, 1.4, etiketler.get("S", "Yüzey"), fontsize=9, fontweight='bold', ha='center', color='#475569')

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
        "Bilgi Yarışması": ["Sanat ve Dünya Tarihi", "Az Bilinen Coğrafya ve Doğa Mucizeleri", "Bilim, Uzay ve Nobel Ödüllü Keşifler", "Tarih", "Teknoloji", "Hayvanlar Alemi", "Geleneksel Yemek Kültürü", "Mitoloji, Edebiyat ve Felsefe Kuramları", "Güncel Konular", "Dünya Haritası", "Spor ve Müzik","Ülkeler Tarihi", "Ülke,Şehir ve Başkentler", "Dünya Mutfağı", "Coğrafi Konum", "Genel Kültür","İcatlar", "Şaşırtıcı Bilimsel Gerçekler ve Trivia"],
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

# Hızlı API İsteği Gönderici Fonksiyon
def api_cagrisi_yap(api_key, prompt):
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=3072
            )
        )
        return response.text
    except Exception:
        return None

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
        "LGS Geçmiş Yıllar Çıkmış Sorular",
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
            ek_baglam = ""
            if sinav_turu == "Yanlışlardan Üretilen Sorular":
                ek_baglam = "Öğrencinin zorlandığı kritik kazanımlardan oluşan pekiştirici sorular üret.\n"
            elif sinav_turu == "Genel Tarama Sınavı":
                ek_baglam = "Seçilen tüm ders ve üniteleri kapsayan dengeli bir genel tarama sınavı olmalıdır.\n"
            elif sinav_turu == "Konu Tarama Sınavı":
                ek_baglam = "Seçilen alt başlıkları ve konuları derinlemesine irdeleyen konu tarama sınavı olmalıdır.\n"
            elif sinav_turu == "LGS Geçmiş Yıllar Çıkmış Sorular":
                ek_baglam = "MEB LGS'de çıkmış gerçek soruların mantığına, zorluk derecesine ve yapısına birebir uygun benzer sorular olmalıdır.\n"
            elif sinav_turu == "Hazır Bulunuşluk Sınavı":
                ek_baglam = "Öğrencinin yeni döneme başlarken bilmesi gereken ön koşul temel kavramları ölçen sınav olmalıdır.\n"
            elif sinav_turu == "Yeni Nesil Sorular":
                ek_baglam = "Günlük yaşam problemleri içeren, grafik, tablo, şema veya görsel yorumlama becerisine dayalı yeni nesil beceri temelli sorular olmalıdır.\n"

            ders_unite_detay = ""
            for d, u_list in secili_ders_unite_haritasi.items():
                ders_unite_detay += f"- Ders/Kategori: {d}, Alt Başlıklar/Üniteler: {', '.join(u_list)}\n"

            gorsel_talimati = """
            GEOMETRİK ÇİZİM VE GÖRSEL SORU KURALLARI (ÇOK ÖNEMLİ):
            1. Üretilen soru havuzunda geometri (dik üçgen, eşkenar üçgen, ikizkenar üçgen, benzer üçgenler, açı veya çember), fen bilimleri (Güneş-Dünya-Ay, dinamometre, basınç vb.) veya veri analizi konularına denk gelen uygun sorular için MUTLAKA uygun `gorsel_tipi` atanmalıdır (Örn: "dik_ucgen", "eskenar_ucgen", "ikizkenar_ucgen", "benzer_ucgen", "cesitkenar_ucgen", "cember", "gunes_dunya_ay", "dinamometre", "grafik", "basinc"). 
            2. Görsel gerektirmeyen tamamen sözel veya düz mantık sorularda `gorsel_tipi` kesinlikle "yok" olmalıdır.
            3. Görsel içeren sorularda, soruda geçen köşe harfleri (örn. A, B, C, D vb.) ve değerler `etiketler` sözlüğünde eksiksiz olarak tanımlanmalı, soru metni ile görsel uyumlu olmalıdır.
            """

            rastgele_tohum = random.randint(10000, 99999)

            prompt = f"""
Sen MEB müfredatına ve soru hazırlama sistemine tam hakim profesyonel bir yapay zekasısın.
[ÖNEMLİ KURAL - ÇEŞİTLİLİK VE ÖZGÜNLÜK GARANTİSİ]: Her defasında tamamen ÖZGÜN, YARATICI, bir önceki testen FARKLI ve DAHA ÖNCE ÜRETİLMEMİŞ benzersiz rastgele sorular tasarla. Özellikle Bilgi Yarışması, trivia ve genel kültür modüllerinde birbirini tekrar eden klasik sorular yerine az bilinen, şaşırtıcı, güncel ve nitelikli detaylara yer ver. Asla klişe veya birbirinin kopyası sorular üretme. (Üretim Varyasyon Kodu: {rastgele_tohum})

{secili_sinif} seviyesinde, '{sinav_turu}' konseptinde, TOPLAM {soru_sayisi} adet nitelikli, her defansında bir önceki testen tamamen özgün,farklı,birbirini tekrarlamayan soru üret. 

{gorsel_talimati}

Zorluk Seviyesi: {zorluk_seviyesi}
Seçilen Dersler ve Hedef Üniteler (MUTLAKA BU KAPSAMA BAĞLI KAL):
{ders_unite_detay}
{ek_baglam}

Yanıtı kesinlikle ve sadece şu JSON formatında ver (saf JSON dizisi döndür):
[
  {{
    "soru_metni": "Soru metni...",
    "secenekler": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "dogru_cevap": "A",
    "cozum_aciklamasi": "Çözüm açıklaması...",
    "ders": "Kategori/Ders Adı",
    "gorsel_tipi": "dik_ucgen", 
    "etiketler": {{"A": "A", "B": "B", "C": "C", "c": "6 cm", "a": "8 cm"}}
  }}
]
"""
            with st.spinner("🚀 Sorular hazırlanıyor ve görseller işleniyor, lütfen bekleyin..."):
                basarili = False
                raw_data = None
                
                # Paralel asenkron API çağrı yönetimi ile maksimum hızlandırma
                with ThreadPoolExecutor(max_workers=min(len(API_KEYS), 4)) as executor:
                    futures = [executor.submit(api_cagrisi_yap, key, prompt) for key in API_KEYS]
                    for future in futures:
                        res = future.result()
                        if res:
                            raw_data = res
                            break
                            
                if raw_data:
                    questions = kararli_json_ayikla(raw_data)
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
                        basarili = True

                if basarili:
                    st.success("🎉 Sorular başarıyla üretildi! Sınava başlayabilirsiniz.")
                    st.rerun()
                else:
                    st.error("Sorular üretilirken bir hata oluştu. Lütfen tekrar deneyiniz veya API anahtarınızı kontrol ediniz.")

# --- ANA EKRAN / SINAV YÖNETİMİ ---
st.title("🎓 Soru Fabrikası Tablet Sınav Modülü")

if st.session_state.quiz_ready_to_start and not st.session_state.exam_started and not st.session_state.quiz_submitted:
    st.markdown("""
    <div class="custom-card" style="text-align: center;">
        <h2>📋 Sınavınız Hazır!</h2>
        <p style="font-size: 18px; color: #475569;">Sorularınız özenle oluşturuldu. Hazır olduğunuzda aşağıdaki butona basarak sınavı başlatabilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Sınavı Başlat", type="primary", use_container_width=True):
            st.session_state.exam_started = True
            st.session_state.start_time = time.time()
            st.rerun()

elif st.session_state.exam_started and not st.session_state.quiz_submitted:
    quiz_data = st.session_state.quiz_data
    total_q = len(quiz_data)
    curr_idx = st.session_state.current_question
    
    # İlerleme çubuğu ve üst bilgi
    st.progress((curr_idx + 1) / total_q)
    
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        st.markdown(f"**Soru:** {curr_idx + 1} / {total_q}")
    with c2:
        st.markdown(f"**Ders:** {quiz_data[curr_idx].get('ders', 'Genel')}")
    with c3:
        gecen_sure = int(time.time() - st.session_state.start_time)
        dakika = gecen_sure // 60
        saniye = gecen_sure % 60
        st.markdown(f"**⏱️ Süre:** {dakika:02d}:{saniye:02d}")
    
    st.markdown("---")
    
    q = quiz_data[curr_idx]
    
    st.markdown(f"""
    <div class="custom-card">
        <div class="soru-metni-kutusu">{curr_idx + 1}. {q.get('soru_metni', '')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Vektörel Görsel Çizimi
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
                
    selected_opt = st.radio(
        "Cevabınızı Seçiniz:",
        options,
        index=default_idx if default_idx is not None else 0,
        key=f"radio_q_{curr_idx}"
    )
    
    if selected_opt:
        st.session_state.user_answers[curr_idx] = selected_opt[0]
        
    st.markdown("---")
    
    nav_col1, nav_col2, nav_col3 = st.columns([2, 2, 2])
    
    with nav_col1:
        if curr_idx > 0:
            if st.button("⬅️ Önceki Soru", kind="secondary", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()
                
    with nav_col2:
        if curr_idx < total_q - 1:
            if st.button("Sonraki Soru ➡️", kind="secondary", use_container_width=True):
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
        
        durum_renk = "#16a34a" if user_ans == correct_ans else ("#dc2626" if user_ans != "Boş" else "#d97706")
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
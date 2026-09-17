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

# --- VEKTÖREL GÖRSEL ÇİZİCİ ---
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
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=180, transparent=True)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_str}"

# --- MEB MÜFREDATI VE ÖZEL MODÜLLER ---
MUGREDAT = {
    "Bilgi Yarışması": {
        "Kim Milyoner Olmak İster Tarzı Sorular": ["Artan Zorluk ve Ödül Basamakları", "Kültür, Sanat ve Dünya Tarihi", "Az Bilinen Coğrafya ve Doğa Mucizeleri", "Bilim, Uzay ve Nobel Ödüllü Keşifler", "Mitoloji, Edebiyat ve Felsefe Kuramları", "Şaşırtıcı Bilimsel Gerçekler ve Trivia"],
        "Genel Kültür ve Trivia": ["Tarih ve Mitoloji", "Coğrafya ve Dünya", "Bilim ve Teknoloji", "Sanat, Sinema ve Edebiyat"]
    },
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
    soru_sayisi = st.slider("🔢 Soru Sayısı:", 1, 100, 5, key=f"slider_soru_{st.session_state.secim_sifirla_tetikleyici}")

    if st.button("🚀 Soruları Üret", use_container_width=True, type="primary"):
        if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
            st.error("Geçerli bir API anahtarı bulunamadı!")
        elif not secili_ders_unite_haritasi:
            st.error("Lütfen en az bir ders veya ünite seçiniz!")
        else:
            ek_baglam = ""
            if secili_sinif == "Bilgi Yarışması" and any("Kim Milyoner Olmak İster" in u for u_list in secili_ders_unite_haritasi.values() for u in u_list):
                ek_baglam = "Sorular 'Kim Milyoner Olmak İster' yarışma formatına uygun olarak tasarlanmalıdır: Kolaydan zora doğru artan bir zorluk eğrisi izlemeli, şaşırtıcı ve dikkat çekici bilgi detayları içermelidir.\n"
            if sinav_turu == "Yanlışlardan Üretilen Sorular":
                ek_baglam += "Öğrencinin zorlandığı kritik kazanımlardan oluşan pekiştirici sorular üret.\n"
            elif sinav_turu == "Genel Tarama Sınavı":
                ek_baglam += "Seçilen tüm ders ve üniteleri kapsayan dengeli bir genel tarama sınavı olmalıdır.\n"
            elif sinav_turu == "Konu Tarama Sınavı":
                ek_baglam += "Seçilen alt başlıkları ve konuları derinlemesine irdeleyen konu tarama sınavı olmalıdır.\n"
            elif sinav_turu == "LGS Geçmiş Yıllar Çıkmış Sorular":
                ek_baglam += "MEB LGS'de çıkmış gerçek soruların mantığına, zorluk derecesine ve yapısına birebir uygun benzer sorular olmalıdır.\n"
            elif sinav_turu == "Hazır Bulunuşluk Sınavı":
                ek_baglam += "Öğrencinin yeni döneme başlarken bilmesi gereken ön koşul temel kavramları ölçen sınav olmalıdır.\n"
            elif sinav_turu == "Yeni Nesil Sorular":
                ek_baglam += "Günlük yaşam problemleri içeren, grafik, tablo, şema veya görsel yorumlama becerisine dayalı yeni nesil beceri temelli sorular olmalıdır.\n"

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
[ÖNEMLİ KURAL - ÇEŞİTLİLİK VE ÖZGÜNLÜK GARANTİSİ]: Her defasında tamamen ÖZGÜN, YARATICI, FARKLI ve DAHA ÖNCE ÜRETİLMEMİŞ benzersiz sorular tasarla. Özellikle Bilgi Yarışması, trivia ve genel kültür modüllerinde birbirini tekrar eden klasik sorular yerine az bilinen, şaşırtıcı, güncel ve nitelikli detaylara yer ver. Asla klişe veya birbirinin kopyası sorular üretme. (Üretim Varyasyon Kodu: {rastgele_tohum})

{secili_sinif} seviyesinde, '{sinav_turu}' konseptinde, TOPLAM {soru_sayisi} adet nitelikli, tamamen özgün soru üret. 

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
            class WorkerContext:
                def __init__(self):
                    self.quiz_data = []
                    self.basarili = False
                    self.hata_mesaji = None
                    self.api_tamamlandi = False

            ctx = WorkerContext()

            def api_thread_islem():
                try:
                    active_key = api_manager.get_next_key()
                    if not active_key:
                        ctx.hata_mesaji = "API anahtarı bulunamadı."
                        return
                    client = genai.Client(api_key=active_key)
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.7,
                            response_mime_type="application/json"
                        ),
                    )
                    if response.text:
                        parsed_data = kararli_json_ayikla(response.text)
                        if parsed_data and isinstance(parsed_data, list):
                            ctx.quiz_data = parsed_data
                            ctx.basarili = True
                        else:
                            ctx.hata_mesaji = "JSON ayrıştırma hatası oluştu."
                    else:
                        ctx.hata_mesaji = "Modelden boş yanıt döndü."
                except Exception as e:
                    ctx.hata_mesaji = str(e)
                finally:
                    ctx.api_tamamlandi = True

            thread = threading.Thread(target=api_thread_islem)
            thread.start()

            with st.spinner("⏳ Soru Fabrikası özgün soruları titizlikle hazırlıyor, lütfen bekleyin..."):
                while thread.is_alive():
                    time.sleep(0.5)

            if ctx.basarili and ctx.quiz_data:
                st.session_state.quiz_data = ctx.quiz_data
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.quiz_ready_to_start = True
                st.session_state.exam_started = False
                st.session_state.current_question = 0
                soru_sayisini_artir(len(ctx.quiz_data))
                st.success(f"🎉 Başarıyla {len(ctx.quiz_data)} adet özgün soru üretildi!")
                st.rerun()
            else:
                hata = ctx.hata_mesaji or "Bilinmeyen API hatası."
                st.error(f"Soru üretilirken bir hata oluştu: {hata}")

# --- ANA EKRAN VE AKIŞ ---
if not st.session_state.quiz_ready_to_start:
    st.markdown("""
        <div class="custom-card" style="text-align: center; padding: 40px;">
            <h1 style="color: #4f46e5; margin-bottom: 15px;">🎓 Soru Fabrikası Tablet Sınav Modülüne Hoş Geldiniz</h1>
            <p style="font-size: 18px; color: #475569; line-height: 1.6;">
                Sol taraftaki panelden eğitim seviyenizi, sınav türünü ve dilediğiniz dersleri seçerek 
                tamamen özgün, MEB müfredatına uyumlu ve yapay zeka destekli sorular üretebilirsiniz. 
                Hazır olduğunuzda <b>"Soruları Üret"</b> butonuna tıklayarak sınavınıza başlayın!
            </p>
        </div>
    """, unsafe_allow_html=True)
elif st.session_state.quiz_ready_to_start and not st.session_state.exam_started:
    st.markdown("""
        <div class="custom-card" style="text-align: center; padding: 35px;">
            <h2 style="color: #0f172a; margin-bottom: 15px;">📝 Sınavınız Hazır!</h2>
            <p style="font-size: 18px; color: #475569; margin-bottom: 25px;">
                Üretilen soru sayısı: <b>{}</b> adet. Sınav esnasında sorular arasında geçiş yapabilir, 
                cevaplarınızı güncelleyebilir ve sürenizi takip edebilirsiniz.
            </p>
        </div>
    """.format(len(st.session_state.quiz_data)), unsafe_allow_html=True)
    
    col_basla1, col_basla2, col_basla3 = st.columns([1, 2, 1])
    with col_basla2:
        if st.button("🚀 Sınavı Başlat", type="primary", use_container_width=True):
            st.session_state.exam_started = True
            st.session_state.start_time = datetime.now()
            st.session_state.total_duration = len(st.session_state.quiz_data) * 90  # Soru başına 1.5 dakika
            st.rerun()

elif st.session_state.exam_started and not st.session_state.quiz_submitted:
    quiz_list = st.session_state.quiz_data
    total_q = len(quiz_list)
    curr_idx = st.session_state.current_question

    # Zamanlayıcı ve İlerleme Kontrolü
    gecen_sure = (datetime.now() - st.session_state.start_time).seconds
    kalan_sure = max(0, st.session_state.total_duration - gecen_sure)
    
    dakika = kalan_sure // 60
    saniye = kalan_sure % 60

    col_ust1, col_ust2, col_ust3 = st.columns([2, 2, 2])
    with col_ust1:
        st.markdown(f"#### 📊 Soru: **{curr_idx + 1} / {total_q}**")
    with col_ust2:
        st.markdown(f"#### ⏳ Kalan Süre: **{dakika:02d}:{saniye:02d}**")
    with col_ust3:
        if st.button("🏁 Sınavı Bitir ve Değerlendir", type="primary", use_container_width=True):
            st.session_state.quiz_submitted = True
            st.rerun()

    st.progress((curr_idx + 1) / total_q)
    st.markdown("---")

    q_data = quiz_list[curr_idx]
    
    st.markdown(f"""
        <div class="custom-card">
            <span style="background-color: #e0e7ff; color: #4f46e5; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 14px;">
                📚 {q_data.get('ders', 'Genel')}
            </span>
            <p class="soru-metni-kutusu" style="margin-top: 20px;">
                {curr_idx + 1}. {temizle_latex_metin(q_data.get('soru_metni', ''))}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Vektörel Görsel Varsa Çiz
    g_tipi = q_data.get("gorsel_tipi", "yok")
    g_etiketler = q_data.get("etiketler", {})
    if g_tipi and g_tipi.lower() != "yok":
        gorsel_base64 = ciz_vektorel_gorsel(g_tipi, g_etiketler)
        if gorsel_base64:
            st.markdown(f"""
                <div class="gorsel-sema-kutusu">
                    <img src="{gorsel_base64}" style="max-width: 100%; height: auto; border-radius: 8px;" />
                </div>
            """, unsafe_allow_html=True)

    # Seçenekler
    secenekler = q_data.get("secenekler", {})
    secenek_anahtarlari = sorted(list(secenekler.keys()))
    
    mevcut_cevap = st.session_state.user_answers.get(curr_idx, None)
    secilen_index = 0
    if mevcut_cevap in secenek_anahtarlari:
        secilen_index = secenek_anahtarlari.index(mevcut_cevap)

    radyo_secenekleri = [f"{k}) {temizle_latex_metin(secenekler[k])}" for k in secenek_anahtarlari]
    
    secim = st.radio(
        "Lütfen doğru seçeneği işaretleyiniz:",
        options=radyo_secenekleri,
        index=secilen_index,
        key=f"radio_soru_{curr_idx}"
    )

    if secim:
        secilen_harf = secim.split(")")[0].strip()
        st.session_state.user_answers[curr_idx] = secilen_harf

    st.markdown("---")
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    with col_nav1:
        if curr_idx > 0:
            if st.button("⬅️ Önceki Soru", kind="secondary", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()
    with col_nav3:
        if curr_idx < total_q - 1:
            if st.button("Sonraki Soru ➡️", kind="secondary", use_container_width=True):
                st.session_state.current_question += 1
                st.rerun()

elif st.session_state.quiz_submitted:
    quiz_list = st.session_state.quiz_data
    user_ans = st.session_state.user_answers
    
    dogru_sayisi = 0
    yanlis_sayisi = 0
    bos_sayisi = 0

    for idx, q in enumerate(quiz_list):
        u_cevap = user_ans.get(idx, None)
        d_cevap = q.get("dogru_cevap", "").strip().upper()
        if not u_cevap:
            bos_sayisi += 1
        elif u_cevap.strip().upper() == d_cevap:
            dogru_sayisi += 1
        else:
            yanlis_sayisi += 1
            if q not in st.session_state.yanlis_sorular_arsivi:
                st.session_state.yanlis_sorular_arsivi.append(q)

    net_sayisi = dogru_sayisi - (yanlis_sayisi * 0.25)
    basari_orani = (dogru_sayisi / len(quiz_list)) * 100 if quiz_list else 0

    st.markdown("""
        <div class="custom-card" style="text-align: center;">
            <h2>🎯 Sınav Sonuç Raporu</h2>
            <hr style="border: 1px solid #cbd5e1; margin: 20px 0;">
        </div>
    """, unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="✅ Doğru Sayısı", value=dogru_sayisi)
    with col_m2:
        st.metric(label="❌ Yanlış Sayısı", value=yanlis_sayisi)
    with col_m3:
        st.metric(label="⚠️ Boş Sayısı", value=bos_sayisi)
    with col_m4:
        st.metric(label="📈 Başarı Oranı", value=f"%{basari_orani:.1f}")

    st.markdown("---")
    st.markdown("### 📝 Soru Çözüm ve Detay İncelemesi")

    for idx, q in enumerate(quiz_list):
        u_cevap = user_ans.get(idx, "Boş")
        d_cevap = q.get("dogru_cevap", "").strip().upper()
        durum = "✅ Doğru" if u_cevap == d_cevap else ("⚠️ Boş" if u_cevap == "Boş" else "❌ Yanlış")
        
        renk = "#16a34a" if durum.startswith("✅") else ("#ca8a04" if durum.startswith("⚠️") else "#dc2626")

        with st.expander(f"Soru {idx + 1} - [{durum}] ({q.get('ders', 'Genel')})"):
            st.markdown(f"**Soru:** {temizle_latex_metin(q.get('soru_metni', ''))}")
            
            g_tipi = q.get("gorsel_tipi", "yok")
            g_etiketler = q.get("etiketler", {})
            if g_tipi and g_tipi.lower() != "yok":
                gorsel_base64 = ciz_vektorel_gorsel(g_tipi, g_etiketler)
                if gorsel_base64:
                    st.markdown(f"""
                        <div class="gorsel-sema-kutusu">
                            <img src="{gorsel_base64}" style="max-width: 100%; height: auto; border-radius: 8px;" />
                        </div>
                    """, unsafe_allow_html=True)

            secenekler = q.get("secenekler", {})
            for k, val in sorted(secenekler.items()):
                st.markdown(f"- **{k})** {temizle_latex_metin(val)}")
            
            st.markdown(f"**Öğrencinin Cevabı:** <span style='color: {renk}; font-weight: bold;'>{u_cevap}</span>", unsafe_allow_html=True)
            st.markdown(f"**Doğru Cevap:** <span style='color: #16a34a; font-weight: bold;'>{d_cevap}</span>", unsafe_allow_html=True)
            st.markdown(f"**Çözüm Açıklaması:** {temizle_latex_metin(q.get('cozum_aciklamasi', 'Açıklama belirtilmemiş.'))}")

    st.markdown("---")
    col_yenile1, col_yenile2, col_yenile3 = st.columns([1, 2, 1])
    with col_yenile2:
        if st.button("🔄 Yeni Sınav Oluştur / Sıfırla", type="primary", use_container_width=True):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_ready_to_start = False
            st.session_state.exam_started = False
            st.session_state.current_question = 0
            st.session_state.secim_sifirla_tetikleyici += 1
            st.rerun()
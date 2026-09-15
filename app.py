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

# --- GELİŞMİŞ VE DİNAMİK ÜÇGEN / FEN GÖRSEL ÇİZİCİ ---
def ciz_vektorel_gorsel(gorsel_tipi="yok", etiketler=None):
    if not isinstance(etiketler, dict):
        etiketler = {}
        
    fig, ax = plt.subplots(figsize=(4.5, 3.3))
    ax.set_aspect('equal')
    ax.axis('off')
    
    tip = str(gorsel_tipi).lower()
    
    # 1. DÜNYA, GÜNEŞ, AY VE UZAY SİSTEMLERİ
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

    # 2. DİNAMOMETRE VE KUVVET ÖLÇÜM DÜZENEĞİ
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

    # 3. DÜNYA'NIN KATMANLARI
    elif "dunya_katmanlari" in tip:
        k_dis = plt.Circle((3.0, 2.5), 1.9, color='#38bdf8', alpha=0.4, ec='#0284c7', linewidth=2)
        k_manto = plt.Circle((3.0, 2.5), 1.3, color='#f97316', alpha=0.6, ec='#c2410c', linewidth=2)
        k_cekirdek = plt.Circle((3.0, 2.5), 0.6, color='#dc2626', ec='#991b1b', linewidth=2)
        ax.add_patch(k_dis)
        ax.add_patch(k_manto)
        ax.add_patch(k_cekirdek)
        ax.text(3.0, 4.0, etiketler.get("K1", "Atmosfer"), fontsize=8, fontweight='bold', ha='center', color='#0369a1')
        ax.text(3.0, 2.5, etiketler.get("K2", "Çekirdek"), fontsize=8, fontweight='bold', ha='center', color='#ffffff')

    # 4. ÇEMBER VE DAİRE GEOMETRİSİ
    elif "cember" in tip or "daire" in tip:
        cember = plt.Circle((3.0, 2.5), 1.5, color='#0f172a', fill=False, linewidth=2.2)
        ax.add_patch(cember)
        ax.plot(3.0, 2.5, 'ko', markersize=5)
        ax.text(3.1, 2.65, etiketler.get("M", "M"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.plot([3.0, 4.5], [2.5, 2.5], color='#dc2626', linewidth=1.8, linestyle='--')
        ax.text(3.75, 2.7, etiketler.get("r", "r"), fontsize=10, fontweight='bold', color='#dc2626')
        ax.plot([3.0, 1.9], [2.5, 3.5], color='#2563eb', linewidth=1.8)
        ax.text(2.3, 3.1, etiketler.get("aci", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(3.0, 0.4, etiketler.get("Aciklama", "Çember Geometrisi"), fontsize=9, fontweight='bold', ha='center', color='#475569')

    # 5. DİK ÜÇGEN
    elif "dik_ucgen" in tip:
        bx, by = 1.2, 1.0
        cx, cy = 4.8, 1.0
        ax_val, ay_val = 1.2, 4.0
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        ax.plot([1.2, 1.5, 1.5, 1.2], [1.0, 1.0, 1.3, 1.3], color='#0f172a', linewidth=1.5) # Dik açı işareti (90°)
        
        ax.text(ax_val - 0.25, ay_val + 0.1, etiketler.get("A", "A"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, etiketler.get("B", "B"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.15, cy - 0.25, etiketler.get("C", "C"), fontsize=11, fontweight='bold', color='#0f172a')
        
        ax.text(2.0, 2.7, etiketler.get("c", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(3.0, 0.7, etiketler.get("a", ""), fontsize=10, fontweight='bold', color='#dc2626')
        ax.text(1.4, 2.5, etiketler.get("b", ""), fontsize=10, fontweight='bold', color='#16a34a')
        ax.text(1.4, 1.3, etiketler.get("aci", ""), fontsize=9, fontweight='bold', color='#9333ea')
        ax.text(3.0, 0.3, "Dik Üçgen", fontsize=9, fontweight='bold', ha='center', color='#475569')

    # 6. EŞKENAR ÜÇGEN
    elif "eskenar_ucgen" in tip:
        bx, by = 1.5, 1.0
        cx, cy = 4.5, 1.0
        ax_val, ay_val = 3.0, 1.0 + 1.5 * np.sqrt(3)
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        
        ax.text(ax_val, ay_val + 0.15, etiketler.get("A", "A"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, etiketler.get("B", "B"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.25, etiketler.get("C", "C"), fontsize=11, fontweight='bold', color='#0f172a')
        
        ax.text(3.0, 2.2, etiketler.get("aci", "60°"), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(3.0, 0.3, "Eşkenar Üçgen (Tüm kenar ve açılar eşit)", fontsize=9, fontweight='bold', ha='center', color='#475569')

    # 7. İKİZKENAR ÜÇGEN
    elif "ikizkenar_ucgen" in tip:
        bx, by = 1.3, 1.0
        cx, cy = 4.7, 1.0
        ax_val, ay_val = 3.0, 4.2
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        
        ax.text(ax_val, ay_val + 0.15, etiketler.get("A", "A"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, etiketler.get("B", "B"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.25, etiketler.get("C", "C"), fontsize=11, fontweight='bold', color='#0f172a')
        
        ax.text(2.0, 2.8, etiketler.get("kenar1", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(4.0, 2.8, etiketler.get("kenar2", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(3.0, 0.7, etiketler.get("taban", ""), fontsize=10, fontweight='bold', color='#dc2626')
        ax.text(3.0, 0.3, "İkizkenar Üçgen", fontsize=9, fontweight='bold', ha='center', color='#475569')

    # 8. ÇEŞİTKENAR ÜÇGEN
    elif "cesitkenar_ucgen" in tip or "ucgen" in tip:
        bx, by = 1.0, 1.0
        cx, cy = 5.0, 1.2
        ax_val, ay_val = 2.2, 4.0
        ax.plot([bx, cx, ax_val, bx], [by, cy, ay_val, by], color='#0f172a', linewidth=2.2, solid_capstyle='round')
        
        ax.text(ax_val - 0.2, ay_val + 0.15, etiketler.get("A", "A"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(bx - 0.25, by - 0.25, etiketler.get("B", "B"), fontsize=11, fontweight='bold', color='#0f172a')
        ax.text(cx + 0.2, cy - 0.25, etiketler.get("C", "C"), fontsize=11, fontweight='bold', color='#0f172a')
        
        ax.text(1.5, 2.6, etiketler.get("c", ""), fontsize=10, fontweight='bold', color='#2563eb')
        ax.text(3.6, 2.7, etiketler.get("b", ""), fontsize=10, fontweight='bold', color='#16a34a')
        ax.text(3.0, 0.9, etiketler.get("a", ""), fontsize=10, fontweight='bold', color='#dc2626')
        ax.text(3.0, 0.3, "Çeşitkenar Üçgen", fontsize=9, fontweight='bold', ha='center', color='#475569')

    # 9. ISITMA / HAL DEĞİŞTİRME
    elif "isitma_kababi" in tip or "hal_degisimi" in tip:
        ax.plot([2.0, 2.0, 4.0, 4.0], [1.0, 3.5, 3.5, 1.0], color='#0f172a', linewidth=2.2)
        rect = plt.Rectangle((2.05, 1.05), 1.9, 1.6, color='#38bdf8', alpha=0.5)
        ax.add_patch(rect)
        ax.plot([3.0, 3.0], [1.2, 4.3], color='#dc2626', linewidth=2.5)
        circle_term = plt.Circle((3.0, 1.2), 0.16, color='#dc2626', fill=True)
        ax.add_patch(circle_term)
        rect_ocak = plt.Rectangle((1.5, 0.6), 3.0, 0.3, color='#475569', ec='#0f172a', linewidth=1.5)
        ax.add_patch(rect_ocak)
        ax.text(3.3, 3.9, etiketler.get("T", "Termometre"), fontsize=9, fontweight='bold', color='#dc2626')
        ax.text(2.2, 1.9, etiketler.get("S", "Sıvı"), fontsize=9, fontweight='bold', color='#0369a1')

    # 10. BASINÇ
    elif "basinc" in tip:
        rect_blok = plt.Rectangle((1.5, 2.0), 3.0, 1.2, color='#cbd5e1', ec='#0f172a', linewidth=2)
        ax.add_patch(rect_blok)
        ax.arrow(3.0, 4.0, 0.0, -0.8, head_width=0.3, head_length=0.2, fc='#dc2626', ec='#dc2626')
        ax.text(3.0, 4.25, etiketler.get("F", "Kuvvet"), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
        ax.text(3.0, 2.6, etiketler.get("G", "Ağırlık"), fontsize=11, fontweight='bold', ha='center', color='#0f172a')
        ax.text(3.0, 1.4, etiketler.get("S", "Yüzey"), fontsize=9, fontweight='bold', ha='center', color='#475569')

    # 11. ELEKTRİK DEVRELERİ
    elif "devre" in tip or "elektrik" in tip:
        ax.plot([1.2, 4.8, 4.8, 1.2, 1.2], [1.5, 1.5, 3.6, 3.6, 1.5], color='#0f172a', linewidth=2, linestyle='--')
        circle_ampul = plt.Circle((3.0, 3.6), 0.38, color='#f59e0b', fill=True, ec='#0f172a', linewidth=2)
        ax.add_patch(circle_ampul)
        ax.text(3.0, 3.6, etiketler.get("A", "💡"), fontsize=12, ha='center', va='center')
        ax.text(3.0, 1.15, etiketler.get("P", "Güç Kaynağı"), fontsize=9, fontweight='bold', ha='center', color='#0f172a')
        
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
        "Matematik": ["Çarpanlar ve Katlar", "Kümeler", "Tam Sayılar", "Kesirlerle İşlemler", "Cebirsel İfadeler", "Açılar", "Üçgende Açılar ve Alan", "Çember ve Daire", "Dörtgende Çevre og Alan"],
        "Fen Bilimleri": ["Güneş Sistemi ve Tutulmalar", "Vücudumuzdaki Sistemler", "Kuvvet og Hareket", "Madde ve Isı", "Ses ve Özellikleri"],
        "Sosyal Bilgiler": ["Biz og Toplum", "Yeryüzünde Yaşam", "Türklerin Tarihsel Yolculuk", "Ussal Ekonomi", "Yönetimimiz ve Demokrasi"],
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
            elif "LGS Çıkmış" in sinav_turu or "LGS Çıkmış Sorular" in secili_ders_unite_haritasi.keys():
                ek_baglam = "Bu sorular MEB tarafından LGS'de sorulmuş gerçek çıkmış soru mantığına ve beceri temelli yapıya birebir uygun olmalıdır.\n"

            ders_unite_detay = ""
            aktif_dersler_listesi = list(secili_ders_unite_haritasi.keys())
            for d, u_list in secili_ders_unite_haritasi.items():
                ders_unite_detay += f"- Ders/Kategori: {d}, Alt Başlıklar: {', '.join(u_list)}\n"

            gorsel_talimati = """
            KESİN ÜÇGEN VE GÖRSEL ÇEŞİTLİLİK KURALLARI (Çok Önemli!):
            Geometri veya üçgen içeren sorularda, soru metninde bahsedilen üçgen türü ile `gorsel_tipi` birebir örtüşmelidir:
            - Eğer soru **dik üçgen** ile ilgiliyse: `gorsel_tipi`: "dik_ucgen" seçilmeli ve etiketler içinde dik açı/kenarlar belirtilmelidir.
            - Eğer soru **eşkenar üçgen** ile ilgiliyse: `gorsel_tipi`: "eskenar_ucgen" seçilmeli (tüm kenarlar eşit görünmelidir).
            - Eğer soru **ikizkenar üçgen** ile ilgiliyse: `gorsel_tipi`: "ikizkenar_ucgen" seçilmeli.
            - Eğer soru **çeşitkenar üçgen** veya genel açı/alan soruları ile ilgiliyse: `gorsel_tipi`: "cesitkenar_ucgen" seçilmelidir.
            - Çember / Daire soruları için: `gorsel_tipi`: "cember"
            - Güneş-Dünya-Ay: `gorsel_tipi`: "gunes_dunya_ay"
            - Dinamometre: `gorsel_tipi`: "dinamometre"
            - Isı / Hal Değişimi: `gorsel_tipi`: "isitma_kababi"
            - Basınç: `gorsel_tipi`: "basinc"
            - Elektrik Devresi: `gorsel_tipi`: "devre"
            - Görsel gerektirmeyen (paragraf, tarih, dil bilgisi vb.): `gorsel_tipi`: "yok"
            """

            prompt = f"""
Sen MEB müfredatına ve LGS sistemine tam hakim profesyonel bir soru hazırlama yapay zekasısın.
{secili_sinif} seviyesinde, {sinav_turu} kapsamında, TOPLAM {soru_sayisi} adet nitelikli ve özgün soru üret. 
Matematik ve geometri sorularında dik üçgen, eşkenar üçgen, ikizkenar üçgen ve çeşitkenar üçgen türlerinin tamamından dengeli ve çeşitlendirilmiş sorular hazırlamaya özen göster.

{gorsel_talimati}

GENEL KURALLAR:
- Derece ifadeleri için LaTeX yerine doğrudan derece sembolü (°) kullan.
- Almanca sorular için dil kurallarına tam uyum sağla.

Zorluk Seviyesi: {zorluk_seviyesi}
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
    "etiketler": {{"A": "A", "B": "B", "C": "C", "a": "8 cm", "b": "6 cm", "c": "10 cm"}}
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
                                    item["gorsel_tipi"] = "yok"
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
                status_placeholder.markdown(f"⏳ **Sorular üretiliyor...** Tahmini kalan süre: **{kalan_tahmin} saniye**")
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
                st.success(f"{len(ctx.quiz_data)} adet üçgen çeşitleriyle uyumlu soru başarıyla üretildi!")
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
        <h2>✨ Sınavınız Hazır!</h2>
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

        mevcut_secim = st.session_state.user_answers.get(curr_idx, None)
        secilen_index = None
        if mevcut_secim in keys_list:
            secilen_index = keys_list.index(mevcut_secim)

        secim = st.radio(
            "Lütfen doğru seçeneği işaretleyiniz:",
            options_list,
            index=secilen_index,
            key=f"radio_q_{curr_idx}"
        )

        if secim:
            secilen_harf = secim.split(")")[0].strip()
            st.session_state.user_answers[curr_idx] = secilen_harf

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])

    with c1:
        if curr_idx > 0:
            if st.button("⬅️ Önceki Soru", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()

    with c3:
        if curr_idx < toplam_soru - 1:
            if st.button("Sonraki Soru ➡️", use_container_width=True, type="primary"):
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("🏁 Sınavı Tamamla ve Bitir", use_container_width=True, type="primary"):
                st.session_state.quiz_submitted = True
                gecen_sure_toplam = int(time.time() - st.session_state.start_time)
                dk = gecen_sure_toplam // 60
                sn = gecen_sure_toplam % 60
                st.session_state.total_duration = f"{dk:02d}:{sn:02d}"
                st.rerun()

else:
    quiz_data = st.session_state.quiz_data
    user_answers = st.session_state.user_answers
    
    dogru_sayisi = 0
    yanlis_sayisi = 0
    bos_sayisi = 0

    yeni_yanlislar = []

    for idx, q in enumerate(quiz_data):
        dogru_harf = str(q.get("dogru_cevap", "")).strip().upper()
        ogrenci_harfi = str(user_answers.get(idx, "")).strip().upper()
        
        if not ogrenci_harfi:
            bos_sayisi += 1
            yeni_yanlislar.append(q)
        elif ogrenci_harfi == dogru_harf:
            dogru_sayisi += 1
        else:
            yanlis_sayisi += 1
            yeni_yanlislar.append(q)

    toplam_s = len(quiz_data)
    basari_orani = (dogru_sayisi / toplam_s) * 100 if toplam_s > 0 else 0

    st.session_state.yanlis_sorular_arsivi.extend(yeni_yanlislar)

    bugun_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    karne_kaydi = {
        "tarih": bugun_str,
        "sinif": f"{dogru_sayisi}D / {yanlis_sayisi}Y / {bos_sayisi}B",
        "dogru": dogru_sayisi,
        "yanlis": yanlis_sayisi,
        "sure": st.session_state.total_duration or "Bilinmiyor"
    }
    if not st.session_state.performance_history or st.session_state.performance_history[-1] != karne_kaydi:
        st.session_state.performance_history.append(karne_kaydi)

    st.markdown(f"""
    <div class="custom-card">
        <h2>📊 Sınav Karnesi ve Değerlendirme Raporu</h2>
        <p style="color: #64748b;">Sınav Süresi: <b>{st.session_state.total_duration}</b> | Tamamlama Tarihi: <b>{bugun_str}</b></p>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="✅ Doğru Sayısı", value=str(dogru_sayisi))
    with m2:
        st.metric(label="❌ Yanlış Sayısı", value=str(yanlis_sayisi))
    with m3:
        st.metric(label="⚠️ Boş Sayısı", value=str(bos_sayisi))
    with m4:
        st.metric(label="🎯 Başarı Puanı", value=f"%{basari_orani:.1f}")

    st.markdown("---")
    st.subheader("📝 Soru Soru Çözüm Analizi ve Açıklamalar")

    for idx, q in enumerate(quiz_data):
        dogru_harf = str(q.get("dogru_cevap", "")).strip().upper()
        ogrenci_harfi = str(user_answers.get(idx, "Boş")).strip().upper()
        durum_ikonu = "✅" if ogrenci_harfi == dogru_harf else "❌"

        with st.container(border=True):
            st.markdown(f"**Soru {idx + 1}** ({q.get('ders', 'Genel')}) {durum_ikonu}")
            st.markdown(f"**Soru Metni:** {temizle_latex_metin(q.get('soru_metni', ''))}")
            
            secenekler = q.get("secenekler", {})
            for k in sorted(secenekler.keys()):
                sec_metin = temizle_latex_metin(secenekler[k])
                isaret = ""
                if k == dogru_harf:
                    isaret = " ⭐ **(Doğru Cevap)**"
                elif k == ogrenci_harfi:
                    isaret = " 👈 **(Senin Cevabın)**"
                st.markdown(f"- **{k})** {sec_metin}{isaret}")

            st.markdown(f"💡 **Çözüm Açıklaması:** {temizle_latex_metin(q.get('cozum_aciklamasi', 'Açıklama bulunmuyor.'))}")

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("🔄 Yeni Sınav Oluştur / Sıfırla", use_container_width=True, type="primary"):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.exam_started = False
            st.session_state.start_time = None
            st.rerun()

    with c_btn2:
        if yeni_yanlislar:
            if st.button("❌ Yanlış Yapılan Sorularla Pratik Yap", use_container_width=True):
                st.session_state.quiz_data = yeni_yanlislar
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.exam_started = False
                st.session_state.start_time = None
                st.session_state.current_question = 0
                st.rerun()
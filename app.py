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
import html
import numpy as np

# --- RENDER / SAYFA AYARI ---
st.set_page_config(
    page_title="Soru Fabrikası Tablet Sınav Modülü",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN ARAYÜZ TASARIMI (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --ac1: #6366f1;
        --ac2: #8b5cf6;
        --ink: #0f172a;
        --ink2: #334155;
        --muted: #64748b;
        --line: #e2e8f0;
    }

    html, body, .stApp, .stMarkdown, .stButton button, label, p, input, textarea {
        font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    .stApp {
        background:
            radial-gradient(900px 480px at 100% -5%, rgba(99,102,241,.14), transparent 60%),
            radial-gradient(800px 460px at -5% 105%, rgba(236,72,153,.10), transparent 55%),
            #f8fafc;
    }
    header[data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1080px; }
    h1, h2, h3, h4, h5, h6 { color: var(--ink); letter-spacing: -0.02em; font-weight: 800; }

    /* ---------- KARŞILAMA / HAZIR EKRANI ---------- */
    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #db2777 130%);
        color: #fff; border-radius: 28px; padding: 44px 40px;
        box-shadow: 0 24px 50px -20px rgba(79,70,229,.55);
        position: relative; overflow: hidden;
    }
    .hero::after {
        content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px;
        border-radius: 50%; background: rgba(255,255,255,.12);
    }
    .hero h1 { color: #fff !important; font-size: 34px; margin: 0 0 10px 0; }
    .hero p { color: rgba(255,255,255,.9); font-size: 17px; margin: 0; max-width: 640px; line-height: 1.6; }
    .hero.orta { text-align: center; }
    .hero.orta p { margin: 0 auto; }
    .hero-chipler { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 24px; position: relative; z-index: 1; }
    .hero-chip { background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.32); border-radius: 18px; padding: 12px 24px; }
    .hero-chip b { display: block; font-size: 26px; }
    .hero-chip span { font-size: 13px; opacity: .92; }
    .ozellik-izgara { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 20px; }
    .ozellik { background: #fff; border: 1px solid var(--line); border-radius: 20px; padding: 20px; box-shadow: 0 8px 24px -14px rgba(15,23,42,.25); }
    .ozellik .ikon { font-size: 28px; }
    .ozellik b { display: block; margin: 8px 0 4px; color: var(--ink); font-size: 16px; }
    .ozellik span { color: var(--muted); font-size: 14px; line-height: 1.55; }

    /* ---------- SINAV EKRANI ---------- */
    .ust-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
    .soru-no { font-size: 24px; font-weight: 800; color: var(--ink); }
    .soru-no small { font-size: 16px; color: var(--muted); font-weight: 600; }
    .sure {
        display: inline-flex; align-items: center; gap: 8px; padding: 9px 20px; border-radius: 999px;
        background: #fff7ed; border: 1.5px solid #fdba74; color: #c2410c; font-weight: 800; font-size: 18px;
    }
    .sure.az { background: #fef2f2; border-color: #fca5a5; color: #b91c1c; }
    .ilerleme-cubuk { height: 10px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
    .ilerleme-cubuk > div { height: 100%; background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899); border-radius: 999px; transition: width .3s; }
    .nokta-sira { display: flex; gap: 8px; flex-wrap: wrap; margin: 14px 0 6px; }
    .nokta {
        width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center;
        border-radius: 11px; background: #fff; border: 1.5px solid var(--line); color: var(--muted); font-weight: 700; font-size: 13px;
    }
    .nokta.cevapli { background: linear-gradient(135deg, #6366f1, #8b5cf6); border-color: transparent; color: #fff; }
    .nokta.aktif { border-color: #f97316; box-shadow: 0 0 0 3px rgba(249,115,22,.28); }
    .nokta.aktif:not(.cevapli) { color: #c2410c; background: #fff7ed; }
    .cevap-ozet { color: var(--muted); font-size: 14px; font-weight: 600; margin: 4px 0 18px; }

    .soru-karti {
        background: #fff; border: 1px solid var(--line); border-radius: 26px; padding: 28px 32px 26px 36px;
        box-shadow: 0 18px 40px -22px rgba(79,70,229,.35); margin-bottom: 18px; position: relative;
    }
    .soru-karti::before {
        content: ""; position: absolute; left: 0; top: 26px; bottom: 26px; width: 5px; border-radius: 0 6px 6px 0;
        background: linear-gradient(180deg, var(--ac1), var(--ac2));
    }
    .rozet { display: inline-block; padding: 5px 14px; border-radius: 999px; background: #eef2ff; color: #4338ca; font-weight: 700; font-size: 13px; margin-bottom: 14px; }
    .soru-metni-kutusu { font-size: 21px; font-weight: 600; color: var(--ink); line-height: 1.65; text-align: left; }
    .gorsel-sema-kutusu { background: #f8fafc; border: 1.5px dashed #cbd5e1; border-radius: 18px; padding: 14px; text-align: center; margin: 18px auto 4px auto; max-width: 100%; }
    .alt-baslik { font-size: 13px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 6px 0 10px; }

    /* Şıklar: seçilince kart boyanır */
    div[data-testid="stRadio"] div[role="radiogroup"] { gap: 10px; }
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background: #fff; border: 2px solid var(--line); border-radius: 16px; padding: 14px 18px;
        width: 100%; cursor: pointer; transition: all .18s ease;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { border-color: #a5b4fc; background: #f5f7ff; }
    div[data-testid="stRadio"] label[data-baseweb="radio"] p { font-size: 18px !important; font-weight: 600 !important; color: var(--ink) !important; margin: 0; }
    @supports selector(:has(*)) {
        div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
            border-color: #6366f1; background: linear-gradient(135deg, #eef2ff, #f5f3ff);
            box-shadow: 0 10px 22px -12px rgba(99,102,241,.6);
        }
        div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p { color: #3730a3 !important; font-weight: 700 !important; }
    }

    /* ---------- BUTONLAR ---------- */
    div.stButton > button { border-radius: 14px; font-weight: 700; transition: all .2s ease-in-out; border: none; }
    div.stButton > button:hover { transform: translateY(-2px); }
    div.stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #fb923c 0%, #ea580c 100%) !important; color: #fff !important;
        padding: 0.75rem 1.5rem !important; font-size: 18px !important; font-weight: 700 !important;
        box-shadow: 0 10px 20px -8px rgba(249,115,22,.55);
    }
    div.stButton > button[kind="secondary"]:hover { box-shadow: 0 14px 24px -8px rgba(234,88,12,.7); }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important; color: #fff !important;
        padding: 0.85rem 2rem; font-size: 18px !important; font-weight: 700 !important; letter-spacing: .3px;
        box-shadow: 0 12px 24px -10px rgba(124,58,237,.6); border-radius: 14px !important;
    }
    div.stButton > button[kind="primary"]:hover { box-shadow: 0 16px 28px -10px rgba(124,58,237,.75); }

    /* ---------- SONUÇ EKRANI ---------- */
    .skor-banner {
        display: flex; flex-wrap: wrap; align-items: center; gap: 28px;
        background: linear-gradient(135deg, #4f46e5, #7c3aed 60%, #db2777); border-radius: 28px;
        padding: 30px 34px; color: #fff; box-shadow: 0 24px 50px -22px rgba(79,70,229,.6); margin-bottom: 20px;
    }
    .skor-puan { font-size: 60px; font-weight: 800; line-height: 1; }
    .skor-puan small { font-size: 20px; opacity: .8; font-weight: 600; }
    .skor-mesaj { font-size: 20px; font-weight: 700; margin-top: 6px; }
    .skor-chipler { display: flex; gap: 12px; margin-left: auto; flex-wrap: wrap; }
    .chip { background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.3); border-radius: 18px; padding: 12px 22px; text-align: center; min-width: 90px; }
    .chip b { display: block; font-size: 26px; }
    .chip span { font-size: 12px; opacity: .92; }
    .sik { padding: 10px 14px; border-radius: 12px; border: 1.5px solid var(--line); margin: 6px 0; background: #fff; font-size: 16px; color: var(--ink2); }
    .sik.dogru { background: #f0fdf4; border-color: #86efac; color: #166534; font-weight: 700; }
    .sik.yanlis { background: #fef2f2; border-color: #fca5a5; color: #991b1b; font-weight: 700; }
    .sik span { float: right; font-size: 12px; font-weight: 700; }
    .cozum { background: #fffbeb; border: 1px solid #fde68a; border-radius: 14px; padding: 12px 16px; color: #78350f; margin-top: 12px; line-height: 1.6; }

    /* ---------- ÜRETİM KARTI ---------- */
    .uretim-karti { background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 18px; text-align: center; box-shadow: 0 8px 24px -14px rgba(15,23,42,.3); margin-bottom: 16px; }
    .uretim-karti h4 { color: #4f46e5; margin: 10px 0 4px; font-size: 15px; }
    .uretim-karti p { color: var(--ink2); font-size: 13px; margin: 0; }
    .uretim-sure { color: #ea580c; font-weight: 700; font-size: 14px; margin-top: 8px; }
    .uretim-sure span { color: var(--muted); font-weight: 500; font-size: 12px; }
    .yukleniyor { width: 34px; height: 34px; margin: 0 auto; border-radius: 50%; border: 4px solid #e0e7ff; border-top-color: #6366f1; animation: don 0.9s linear infinite; }
    @keyframes don { to { transform: rotate(360deg); } }

    /* ---------- METRİK / GENEL KARTLAR ---------- */
    div[data-testid="stMetric"] {
        background: #fff; border: 1px solid var(--line); padding: 14px 16px; border-radius: 16px;
        box-shadow: 0 6px 18px -12px rgba(15,23,42,.3); border-left: 5px solid var(--ac1);
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #4f46e5 !important; font-weight: 800; }
    [data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 16px !important; background: #fff !important; overflow: hidden; }
    [data-testid="stExpander"] summary { font-weight: 700; }

    /* ---------- KENAR ÇUBUĞU ---------- */
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); border-right: 1px solid var(--line); }
    .marka { display: flex; align-items: center; gap: 12px; padding: 4px 2px 2px; }
    .marka-logo {
        width: 44px; height: 44px; border-radius: 14px; background: linear-gradient(135deg, #6366f1, #8b5cf6);
        display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 10px 20px -8px rgba(99,102,241,.7);
    }
    .marka b { font-size: 17px; color: var(--ink); display: block; line-height: 1.2; }
    .marka span { font-size: 12px; color: var(--muted); }
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div { border-radius: 12px; border-color: var(--line); background: #f8fafc; }
    section[data-testid="stSidebar"] [data-testid="stExpander"] { box-shadow: 0 6px 16px -12px rgba(15,23,42,.35); margin-bottom: 10px; }

    /* ---------- SEÇİM KUTULARI (ders / ünite): tik yok, seçilince boya ile dolar ---------- */
    div[data-testid="stCheckbox"] { background: #f8fafc; border: 1.5px solid var(--line); border-radius: 14px; padding: 9px 12px; margin-bottom: 7px; transition: all .18s ease; }
    div[data-testid="stCheckbox"]:hover { border-color: #a5b4fc; background: #f5f7ff; }
    div[data-testid="stCheckbox"] label { width: 100%; cursor: pointer; align-items: center; }
    div[data-testid="stCheckbox"] label p { font-size: 14px !important; font-weight: 600 !important; color: #1e293b !important; margin: 0; }
    div[data-testid="stCheckbox"] svg { display: none !important; }
    @supports selector(:has(*)) {
        div[data-testid="stCheckbox"]:has(input:checked) {
            background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%); border-color: #6366f1;
            box-shadow: 0 8px 18px -10px rgba(99,102,241,.6);
        }
        div[data-testid="stCheckbox"]:has(input:checked) label p { color: #4338ca !important; }
        div[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > span:first-child {
            width: 22px !important; height: 22px !important; border-radius: 8px !important;
            border: 2px solid #cbd5e1 !important; background: #ffffff !important; background-image: none !important;
            box-shadow: none !important; transition: all .18s ease;
        }
        div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > span:first-child {
            background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; border-color: transparent !important;
            box-shadow: 0 5px 12px -3px rgba(99,102,241,.65) !important;
        }
        div[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > span:first-child svg,
        div[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > span:first-child::before,
        div[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > span:first-child::after {
            display: none !important; content: none !important;
        }
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

# --- GÜNEŞ-DÜNYA-AY / AY EVRELERİ ÇİZİCİ ---
# (anahtar, Türkçe ad, konum harfi, evre açısı derece)  0=Yeni Ay, 90=İlk Dördün, 180=Dolunay, 270=Son Dördün
EVRELER = [
    ("yeni_ay", "Yeni Ay", "A", 0),
    ("ilk_hilal", "İlk Hilal", "B", 45),
    ("ilk_dordun", "İlk Dördün", "C", 90),
    ("sisman_buyuyen", "Şişkin Ay (büyüyen)", "D", 135),
    ("dolunay", "Dolunay", "E", 180),
    ("sisman_kuculen", "Şişkin Ay (küçülen)", "F", 225),
    ("son_dordun", "Son Dördün", "G", 270),
    ("son_hilal", "Son Hilal", "H", 315),
]
_AD = {k: a for k, a, _, _ in EVRELER}
_AC = {k: p for k, _, _, p in EVRELER}


def _norm(s):
    s = str(s).replace("İ", "i").replace("I", "i").lower()
    for a, b in zip("çğıöşü", "cgiosu"):
        s = s.replace(a, b)
    return s.replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "")


def evre_bul(*metinler):
    """Verilen metinlerden (evre etiketi, görsel tipi...) Ay evresi anahtarını bulur."""
    for m in metinler:
        s = _norm(m or "")
        if not s:
            continue
        if "yeni" in s:
            return "yeni_ay"
        if "dolunay" in s or "dolu_ay" in s:
            return "dolunay"
        if "ilk_dordun" in s or "ilkdordun" in s:
            return "ilk_dordun"
        if "son_dordun" in s or "sondordun" in s:
            return "son_dordun"
        if "sisman" in s:
            return "sisman_kuculen" if ("kuculen" in s or "son" in s) else "sisman_buyuyen"
        if "hilal" in s:
            return "son_hilal" if ("kuculen" in s or "son" in s) else "ilk_hilal"
    return None


def _ay_diski(ax, cx, cy, r, p_deg, zorder=3):
    """Dünya'dan görünen Ay diski: karanlık daire + aydınlık kısım (terminatör eğrisiyle)."""
    ax.add_patch(plt.Circle((cx, cy), r, facecolor="#334155", edgecolor="#0f172a",
                            linewidth=1.6, zorder=zorder))
    p = np.radians(p_deg % 360)
    sign = 1.0 if p <= np.pi else -1.0          # büyüyen: sağ, küçülen: sol
    pp = p if p <= np.pi else 2 * np.pi - p
    if pp > 1e-6:
        t = np.linspace(-np.pi / 2, np.pi / 2, 80)
        limb_x, ys = r * np.cos(t), r * np.sin(t)
        term_x = r * np.cos(pp) * np.cos(t)
        xs = np.concatenate([limb_x, term_x[::-1]])
        yy = np.concatenate([ys, ys[::-1]])
        ax.fill(cx + sign * xs, cy + yy, color="#fde68a", zorder=zorder + 1, linewidth=0)
    ax.add_patch(plt.Circle((cx, cy), r, fill=False, edgecolor="#0f172a",
                            linewidth=1.6, zorder=zorder + 2))


def ay_evreleri_ciz(ax, etiketler=None, gorsel_tipi=""):
    """ax üzerine 0-6 x 0-5 koordinatlarında çizer. Sorudaki evre 'evre' etiketinden gelir."""
    etiketler = etiketler if isinstance(etiketler, dict) else {}
    hedef = evre_bul(etiketler.get("evre"), gorsel_tipi)
    adlari_goster = _norm(etiketler.get("etiket_goster", "hayir")) in ("evet", "true", "1", "goster")
    vurgula = str(etiketler.get("vurgula", "")).strip().upper()
    gorunum = _norm(etiketler.get("gorunum_goster", "hayir")) in ("evet", "true", "1")

    # Yalnızca Dünya'dan görünen evre isteniyorsa
    if _norm(etiketler.get("gosterim", "")) == "sadece_evre" and hedef:
        _ay_diski(ax, 3.0, 2.6, 1.5, _AC[hedef])
        if adlari_goster:
            ax.text(3.0, 0.5, _AD[hedef], fontsize=11, fontweight="bold", ha="center", color="#0f172a")
        return

    gx, gy = 0.3, 2.5             # Güneş
    ex, ey, R = 2.85, 2.5, 1.3    # Dünya merkezi ve yörünge yarıçapı

    # Güneş ışınları (soldan, paralel)
    ax.add_patch(plt.Circle((gx, gy), 0.3, color="#f59e0b", ec="#d97706", linewidth=2, zorder=2))
    ax.text(gx, gy, etiketler.get("G", "Güneş"), fontsize=5, fontweight="bold",
            ha="center", va="center", color="#ffffff", zorder=3)
    for yr in (1.9, 2.25, 2.75, 3.1):
        ax.annotate("", xy=(1.0, yr), xytext=(0.65, yr),
                    arrowprops=dict(arrowstyle="->", color="#f59e0b", lw=1.5))

    # Yörünge ve Dünya
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(ex + R * np.cos(th), ey + R * np.sin(th), color="#94a3b8", linestyle="--", linewidth=1)
    ax.add_patch(plt.Circle((ex, ey), 0.4, color="#38bdf8", ec="#0284c7", linewidth=2, zorder=2))
    ax.text(ex, ey, etiketler.get("D", "Dünya"), fontsize=6, fontweight="bold",
            ha="center", va="center", color="#0f172a", zorder=3)

    # 8 Ay konumu: Yeni Ay Güneş tarafında, saat yönünün tersine ilerler
    for key, ad, harf, p in EVRELER:
        ang = np.radians(180 + p)
        mx, my = ex + R * np.cos(ang), ey + R * np.sin(ang)
        rm = 0.19
        vurgulu = bool(vurgula) and (harf == vurgula)
        if vurgulu:
            ax.add_patch(plt.Circle((mx, my), rm + 0.1, fill=False, edgecolor="#f97316",
                                    linewidth=2.2, zorder=4))
        # Güneş'e bakan (sol) yarı aydınlık
        ax.add_patch(plt.Circle((mx, my), rm, facecolor="#334155", edgecolor="#0f172a",
                                linewidth=1.2, zorder=5))
        ax.add_patch(matplotlib_wedge(mx, my, rm))
        lx, ly = ex + (R + 0.45) * np.cos(ang), ey + (R + 0.45) * np.sin(ang)
        yazi = f"{harf}\n{ad}" if adlari_goster else harf
        ax.text(lx, ly, yazi, fontsize=5 if adlari_goster else 9, fontweight="bold",
                ha="center", va="center", color="#0f172a", zorder=6)

    # Dünya'dan görünüş (soru hangi evreyi soruyorsa o)
    if hedef and gorunum:
        _ay_diski(ax, 5.45, 2.5, 0.55, _AC[hedef])
        ax.text(5.45, 3.35, "Dünya'dan\ngörünüş", fontsize=6, fontweight="bold",
                ha="center", color="#475569")
        if adlari_goster:
            ax.text(5.45, 1.65, _AD[hedef], fontsize=7, fontweight="bold", ha="center", color="#0f172a")


def matplotlib_wedge(mx, my, rm):
    from matplotlib.patches import Wedge
    return Wedge((mx, my), rm, 90, 270, facecolor="#fde68a", edgecolor="#0f172a",
                 linewidth=1.0, zorder=6)

# --- GÖRSEL YARDIMCILARI (SORUDAKİ VERİYLE BİREBİR UYUMLU ÇİZİM) ---
import textwrap
from matplotlib.patches import Rectangle, Arc, Polygon, Wedge, FancyBboxPatch


def _t(x):
    """Etiketi matplotlib için güvenli metne çevirir ($ / LaTeX kalıntılarını temizler)."""
    s = "" if x is None else str(x)
    s = s.replace("^\\circ", "°").replace("\\circ", "°").replace("$", "")
    s = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', s)
    s = s.replace("\\%", "%").replace("\\", "")
    return s.strip()


_OLCU_RE = re.compile(r'\s*(\d+(?:[.,]\d+)?)\s*(?:°|derece|cm|mm|km|m|N|kg|g|br|birim)?\s*', re.I)


def olcu_cek(deger):
    """'6 cm', '40°', 8 -> sayı. Sadece SAF ölçüler (x, 2x gibi cebirsel ifadeler -> None)."""
    if deger is None:
        return None
    if isinstance(deger, (int, float)):
        return float(deger)
    m = _OLCU_RE.fullmatch(str(deger))
    return float(m.group(1).replace(",", ".")) if m else None


def sayi_cek(deger, varsayilan=None):
    if deger is None:
        return varsayilan
    if isinstance(deger, (int, float)):
        return float(deger)
    m = re.search(r'-?\d+(?:[.,]\d+)?', str(deger))
    return float(m.group(0).replace(",", ".")) if m else varsayilan


def liste_cek(deger):
    if deger is None:
        return []
    if isinstance(deger, (list, tuple)):
        return list(deger)
    if isinstance(deger, str):
        ayirici = r'[;|]' if re.search(r'[;|]', deger) else r','
        return [x.strip() for x in re.split(ayirici, deger) if x.strip()]
    return [deger]


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


def _kose_harfleri(et, anahtarlar=("A", "B", "C")):
    if all(k in et for k in anahtarlar):
        return tuple(_t(et[k]) for k in anahtarlar)
    if tuple(anahtarlar) == ("A", "B", "C"):
        return tuple(_t(x) for x in get_custom_labels(et, ("A", "B", "C")))
    return tuple(_t(et.get(k, k)) for k in anahtarlar)


def _kenar_etiketleri(et, onek=("AB", "BC", "CA"), eski=("c", "a", "b")):
    sonuc = {}
    for ad in onek:
        ters = ad[::-1]
        sonuc[ad] = _t(et.get(ad) or et.get(ters) or "")
    if not any(sonuc.values()) and eski:
        for ad, k in zip(onek, eski):
            sonuc[ad] = _t(et.get(k, ""))
    return sonuc


# --- ÜÇGEN GEOMETRİSİ ---
def _geo_kenarlardan(ab, bc, ca):
    if min(ab, bc, ca) <= 0:
        return None
    x = (bc ** 2 + ab ** 2 - ca ** 2) / (2 * bc)
    y2 = ab ** 2 - x ** 2
    if y2 <= 1e-9:
        return None
    return {"A": (x, y2 ** 0.5), "B": (0.0, 0.0), "C": (bc, 0.0)}


def _geo_acilardan(a_d, b_d, c_d):
    if min(a_d, b_d, c_d) <= 0 or abs(a_d + b_d + c_d - 180) > 1.0:
        return None
    A, B, C = np.radians([a_d, b_d, c_d])
    ab = np.sin(C) / np.sin(A)
    return {"A": (ab * np.cos(B), ab * np.sin(B)), "B": (0.0, 0.0), "C": (1.0, 0.0)}


def _acilari_tamamla(a_d, b_d, c_d):
    bil = [a_d, b_d, c_d]
    n = sum(x is not None for x in bil)
    if n == 3:
        return bil
    if n == 2:
        eksik = 180.0 - sum(x for x in bil if x is not None)
        return [eksik if x is None else x for x in bil]
    return None


def _sigdir(P, x0=0.9, x1=5.1, y0=1.0, y1=4.0):
    xs = [p[0] for p in P.values()]
    ys = [p[1] for p in P.values()]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    s = min((x1 - x0) / w, (y1 - y0) / h) if w > 0 and h > 0 else 1.0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mx, my = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return {k: (cx + (p[0] - mx) * s, cy + (p[1] - my) * s) for k, p in P.items()}


def _ucgen_ciz(ax, P, kose=("A", "B", "C"), kenar=None, aci=None, dik=None,
               esit=(), renk="#0f172a", fs=11, kose_anahtar=("A", "B", "C"),
               kenar_adlari=("AB", "BC", "CA")):
    kenar = kenar or {}
    aci = aci or {}
    K = [np.array(P[v], dtype=float) for v in kose_anahtar]
    ax.plot([K[1][0], K[2][0], K[0][0], K[1][0]], [K[1][1], K[2][1], K[0][1], K[1][1]],
            color=renk, linewidth=2.2, solid_capstyle='round', zorder=3)
    mrk = np.mean(K, axis=0)
    isim = dict(zip(kose_anahtar, kose))
    for v, p in zip(kose_anahtar, K):
        d = p - mrk
        n = np.linalg.norm(d) or 1.0
        q = p + d / n * 0.32
        ax.text(q[0], q[1], isim[v], fontsize=fs, fontweight='bold', ha='center', va='center', color=renk, zorder=6)
        if aci.get(v):
            q2 = p - d / n * 0.62
            ax.text(q2[0], q2[1], aci[v], fontsize=fs - 3, fontweight='bold', ha='center', va='center',
                    color="#dc2626", zorder=6)
    ciftler = ((kose_anahtar[0], kose_anahtar[1]), (kose_anahtar[1], kose_anahtar[2]), (kose_anahtar[2], kose_anahtar[0]))
    for (u, w), ad in zip(ciftler, kenar_adlari):
        pu, pw = np.array(P[u], dtype=float), np.array(P[w], dtype=float)
        m = (pu + pw) / 2
        d = m - mrk
        n = np.linalg.norm(d) or 1.0
        if kenar.get(ad):
            q = m + d / n * (0.4 if ad in esit else 0.3)
            ax.text(q[0], q[1], kenar[ad], fontsize=fs - 1, fontweight='bold', ha='center', va='center',
                    color="#2563eb", zorder=6)
        if ad in esit:
            t = pw - pu
            t = t / (np.linalg.norm(t) or 1.0)
            nr = np.array([-t[1], t[0]])
            ax.plot([m[0] - nr[0] * 0.1, m[0] + nr[0] * 0.1], [m[1] - nr[1] * 0.1, m[1] + nr[1] * 0.1],
                    color="#2563eb", linewidth=1.8, zorder=4)
    if dik in kose_anahtar:
        i = kose_anahtar.index(dik)
        v = K[i]
        u1 = K[(i + 1) % 3] - v
        u2 = K[(i + 2) % 3] - v
        u1 /= np.linalg.norm(u1)
        u2 /= np.linalg.norm(u2)
        s = 0.28
        pts = [v + u1 * s, v + (u1 + u2) * s, v + u2 * s]
        ax.plot([pts[0][0], pts[1][0], pts[2][0]], [pts[0][1], pts[1][1], pts[2][1]],
                color=renk, linewidth=1.5, zorder=4)


def _aci_etiketleri(et, kose_anahtar=("A", "B", "C")):
    return {v: _t(et.get(f"aci_{v}") or et.get(f"{v}_aci") or "") for v in kose_anahtar}


def _genel_geometri(et, aci_l):
    """Sayısal kenar/açı verisi varsa gerçek ölçüye göre üçgen kurar; yoksa None."""
    ab, bc, ca = (olcu_cek(et.get(k) or et.get(k[::-1])) for k in ("AB", "BC", "CA"))
    if None not in (ab, bc, ca):
        g = _geo_kenarlardan(ab, bc, ca)
        if g:
            return g
    ac = _acilari_tamamla(*(olcu_cek(aci_l.get(v)) for v in "ABC"))
    if ac:
        return _geo_acilardan(*ac)
    return None


def _ucgen_dik(ax, et):
    kose = _kose_harfleri(et)
    kenar = _kenar_etiketleri(et, eski=("c", "a", "b"))
    ab = olcu_cek(et.get("AB") or et.get("BA"))
    bc = olcu_cek(et.get("BC") or et.get("CB"))
    ca = olcu_cek(et.get("CA") or et.get("AC"))
    if ab and bc is None and ca and ca > ab:
        bc = (ca ** 2 - ab ** 2) ** 0.5
    elif bc and ab is None and ca and ca > bc:
        ab = (ca ** 2 - bc ** 2) ** 0.5
    aci_l = _aci_etiketleri(et)
    if not (ab and bc):
        aA, aC = olcu_cek(aci_l.get("A")), olcu_cek(aci_l.get("C"))
        if aC and 0 < aC < 90:
            bc = bc or 4.0
            ab = bc * np.tan(np.radians(aC))
        elif aA and 0 < aA < 90:
            ab = ab or 3.0
            bc = ab * np.tan(np.radians(aA))
    if not (ab and bc):
        ab, bc = 3.0, 3.6
    oran = min(max(ab / bc, 0.4), 2.5)
    P = _sigdir({"A": (0, oran), "B": (0, 0), "C": (1, 0)})
    _ucgen_ciz(ax, P, kose, kenar, aci_l, dik="B")


def _ucgen_eskenar(ax, et):
    kose = _kose_harfleri(et)
    kenar = _kenar_etiketleri(et, eski=())
    if et.get("kenar") and not any(kenar.values()):
        kenar = {k: _t(et["kenar"]) for k in ("AB", "BC", "CA")}
    aci_l = _aci_etiketleri(et)
    if et.get("aci") and not any(aci_l.values()):
        aci_l = {v: _t(et["aci"]) for v in "ABC"}
    P = _sigdir({"A": (0.5, 3 ** 0.5 / 2), "B": (0, 0), "C": (1, 0)})
    _ucgen_ciz(ax, P, kose, kenar, aci_l, esit=("AB", "BC", "CA"))


def _ucgen_ikizkenar(ax, et):
    kose = _kose_harfleri(et)
    kenar = _kenar_etiketleri(et, eski=())
    if not any(kenar.values()):
        kenar = {"AB": _t(et.get("kenar1", "")), "BC": _t(et.get("taban", "")), "CA": _t(et.get("kenar2", ""))}
    aci_l = _aci_etiketleri(et)
    tepe = olcu_cek(aci_l.get("A"))
    taban = olcu_cek(aci_l.get("B")) or olcu_cek(aci_l.get("C"))
    g = None
    if tepe and 0 < tepe < 180:
        g = _geo_acilardan(tepe, (180 - tepe) / 2, (180 - tepe) / 2)
    elif taban and 0 < taban < 90:
        g = _geo_acilardan(180 - 2 * taban, taban, taban)
    if g is None:
        ab = olcu_cek(et.get("AB") or et.get("CA") or et.get("AC"))
        bc = olcu_cek(et.get("BC"))
        if ab and bc:
            g = _geo_kenarlardan(ab, bc, ab)
    if g is None:
        g = _geo_acilardan(56, 62, 62)
    _ucgen_ciz(ax, _sigdir(g), kose, kenar, aci_l, esit=("AB", "CA"))


def _ucgen_cesitkenar(ax, et):
    kose = _kose_harfleri(et)
    kenar = _kenar_etiketleri(et, eski=("c", "a", "b"))
    aci_l = _aci_etiketleri(et)
    g = _genel_geometri(et, aci_l) or {"A": (2.2, 4.0), "B": (1.0, 1.0), "C": (5.0, 1.2)}
    _ucgen_ciz(ax, _sigdir(g), kose, kenar, aci_l)


def _ucgen_benzer(ax, et):
    duzen = _norm(et.get("duzen", ""))
    kose = _kose_harfleri(et)
    aci_l = _aci_etiketleri(et)
    g = _genel_geometri(et, aci_l) or {"A": (1.0, 2.2), "B": (0.0, 0.0), "C": (1.6, 0.0)}

    if duzen in ("ic_ice", "ice", "paralel", "thales"):
        P = _sigdir(g, 1.0, 5.0, 0.9, 4.0)
        ad, db = olcu_cek(et.get("AD")), olcu_cek(et.get("DB"))
        ae, ec = olcu_cek(et.get("AE")), olcu_cek(et.get("EC"))
        ab_, ac_ = olcu_cek(et.get("AB")), olcu_cek(et.get("CA") or et.get("AC"))
        if ad and db:
            t = ad / (ad + db)
        elif ae and ec:
            t = ae / (ae + ec)
        elif ad and ab_:
            t = ad / ab_
        elif ae and ac_:
            t = ae / ac_
        else:
            t = 0.5
        t = min(max(t, 0.2), 0.8)
        A, B, C = (np.array(P[k]) for k in "ABC")
        D, E = A + t * (B - A), A + t * (C - A)
        _ucgen_ciz(ax, P, kose, {}, aci_l)
        ax.plot([D[0], E[0]], [D[1], E[1]], color="#dc2626", linewidth=2.2, zorder=4)
        ax.plot(*zip(D, E), "o", color="#dc2626", ms=4, zorder=5)
        d_ad, d_ae = _t(et.get("D", "D")), _t(et.get("E", "E"))
        ax.text(D[0] - 0.25, D[1], d_ad, fontsize=10, fontweight='bold', ha='center', va='center', color="#dc2626")
        ax.text(E[0] + 0.25, E[1], d_ae, fontsize=10, fontweight='bold', ha='center', va='center', color="#dc2626")

        def yaz(p, q, anahtarlar, yon, renk="#2563eb"):
            lab = next((_t(et[k]) for k in anahtarlar if et.get(k)), "")
            if lab:
                m = (p + q) / 2
                ax.text(m[0] + yon[0], m[1] + yon[1], lab, fontsize=9, fontweight='bold', ha='center',
                        va='center', color=renk)
        yaz(A, D, ("AD", "DA"), (-0.35, 0.1))
        yaz(D, B, ("DB", "BD"), (-0.35, 0.0))
        yaz(A, E, ("AE", "EA"), (0.35, 0.1))
        yaz(E, C, ("EC", "CE"), (0.35, 0.0))
        yaz(D, E, ("DE", "ED"), (0.0, 0.25), "#dc2626")
        yaz(B, C, ("BC", "CB"), (0.0, -0.3))
        return

    kose2 = (_t(et.get("D", "D")), _t(et.get("E", "E")), _t(et.get("F", "F")))
    kenar1 = _kenar_etiketleri(et, ("AB", "BC", "CA"), eski=())
    k2 = _kenar_etiketleri(et, ("DE", "EF", "FD"), eski=())
    kenar2 = {"AB": k2["DE"], "BC": k2["EF"], "CA": k2["FD"]}
    aci2 = {a: _t(et.get(f"aci_{d}") or "") for a, d in zip("ABC", "DEF")}
    k = None
    for u, w in (("AB", "DE"), ("BC", "EF"), ("CA", "FD")):
        a1 = olcu_cek(et.get(u) or et.get(u[::-1]))
        a2 = olcu_cek(et.get(w) or et.get(w[::-1]))
        if a1 and a2:
            k = a2 / a1
            break
    if k is None:
        k = sayi_cek(et.get("oran"), None)
        if k is None:
            k = 1.6
    k = min(max(k, 0.5), 2.2)
    xs = [p[0] for p in g.values()]
    ys = [p[1] for p in g.values()]
    w0, h0 = max(xs) - min(xs), max(ys) - min(ys)
    s = min((5.2 - 0.9) / ((1 + k) * w0), 3.0 / (h0 * max(1, k)))
    base_y = 1.2

    def yerles(x_sol, olcek):
        return {v: (x_sol + (p[0] - min(xs)) * olcek, base_y + (p[1] - min(ys)) * olcek) for v, p in g.items()}
    P1 = yerles(0.5, s)
    P2 = yerles(0.5 + w0 * s + 0.9, s * k)
    _ucgen_ciz(ax, P1, kose, kenar1, aci_l, renk="#2563eb", fs=10)
    _ucgen_ciz(ax, P2, kose2, kenar2, aci2, renk="#dc2626", fs=10, kenar_adlari=("AB", "BC", "CA"))
    ax.text(0.5 + w0 * s + 0.45, base_y + h0 * s * 0.4, "∼", fontsize=18, fontweight='bold', ha='center', color="#0f172a")


# --- ÇEMBER ---
def _cember_ciz(ax, et):
    cx, cy, R = 3.0, 2.5, 1.6
    ax.add_patch(plt.Circle((cx, cy), R, fill=False, ec='#0f172a', linewidth=2.2, zorder=2))
    ax.plot(cx, cy, 'ko', markersize=4, zorder=5)
    ax.text(cx - 0.1, cy - 0.12, _t(et.get("M", "M")), fontsize=11, fontweight='bold', ha='right', va='top', color='#0f172a')

    def nokta(aci_d, ad, uzak=0.25):
        a = np.radians(aci_d)
        p = (cx + R * np.cos(a), cy + R * np.sin(a))
        ax.plot(*p, 'ko', markersize=4, zorder=5)
        if ad:
            ax.text(cx + (R + uzak) * np.cos(a), cy + (R + uzak) * np.sin(a), ad, fontsize=11,
                    fontweight='bold', ha='center', va='center', color='#0f172a')
        return p

    cap = et.get("cap")
    r_et = et.get("r")
    aci = olcu_cek(et.get("aci"))
    kiris = et.get("kiris")
    yay = et.get("yay")

    if cap:
        p1, p2 = nokta(180, _t(et.get("uc1", "A"))), nokta(0, _t(et.get("uc2", "B")))
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#dc2626', linewidth=1.9, zorder=3)
        ax.text(cx, cy + 0.2, _t(cap), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
    if r_et:
        a = 60 if cap else 0
        p = nokta(a, "", 0)
        ax.plot([cx, p[0]], [cy, p[1]], color='#dc2626', linewidth=1.9, linestyle='--', zorder=3)
        ax.text(cx + (R / 2) * np.cos(np.radians(a)) + 0.05, cy + (R / 2) * np.sin(np.radians(a)) + 0.18,
                _t(r_et), fontsize=10, fontweight='bold', color='#dc2626')
    if aci and 0 < aci < 360:
        a1, a2 = 90 + aci / 2, 90 - aci / 2
        pA, pB = nokta(a1, _t(et.get("A", "A"))), nokta(a2, _t(et.get("B", "B")))
        for p in (pA, pB):
            ax.plot([cx, p[0]], [cy, p[1]], color='#0f172a', linewidth=1.8, zorder=3)
        ax.add_patch(Arc((cx, cy), 1.0, 1.0, theta1=a2, theta2=a1, color='#dc2626', linewidth=2, zorder=4))
        ax.text(cx, cy + 0.72, _t(et.get("aci_etiket", et.get("aci"))), fontsize=9, fontweight='bold',
                ha='center', color='#dc2626')
        if yay:
            ax.add_patch(Arc((cx, cy), 2 * R, 2 * R, theta1=a2, theta2=a1, color='#dc2626', linewidth=3.2, zorder=4))
            ax.text(cx, cy + R + 0.45, _t(yay), fontsize=10, fontweight='bold', ha='center', color='#dc2626')
    if kiris:
        k1, k2 = nokta(215, _t(et.get("k1", "K"))), nokta(325, _t(et.get("k2", "L")))
        ax.plot([k1[0], k2[0]], [k1[1], k2[1]], color='#16a34a', linewidth=2, zorder=3)
        ax.text((k1[0] + k2[0]) / 2, k1[1] + 0.18, _t(kiris), fontsize=10, fontweight='bold', ha='center', color='#16a34a')
    if et.get("baslik"):
        ax.text(3.0, 0.3, _t(et["baslik"]), fontsize=9, fontweight='bold', ha='center', color='#475569')


# --- GRAFİK / TABLO (bağımsız figür: yazılar üst üste binmez) ---
def _sar(metin, genislik=11):
    return textwrap.fill(_t(metin), genislik, break_long_words=False, break_on_hyphens=False)


def _guzel_adim(ust):
    for st_ in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000):
        if ust / st_ <= 10:
            return st_
    return max(ust / 10, 1)


def _fig_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=180, transparent=True, pad_inches=0.12)
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img}"


def _grafik_fig(tip, et):
    kat = [_t(x) for x in liste_cek(et.get("kategoriler") if et.get("kategoriler") is not None else et.get("x_etiketler"))]
    deg = [sayi_cek(x, 0.0) for x in liste_cek(et.get("degerler"))]
    if not deg:
        kat = [_t(et.get(k)) for k in ("X1", "X2", "X3") if et.get(k)]
        deg = [3.0, 5.0, 2.0][:len(kat)] if kat else []
    if not deg:
        kat, deg = ["A", "B", "C"], [3.0, 5.0, 2.0]
    if not kat:
        kat = [str(i + 1) for i in range(len(deg))]
    n = min(len(kat), len(deg), 10)
    kat, deg = kat[:n], deg[:n]
    deg2 = [sayi_cek(x, 0.0) for x in liste_cek(et.get("degerler2"))][:n]
    tur = _norm(et.get("tur", ""))
    if not tur:
        tur = "cizgi" if "cizgi" in tip else ("daire" if ("daire" in tip or "pasta" in tip) else "sutun")
    goster = _norm(et.get("deger_goster", "hayir")) in ("evet", "true", "1")
    baslik = _t(et.get("baslik", ""))
    s1, s2 = _t(et.get("seri1_adi", "")), _t(et.get("seri2_adi", ""))
    PAL = ['#38bdf8', '#f97316', '#a855f7', '#22c55e', '#ef4444', '#eab308', '#14b8a6', '#6366f1', '#ec4899', '#84cc16']

    if tur in ("daire", "pasta"):
        fig, ax = plt.subplots(figsize=(5.4, 3.5), constrained_layout=True)
        ax.set_aspect('equal')
        dilimler, _, *oto = ax.pie(
            [max(d, 0) for d in deg], colors=PAL[:n], startangle=90, counterclock=False,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2},
            autopct=(lambda p: f"{p * sum(deg) / 100:g}") if goster else None, pctdistance=0.72,
            textprops={'fontsize': 10, 'fontweight': 'bold', 'color': '#0f172a'})
        ax.legend(dilimler, [_sar(k, 16) for k in kat], loc='center left', bbox_to_anchor=(1.02, 0.5),
                  frameon=False, fontsize=10, handlelength=1.2)
        if baslik:
            ax.set_title(_sar(baslik, 36), fontsize=11, fontweight='bold', pad=10)
        return _fig_png(fig)

    gen = min(7.4, max(4.6, 0.85 * n + 2.4))
    fig, ax = plt.subplots(figsize=(gen, 3.6), constrained_layout=True)
    ust = max(deg + (deg2 or [0.0]))
    adim = _guzel_adim(ust if ust > 0 else 1)
    ymax = (np.floor(ust / adim) + 1) * adim
    ax.set_ylim(0, ymax)
    ax.set_yticks(np.arange(0, ymax + adim / 2, adim))
    ax.tick_params(axis='y', labelsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='y', color='#e2e8f0', linewidth=0.9)
    xs = np.arange(n)
    if tur == "cizgi":
        ax.plot(xs, deg, marker='o', color='#2563eb', linewidth=2.4, markersize=6, label=s1 or None)
        if deg2:
            ax.plot(xs, deg2, marker='s', color='#f97316', linewidth=2.4, markersize=6, label=s2 or None)
        if goster:
            for x, d in zip(xs, deg):
                ax.annotate(f"{d:g}", (x, d), textcoords="offset points", xytext=(0, 7), ha='center', fontsize=9, fontweight='bold')
        ax.set_xlim(-0.5, n - 0.5)
    else:
        if deg2:
            bw = 0.36
            g = [(ax.bar(xs - bw / 2, deg, bw, color='#38bdf8', ec='#0f172a', linewidth=1.2, label=s1 or None), deg),
                 (ax.bar(xs + bw / 2, deg2, bw, color='#f97316', ec='#0f172a', linewidth=1.2, label=s2 or None), deg2)]
        else:
            g = [(ax.bar(xs, deg, 0.58, color=PAL[:n], ec='#0f172a', linewidth=1.2), deg)]
        if goster:
            for bars, vals in g:
                for b, d in zip(bars, vals):
                    ax.text(b.get_x() + b.get_width() / 2, d + adim * 0.08, f"{d:g}", ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_xticks(xs)
    uzun = max(len(k) for k in kat)
    dondur = 28 if (n > 8 or (n > 6 and uzun > 10)) else 0
    ax.set_xticklabels([_sar(k, 12) for k in kat], fontsize=9.5 if n <= 6 else 8.5,
                       rotation=dondur, ha='right' if dondur else 'center', rotation_mode='anchor')
    if et.get("y_baslik"):
        ax.set_ylabel(_sar(et["y_baslik"], 22), fontsize=9.5, fontweight='bold')
    if et.get("x_baslik"):
        ax.set_xlabel(_sar(et["x_baslik"], 40), fontsize=9.5, fontweight='bold')
    if baslik:
        ax.set_title(_sar(baslik, 44), fontsize=11, fontweight='bold', pad=10)
    if s1 or s2:
        ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=9.5)
    return _fig_png(fig)


def _tablo_fig(et):
    sut = [_t(x) for x in liste_cek(et.get("sutunlar"))]
    sat = et.get("satirlar")
    satirlar = []
    if isinstance(sat, list):
        for r in sat:
            satirlar.append([_t(c) for c in (r if isinstance(r, (list, tuple)) else liste_cek(r))])
    elif isinstance(sat, str):
        satirlar = [[_t(c) for c in liste_cek(r)] for r in re.split(r'[;|]', sat) if r.strip()]
    if not satirlar and et.get("kategoriler") is not None and et.get("degerler") is not None:
        kat, deg = liste_cek(et["kategoriler"]), liste_cek(et["degerler"])
        satirlar = [[_t(k), _t(d)] for k, d in zip(kat, deg)]
        sut = sut or [_t(et.get("kategori_baslik", "Kategori")), _t(et.get("deger_baslik", "Değer"))]
    if not satirlar:
        return None
    satirlar = satirlar[:10]
    m = max(len(r) for r in satirlar + ([sut] if sut else []))
    satirlar = [[_sar(c, 16) for c in (r + [""] * (m - len(r)))] for r in satirlar]
    sut = [_sar(c, 16) for c in (sut + [""] * (m - len(sut)))] if sut else None
    baslik = _t(et.get("baslik", ""))
    satir_say = len(satirlar) + (1 if sut else 0)
    fig, ax = plt.subplots(figsize=(min(7.4, max(3.6, 1.5 * m + 0.8)), 0.55 * satir_say + (0.7 if baslik else 0.25)),
                           constrained_layout=True)
    ax.axis('off')
    tbl = ax.table(cellText=satirlar, colLabels=sut, loc='center', cellLoc='center', bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor('#94a3b8')
        cell.set_linewidth(1.1)
        cell.set_text_props(color='#0f172a')
        if sut and r == 0:
            cell.set_facecolor('#e0e7ff')
            cell.set_text_props(fontweight='bold', color='#312e81')
        elif (r % 2 == 0):
            cell.set_facecolor('#f8fafc')
        if c == 0 and not (sut and r == 0):
            cell.set_text_props(fontweight='bold')
    if baslik:
        ax.set_title(_sar(baslik, 44), fontsize=11, fontweight='bold', pad=8)
    return _fig_png(fig)


def _serbest_ciz(tip, et):
    if "tablo" in tip:
        return _tablo_fig(et)
    return _grafik_fig(tip, et)


# --- DİNAMOMETRE (yeniden tasarım) ---
def _guzel_maks(v):
    for m in (5, 10, 20, 25, 50, 100, 200, 500):
        if v <= m:
            return m
    return float(np.ceil(v / 100) * 100)


def _dinamometre_tek(ax, cx, kuvvet, maks, ad="", yuk="", n=1, deger_yaz=False):
    w = 1.3 if n == 1 else 1.18
    ust, alt = 4.5, 1.9
    kuvvet = min(max(kuvvet, 0.0), maks)
    # asma halkası + gövde
    ax.add_patch(plt.Circle((cx, 4.78), 0.15, fill=False, ec='#475569', linewidth=2.4, zorder=2))
    ax.plot([cx, cx], [4.63, ust], color='#475569', linewidth=2.6, zorder=2)
    ax.add_patch(FancyBboxPatch((cx - w / 2, alt), w, ust - alt, boxstyle="round,pad=0,rounding_size=0.12",
                                fc='#e2e8f0', ec='#0f172a', linewidth=2.2, zorder=2))
    px0, px1 = cx - w / 2 + 0.09, cx + w / 2 - 0.09
    ax.add_patch(Rectangle((px0, alt + 0.1), px1 - px0, ust - alt - 0.2, fc='#ffffff', ec='#94a3b8', linewidth=1.2, zorder=3))
    s0, s1 = ust - 0.32, alt + 0.3

    def yv(v):
        return s0 - (v / maks) * (s0 - s1)
    adim = 1.0 if maks <= 10 else maks / 10.0
    for v in np.arange(0, maks + 1e-9, adim):
        ax.plot([px0, px0 + 0.16], [yv(v), yv(v)], color='#0f172a', linewidth=1.4, zorder=4)
        ax.text(px0 + 0.21, yv(v), f"{v:g}", fontsize=7.5, va='center', ha='left', color='#0f172a', zorder=4)
        if v + adim / 2 <= maks + 1e-9:
            ax.plot([px0, px0 + 0.08], [yv(v + adim / 2)] * 2, color='#0f172a', linewidth=0.9, zorder=4)
    ax.text(px1 - 0.03, ust - 0.2, "N", fontsize=9, fontweight='bold', color='#dc2626', ha='right', va='center', zorder=4)
    # kılavuz yuva
    ax.add_patch(Rectangle((cx - 0.045, yv(maks) - 0.06), 0.09, (yv(0) - yv(maks)) + 0.12, fc='#cbd5e1', ec='none', zorder=3))
    # ibre + çubuk + kanca
    yp = yv(kuvvet)
    ext = 0.1 + 0.3 * (kuvvet / maks)
    uc = alt - ext
    ax.plot([cx, cx], [yp, uc], color='#64748b', linewidth=3, zorder=4, solid_capstyle='butt')
    ax.plot([px0 + 0.02, cx - 0.09], [yp, yp], color='#dc2626', linewidth=1.2, zorder=3.5, alpha=0.9)
    ax.plot([cx - 0.09, px1 - 0.02], [yp, yp], color='#dc2626', linewidth=3.2, zorder=5, solid_capstyle='round')
    ax.add_patch(plt.Circle((cx, uc - 0.08), 0.08, fill=False, ec='#475569', linewidth=2, zorder=4))
    ip_ust = uc - 0.16
    bw, bh = (0.92, 0.6) if n == 1 else (0.8, 0.54)
    ax.plot([cx, cx], [ip_ust, ip_ust - 0.2], color='#475569', linewidth=2, zorder=4)
    wy = ip_ust - 0.2 - bh
    ax.add_patch(Rectangle((cx - bw / 2, wy), bw, bh, fc='#cbd5e1', ec='#0f172a', linewidth=2, zorder=4))
    ax.text(cx, wy + bh / 2, _t(yuk) or "Yük", fontsize=8.5 if n == 1 else 8, fontweight='bold', ha='center', va='center', color='#0f172a', zorder=5)
    if ad:
        ax.text(cx, max(wy - 0.22, 0.2), _t(ad), fontsize=12, fontweight='bold', ha='center', va='center', color='#0f172a')
    if deger_yaz:
        ax.text(cx + w / 2 + 0.1, yp, f"{kuvvet:g} N", fontsize=9, fontweight='bold', color='#dc2626', ha='left', va='center',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#fca5a5', lw=1), zorder=6)


def _dinamometre_ciz(ax, et):
    ham = et.get("kuvvetler") if et.get("kuvvetler") is not None else et.get("kuvvet")
    ks = [sayi_cek(x, 0.0) for x in liste_cek(ham)][:3] or [4.0]
    maks = sayi_cek(et.get("maks"), None) or _guzel_maks(max(ks))
    maks = max(maks, max(ks))
    yukler = liste_cek(et.get("yukler") if et.get("yukler") is not None else et.get("yuk"))
    isimler = liste_cek(et.get("isimler"))
    deger_yaz = _norm(et.get("deger_yaz", "hayir")) in ("evet", "true", "1")
    n = len(ks)
    merkezler = {1: [3.0], 2: [1.9, 4.1], 3: [1.0, 3.0, 5.0]}[n]
    for i, (cx, kv) in enumerate(zip(merkezler, ks)):
        _dinamometre_tek(ax, cx, kv, maks, isimler[i] if i < len(isimler) else "",
                         yukler[i] if i < len(yukler) else "", n=n, deger_yaz=deger_yaz)



def _surtunme_ciz(ax, et):
    kv = sayi_cek(et.get("kuvvet") if et.get("kuvvet") is not None else et.get("kuvvetler"), 3.0)
    maks = max(sayi_cek(et.get("maks"), None) or _guzel_maks(kv), kv)
    zy = 1.4
    ax.plot([0.3, 5.7], [zy, zy], color='#0f172a', linewidth=2.5)
    for x in np.arange(0.4, 5.7, 0.22):
        ax.plot([x, x - 0.14], [zy, zy - 0.14], color='#94a3b8', linewidth=1)
    yuzey = _t(et.get("yuzey", ""))
    if yuzey:
        ax.text(3.0, 0.7, yuzey, fontsize=10, fontweight='bold', ha='center', color='#475569')
    ax.add_patch(Rectangle((0.9, zy), 1.4, 0.95, fc='#cbd5e1', ec='#0f172a', linewidth=2, zorder=3))
    ax.text(1.6, zy + 0.47, _t(et.get("yuk", "Cisim")), fontsize=10, fontweight='bold', ha='center', va='center', zorder=4)
    ay = zy + 0.47
    ax.plot([2.3, 2.75], [ay, ay], color='#475569', linewidth=2.5)
    bx0, bx1 = 2.75, 4.95
    ax.add_patch(Rectangle((bx0, ay - 0.22), bx1 - bx0, 0.44, fc='#f1f5f9', ec='#0f172a', linewidth=2, zorder=3))
    sx0, sx1 = bx0 + 0.18, bx1 - 0.18
    step = 1.0 if maks <= 10 else maks / 10
    for v in np.arange(0, maks + 1e-9, step):
        x = sx0 + (v / maks) * (sx1 - sx0)
        ax.plot([x, x], [ay + 0.22, ay + 0.08], color='#0f172a', linewidth=1.2, zorder=4)
        ax.text(x, ay + 0.3, f"{v:g}", fontsize=6.5, ha='center', va='bottom', zorder=4)
    xp = sx0 + (min(max(kv, 0), maks) / maks) * (sx1 - sx0)
    ax.plot([xp, xp], [ay - 0.2, ay + 0.2], color='#dc2626', linewidth=2.4, zorder=5)
    ax.text((bx0 + bx1) / 2, ay + 0.62, "Kuvvet (N)", fontsize=7.5, fontweight='bold', color='#dc2626', ha='center', va='bottom')
    ax.plot([bx1, bx1 + 0.2], [ay, ay], color='#475569', linewidth=2.5)
    ax.annotate("", xy=(5.75, ay), xytext=(5.15, ay), arrowprops=dict(arrowstyle='->', color='#16a34a', lw=2.2))
    ax.text(5.45, ay + 0.2, "Çekme", fontsize=8, fontweight='bold', color='#16a34a', ha='center')
    if _norm(et.get("surtunme_goster", "evet")) not in ("hayir", "false", "0"):
        ax.annotate("", xy=(0.45, zy + 0.12), xytext=(0.9, zy + 0.12), arrowprops=dict(arrowstyle='->', color='#dc2626', lw=2.2))
        ax.text(0.62, zy + 0.32, "Sürtünme", fontsize=7.5, fontweight='bold', color='#dc2626', ha='center')


# --- BASINÇ ---
def _basinc_kati(ax, et):
    durus = _norm(et.get("durus", "yatay"))
    w, h = (1.0, 2.4) if durus == "dikey" else (2.4, 1.0)
    zemin, cx = 1.3, 3.0
    ax.plot([0.5, 5.5], [zemin, zemin], color='#0f172a', linewidth=2.5)
    for x in np.arange(0.6, 5.5, 0.25):
        ax.plot([x, x - 0.15], [zemin, zemin - 0.15], color='#94a3b8', linewidth=1)
    ax.add_patch(Rectangle((cx - w / 2, zemin), w, h, fc='#cbd5e1', ec='#0f172a', linewidth=2, zorder=3))
    cisim = _t(et.get("cisim", ""))
    if cisim:
        ax.text(cx, zemin + h * 0.78, cisim, fontsize=10, fontweight='bold', ha='center', va='center', zorder=5)
    ax.annotate("", xy=(cx, zemin + 0.04), xytext=(cx, zemin + h * 0.5),
                arrowprops=dict(arrowstyle='->', color='#0f172a', lw=2), zorder=5)
    ax.text(cx + w / 2 + 0.12, zemin + h * 0.3, _t(et.get("G", "G")), fontsize=10, fontweight='bold', ha='left', va='center', zorder=5)
    ax.plot([cx + 0.04, cx + w / 2 + 0.08], [zemin + h * 0.3] * 2, color='#94a3b8', linewidth=0.9, linestyle=':', zorder=4)
    if et.get("F"):
        ax.annotate("", xy=(cx, zemin + h + 0.05), xytext=(cx, zemin + h + 0.95),
                    arrowprops=dict(arrowstyle='->', color='#dc2626', lw=2.4))
        ax.text(cx + 0.12, zemin + h + 0.5, _t(et["F"]), fontsize=10, fontweight='bold', color='#dc2626', ha='left', va='center')
    ax.annotate("", xy=(cx - w / 2, zemin - 0.4), xytext=(cx + w / 2, zemin - 0.4),
                arrowprops=dict(arrowstyle='<->', color='#475569', lw=1.6))
    s_et = _t(et.get("S", ""))
    ax.text(cx, zemin - 0.7, (f"S = {s_et}" if s_et and "=" not in s_et and s_et != "S" else (s_et or "S")),
            fontsize=9, fontweight='bold', ha='center', va='top', color='#475569')


def _basinc_sivi(ax, et):
    y0, yu = 0.9, 4.1
    seviye = 3.5
    noktalar = [_t(x) for x in liste_cek(et.get("noktalar"))]
    n = 1 if noktalar else max(1, min(int(sayi_cek(et.get("kap_sayisi"), 1)), 3))
    genislik = {1: [2.6 if noktalar else 1.8], 2: [1.4, 2.2], 3: [1.1, 1.8, 1.2]}[n]
    merkez = {1: [3.0], 2: [1.9, 4.2], 3: [1.2, 3.0, 4.8]}[n]
    sivi = _t(et.get("sivi_adi", "Su"))
    for cx, w in zip(merkez, genislik):
        ax.add_patch(Rectangle((cx - w / 2, y0), w, seviye - y0, fc='#bae6fd', ec='none', alpha=0.9, zorder=1))
        ax.plot([cx - w / 2, cx - w / 2, cx + w / 2, cx + w / 2], [yu, y0, y0, yu], color='#0f172a', linewidth=2.4, zorder=3)
        ax.plot([cx - w / 2 + 0.03, cx + w / 2 - 0.03], [seviye, seviye], color='#0284c7', linewidth=1.8, zorder=3)
    ax.text(merkez[-1], y0 - 0.3, sivi, fontsize=9, fontweight='bold', ha='center', va='top', color='#0369a1')
    if noktalar:
        der = [sayi_cek(x, i + 1.0) for i, x in enumerate(liste_cek(et.get("derinlikler")))]
        der += [float(i + 1) for i in range(len(der), len(noktalar))]
        dl = liste_cek(et.get("derinlikler"))
        mx = max(der)
        cx, w = merkez[0], genislik[0]
        for i, (ad, d) in enumerate(zip(noktalar, der)):
            y = seviye - (d / mx) * (seviye - y0 - 0.45)
            ax.plot([cx - w / 2, cx], [y, y], color='#475569', linewidth=0.9, linestyle=':', zorder=3)
            ax.plot(cx, y, 'ko', markersize=5, zorder=5)
            ax.text(cx + 0.15, y, ad, fontsize=10, fontweight='bold', va='center', zorder=5)
            if i < len(dl):
                ax.text(cx - w / 2 - 0.1, y, _t(dl[i]), fontsize=8, fontweight='bold', ha='right', va='center', color='#dc2626')
        return
    yp = seviye - 1.4
    for cx, w in zip(merkez, genislik):
        ax.plot(cx, yp, 'ko', markersize=5, zorder=5)
        ax.text(cx + 0.14, yp - 0.02, _t(et.get("P", "P")), fontsize=10, fontweight='bold', va='center', zorder=5)
        ax.annotate("", xy=(cx, yp + 0.05), xytext=(cx, seviye - 0.02), arrowprops=dict(arrowstyle='<->', color='#dc2626', lw=1.8), zorder=5)
        if et.get("h"):
            ax.text(cx - 0.1, (yp + seviye) / 2, _t(et["h"]), fontsize=9, fontweight='bold', color='#dc2626', ha='right', va='center', zorder=5)


# --- EK GÖRSEL TİPLERİ: MEVSİM, DNA, ÇAPRAZLAMA, DİRENÇ, BASİT MAKİNELER ---
import itertools


def _mevsim_ciz(ax, et):
    gx, gy, a, b = 3.0, 2.5, 2.05, 1.4
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(gx + a * np.cos(th), gy + b * np.sin(th), color='#94a3b8', linestyle='--', linewidth=1.2)
    ax.add_patch(plt.Circle((gx, gy), 0.42, color='#f59e0b', ec='#d97706', linewidth=2, zorder=2))
    ax.text(gx, gy, _t(et.get("G", "Güneş")), fontsize=6, fontweight='bold', color='#ffffff', ha='center', va='center', zorder=3)
    # (anahtar, yörünge açısı, tarih, kuzey yarımküre mevsimi) - Dünya saat yönünün tersine döner
    KON = [("haziran", 180, "21 Haziran", "Yaz"), ("eylul", 270, "23 Eylül", "Sonbahar"),
           ("aralik", 0, "21 Aralık", "Kış"), ("mart", 90, "21 Mart", "İlkbahar")]
    harf = {"haziran": "K", "eylul": "L", "aralik": "M", "mart": "N"}
    vurgu = _norm(et.get("vurgula", ""))
    tarih = _norm(et.get("tarih_goster", "hayir")) in ("evet", "true", "1")
    mevsim = _norm(et.get("mevsim_goster", "hayir")) in ("evet", "true", "1")
    tilt = np.radians(23.5)
    ux, uy = np.sin(tilt), np.cos(tilt)
    r = 0.3
    for key, ang, tr, mv in KON:
        t = np.radians(ang)
        ex, ey = gx + a * np.cos(t), gy + b * np.sin(t)
        ad = _t(et.get(key, harf[key]))
        if vurgu == key:
            ax.add_patch(plt.Circle((ex, ey), r + 0.13, fill=False, ec='#f97316', linewidth=2.4, zorder=3))
        ax.add_patch(plt.Circle((ex, ey), r, fc='#1e3a5f', ec='#0f172a', linewidth=1.4, zorder=4))
        gd = np.degrees(np.arctan2(gy - ey, gx - ex))
        ax.add_patch(Wedge((ex, ey), r, gd - 90, gd + 90, fc='#7dd3fc', ec='#0f172a', linewidth=1.0, zorder=5))
        ax.plot([ex - ux * (r + 0.2), ex + ux * (r + 0.2)], [ey - uy * (r + 0.2), ey + uy * (r + 0.2)],
                color='#dc2626', linewidth=1.8, zorder=6)
        ax.plot(ex + ux * (r + 0.2), ey + uy * (r + 0.2), 'o', color='#dc2626', ms=3.5, zorder=7)
        d = np.array([ex - gx, ey - gy])
        d = d / np.linalg.norm(d)
        lx, ly = ex + d[0] * (r + 0.55), ey + d[1] * (r + 0.5)
        metin = ad
        if tarih:
            metin += f"\n{tr}"
        if mevsim:
            metin += f"\n{mv}"
        ax.text(lx, ly, metin, fontsize=9 if metin == ad else 7, fontweight='bold', ha='center', va='center', color='#0f172a', zorder=8)
    ax.text(0.15, 0.2, "Kırmızı çubuk: Dünya'nın eksen eğikliği (kuzey ucu noktalı)", fontsize=5.5, color='#64748b', va='center')


def _dna_ciz(ax, et):
    dizi = re.sub(r'[^ATGC]', '', str(et.get("baz_dizisi", "ATGCCTAG")).upper())[:10] or "ATGCCTAG"
    n = len(dizi)
    comp = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    renk = {'A': '#ef4444', 'T': '#3b82f6', 'G': '#22c55e', 'C': '#f59e0b'}
    gizle = _norm(et.get("gizle", "")) in ("tamamlayici", "ikinci_zincir", "evet")
    xs = np.linspace(0.9, 5.1, n)
    xx = np.linspace(0.5, 5.5, 300)
    dalga = 0.14 * np.sin(2 * np.pi * (xx - 0.5) / 1.7)
    ax.plot(xx, 3.35 + dalga, color='#64748b', linewidth=3.5, solid_capstyle='round', zorder=2)
    ax.plot(xx, 1.65 - dalga, color='#64748b', linewidth=3.5, solid_capstyle='round', zorder=2)
    for x, b in zip(xs, dizi):
        yt = 3.35 + 0.14 * np.sin(2 * np.pi * (x - 0.5) / 1.7)
        yb = 1.65 - 0.14 * np.sin(2 * np.pi * (x - 0.5) / 1.7)
        ym = (yt + yb) / 2
        c2 = comp[b]
        ax.plot([x, x], [yt, ym], color=renk[b], linewidth=3.2, zorder=3)
        ax.plot([x, x], [ym, yb], color='#cbd5e1' if gizle else renk[c2], linewidth=3.2, zorder=3)
        ax.add_patch(plt.Circle((x, yt), 0.17, fc=renk[b], ec='#0f172a', linewidth=1.2, zorder=4))
        ax.text(x, yt, b, fontsize=8, fontweight='bold', color='#ffffff', ha='center', va='center', zorder=5)
        ax.add_patch(plt.Circle((x, yb), 0.17, fc='#e2e8f0' if gizle else renk[c2], ec='#0f172a', linewidth=1.2, zorder=4))
        ax.text(x, yb, "?" if gizle else c2, fontsize=8, fontweight='bold', color='#0f172a' if gizle else '#ffffff',
                ha='center', va='center', zorder=5)
    if et.get("baslik"):
        ax.text(3.0, 0.6, _t(et["baslik"]), fontsize=9, fontweight='bold', ha='center', color='#475569')


def _caprazlama_ciz(ax, et):
    e1 = re.sub(r'[^A-Za-z]', '', str(et.get("ebeveyn1", "Aa")))
    e2 = re.sub(r'[^A-Za-z]', '', str(et.get("ebeveyn2", "Aa")))
    if len(e1) < 2 or len(e1) % 2 or len(e1) != len(e2) or len(e1) > 4:
        e1, e2 = "Aa", "Aa"
    p1 = [e1[i:i + 2] for i in range(0, len(e1), 2)]
    p2 = [e2[i:i + 2] for i in range(0, len(e2), 2)]
    g1 = [''.join(c) for c in itertools.product(*p1)]
    g2 = [''.join(c) for c in itertools.product(*p2)]
    goster = _norm(et.get("hucreleri_goster", "hayir")) in ("evet", "true", "1")
    n1, n2 = len(g2), len(g1)
    cw = min(0.95, 3.6 / n1)
    ch = min(0.7, 2.8 / n2)
    x0, y0 = 1.6, 3.9 - ch
    ax.text(x0 - 0.12, y0 - (n2 * ch) / 2, _t(et.get("ad1", e1)), fontsize=10, fontweight='bold', ha='right', va='center', color='#4f46e5')
    ax.text(x0 + 0.5 + cw * n1 / 2, y0 + ch * 0.6 + 0.12, _t(et.get("ad2", e2)), fontsize=10, fontweight='bold', ha='center', va='bottom', color='#db2777')
    for j, g in enumerate(g2):
        ax.add_patch(Rectangle((x0 + 0.5 + j * cw, y0 + ch * 0.0 + 0.0), cw, ch * 0.6, fc='#fce7f3', ec='#0f172a', linewidth=1.2))
        ax.text(x0 + 0.5 + (j + 0.5) * cw, y0 + ch * 0.3, g, fontsize=8, fontweight='bold', ha='center', va='center')
    top = y0
    for i, g in enumerate(g1):
        yy = top - (i + 1) * ch
        ax.add_patch(Rectangle((x0, yy), 0.5, ch, fc='#e0e7ff', ec='#0f172a', linewidth=1.2))
        ax.text(x0 + 0.25, yy + ch / 2, g, fontsize=8, fontweight='bold', ha='center', va='center')
        for j, h in enumerate(g2):
            gen = []
            for k in range(len(p1)):
                ik = g[k] + h[k]
                gen.append(''.join(sorted(ik, key=lambda c: (c.islower(), c))))
            ax.add_patch(Rectangle((x0 + 0.5 + j * cw, yy), cw, ch, fc='#ffffff', ec='#0f172a', linewidth=1.2))
            ax.text(x0 + 0.5 + (j + 0.5) * cw, yy + ch / 2, ''.join(gen) if goster else "", fontsize=9, fontweight='bold',
                    ha='center', va='center', color='#0f172a')


def _direnc_ciz(ax, et):
    su = _norm(et.get("ortam", "hava")) == "su"
    isim = liste_cek(et.get("isimler")) or ["K", "L"]
    alan = liste_cek(et.get("alanlar")) or ["genis", "dar"]
    n = max(1, min(len(alan), 3))
    isim = (isim + ["K", "L", "M"])[:n]
    sozlu = {"genis": 1.5, "buyuk": 1.5, "orta": 1.0, "dar": 0.6, "kucuk": 0.6}
    ham = []
    for a in alan[:n]:
        v = olcu_cek(a)
        ham.append(v if v is not None else sozlu.get(_norm(a), 1.0))
    mx = max(ham)
    w = [max(0.45, 1.5 * h / mx) if all(olcu_cek(a) is not None for a in alan[:n]) else h for h, a in zip(ham, alan[:n])]
    parasut = _norm(et.get("sekil", "levha")) == "parasut"
    if su:
        ax.add_patch(Rectangle((0.2, 0.3), 5.6, 4.3, fc='#e0f2fe', ec='#38bdf8', linewidth=1.5, zorder=0))
        for y in (1.0, 2.0, 3.0, 4.0):
            xs = np.linspace(0.3, 5.7, 60)
            ax.plot(xs, y + 0.05 * np.sin(xs * 6), color='#7dd3fc', linewidth=1, zorder=0)
    merkez = {1: [3.0], 2: [1.8, 4.2], 3: [1.1, 3.0, 4.9]}[n]
    kg = _norm(et.get("kuvvet_goster", "hayir")) in ("evet", "true", "1")
    for cx, wi, ad in zip(merkez, w, isim):
        yc = 3.0
        if parasut:
            ax.add_patch(Wedge((cx, yc + 0.2), wi / 2 + 0.2, 0, 180, fc='#fbbf24', ec='#0f172a', linewidth=1.8, zorder=3))
            ax.plot([cx - wi / 2 - 0.2, cx], [yc + 0.2, yc - 0.45], color='#0f172a', linewidth=1, zorder=3)
            ax.plot([cx + wi / 2 + 0.2, cx], [yc + 0.2, yc - 0.45], color='#0f172a', linewidth=1, zorder=3)
            ax.add_patch(Rectangle((cx - 0.17, yc - 0.75), 0.34, 0.3, fc='#cbd5e1', ec='#0f172a', linewidth=1.5, zorder=4))
            ymid = yc - 0.3
        else:
            ax.add_patch(Rectangle((cx - wi / 2, yc), wi, 0.16, fc='#cbd5e1', ec='#0f172a', linewidth=1.8, zorder=3))
            ymid = yc + 0.08
        if kg:
            ax.annotate("", xy=(cx, ymid - 1.0), xytext=(cx, ymid), arrowprops=dict(arrowstyle='->', color='#0f172a', lw=2.2), zorder=6)
            ax.text(cx + 0.1, ymid - 0.75, "G", fontsize=9, fontweight='bold', va='center')
            rl = 0.35 + 0.65 * (wi / 1.5)
            ax.annotate("", xy=(cx, ymid + rl + (0.35 if parasut else 0.0)), xytext=(cx, ymid),
                        arrowprops=dict(arrowstyle='->', color='#dc2626', lw=2.2), zorder=6)
            ax.text(cx + 0.1, ymid + rl * 0.5 + (0.2 if parasut else 0.0), "R", fontsize=9, fontweight='bold', color='#dc2626', va='center')
        ax.text(cx, 1.05, ad, fontsize=11, fontweight='bold', ha='center', color='#0f172a', zorder=6)
    ax.text(5.7, 4.5, "Su" if su else "Hava", fontsize=8, fontweight='bold', ha='right', color='#0369a1' if su else '#64748b')


def _kaldirac_ciz(ax, et):
    tur = _norm(et.get("tur", "birinci"))
    ky, yy = olcu_cek(et.get("kuvvet_kolu")), olcu_cek(et.get("yuk_kolu"))
    ky_var, yy_var = ky is not None, yy is not None
    ky, yy = ky or 3.0, yy or 1.0
    if tur.startswith("ucuncu") and not (ky_var and yy_var):
        ky, yy = 2.0, 4.0
    L, x0, yb = 4.4, 0.8, 2.3
    if tur.startswith("ikinci"):
        yy = min(yy, ky * 0.9)
        xf, xl, xk = x0, x0 + L * yy / ky, x0 + L
        kuvvet_yon = "yukari"
    elif tur.startswith("ucuncu"):
        ky = min(ky, yy * 0.9)
        xf, xk, xl = x0, x0 + L * ky / yy, x0 + L
        kuvvet_yon = "yukari"
    else:
        xf, xl, xk = x0 + L * yy / (yy + ky), x0, x0 + L
        kuvvet_yon = "asagi"
    ax.add_patch(Rectangle((x0 - 0.1, yb), L + 0.2, 0.14, fc='#d6a65c', ec='#0f172a', linewidth=2, zorder=3))
    ax.add_patch(Polygon([[xf, yb], [xf - 0.3, yb - 0.6], [xf + 0.3, yb - 0.6]], fc='#94a3b8', ec='#0f172a', linewidth=2, zorder=2))
    ax.plot([xf - 0.7, xf + 0.7], [yb - 0.6, yb - 0.6], color='#0f172a', linewidth=2.5)
    ax.text(xf, yb - 0.85, "Destek", fontsize=7.5, fontweight='bold', ha='center', color='#475569')
    # yük: kirişten sarkan blok
    ax.plot([xl, xl], [yb, yb - 0.55], color='#475569', linewidth=2)
    ax.add_patch(Rectangle((xl - 0.28, yb - 1.15), 0.56, 0.6, fc='#cbd5e1', ec='#0f172a', linewidth=2, zorder=3))
    ax.text(xl, yb - 0.85, _t(et.get("yuk", "Yük")), fontsize=7.5, fontweight='bold', ha='center', va='center', zorder=4)
    kt = _t(et.get("kuvvet", "F"))
    if kuvvet_yon == "asagi":
        ax.annotate("", xy=(xk, yb + 0.14), xytext=(xk, yb + 1.0), arrowprops=dict(arrowstyle='<-', color='#dc2626', lw=2.4), zorder=6)
        ax.text(xk + 0.12, yb + 0.6, kt, fontsize=9, fontweight='bold', color='#dc2626', va='center')
    else:
        ax.annotate("", xy=(xk, yb + 0.16), xytext=(xk, yb - 0.85), arrowprops=dict(arrowstyle='<-', color='#dc2626', lw=2.4), zorder=6)
        ax.text(xk + 0.12, yb - 0.5, kt, fontsize=9, fontweight='bold', color='#dc2626', va='center')

    def kol(xa, xb, y, metin, renk):
        ax.annotate("", xy=(xb, y), xytext=(xa, y), arrowprops=dict(arrowstyle='<->', color=renk, lw=1.4))
        ax.text((xa + xb) / 2, y + 0.12, metin, fontsize=7.5, fontweight='bold', ha='center', color=renk)
    yk_m = _t(et.get("yuk_kolu")) if yy_var else "Yük kolu"
    kk_m = _t(et.get("kuvvet_kolu")) if ky_var else "Kuvvet kolu"
    kol(min(xf, xl), max(xf, xl), 3.5, yk_m, '#475569')
    kol(min(xf, xk), max(xf, xk), 4.0, kk_m, '#dc2626')


def _egik_duzlem_ciz(ax, et):
    uz, yk, tb = olcu_cek(et.get("uzunluk")), olcu_cek(et.get("yukseklik")), olcu_cek(et.get("taban"))
    if uz and yk and uz > yk:
        tb = (uz ** 2 - yk ** 2) ** 0.5
    elif yk and tb and not uz:
        uz = (yk ** 2 + tb ** 2) ** 0.5
    elif uz and tb and tb < uz:
        yk = (uz ** 2 - tb ** 2) ** 0.5
    if not (yk and tb):
        yk, tb = 2.0, 4.0
    s = min(4.2 / tb, 2.7 / yk)
    W, H = tb * s, yk * s
    A = np.array([0.8, 1.0])
    C = np.array([0.8 + W, 1.0])
    D = np.array([0.8 + W, 1.0 + H])
    ax.add_patch(Polygon([A, C, D], fc='#f1f5f9', ec='#0f172a', linewidth=2.2, zorder=2))
    ax.plot([C[0] - 0.25, C[0] - 0.25, C[0]], [C[1], C[1] + 0.25, C[1] + 0.25], color='#0f172a', linewidth=1.4)
    u = (D - A) / np.linalg.norm(D - A)
    nrm = np.array([-u[1], u[0]])
    p = A + u * np.linalg.norm(D - A) * 0.55
    bw, bh = 0.7, 0.45
    blok = [p - u * bw / 2, p + u * bw / 2, p + u * bw / 2 + nrm * bh, p - u * bw / 2 + nrm * bh]
    ax.add_patch(Polygon(blok, fc='#cbd5e1', ec='#0f172a', linewidth=2, zorder=4))
    bc = p + nrm * bh / 2
    ax.annotate("", xy=bc + u * 1.2, xytext=bc, arrowprops=dict(arrowstyle='->', color='#dc2626', lw=2.4), zorder=6)
    ft = bc + u * 1.3 + nrm * 0.15
    ax.text(ft[0], ft[1], _t(et.get("kuvvet", "F")), fontsize=10, fontweight='bold', color='#dc2626', zorder=6)
    ax.annotate("", xy=bc + np.array([0, -0.95]), xytext=bc, arrowprops=dict(arrowstyle='->', color='#0f172a', lw=2.2), zorder=6)
    ax.text(bc[0] + 0.1, bc[1] - 0.75, _t(et.get("yuk", "G")), fontsize=9, fontweight='bold', zorder=6)
    m = (A + D) / 2
    uzt = _t(et.get("uzunluk", ""))
    if uzt:
        m2 = A + u * np.linalg.norm(D - A) * 0.2
        q = m2 + np.array([-u[1], u[0]]) * 0.32
        ax.text(q[0], q[1], uzt, fontsize=9, fontweight='bold', color='#2563eb', ha='center', va='center', rotation=np.degrees(np.arctan2(u[1], u[0])))
    ykt = _t(et.get("yukseklik", ""))
    if ykt:
        ax.text(D[0] + 0.15, (C[1] + D[1]) / 2, ykt, fontsize=9, fontweight='bold', color='#16a34a', va='center')
    tbt = _t(et.get("taban", ""))
    if tbt:
        ax.text((A[0] + C[0]) / 2, A[1] - 0.25, tbt, fontsize=9, fontweight='bold', color='#475569', ha='center')


def _makara_ciz(ax, et):
    tur = _norm(et.get("tur", "sabit"))
    yuk, kt = _t(et.get("yuk", "Yük")), _t(et.get("kuvvet", "F"))
    ax.plot([1.6, 4.4], [4.6, 4.6], color='#0f172a', linewidth=3)
    for x in np.arange(1.7, 4.4, 0.2):
        ax.plot([x, x + 0.12], [4.6, 4.75], color='#94a3b8', linewidth=1)
    r = 0.45
    if tur.startswith("hareketli"):
        pc = (3.0, 2.9)
        ax.plot([2.55, 2.55], [4.6, pc[1]], color='#0f172a', linewidth=1.8)
        th = np.linspace(np.pi, 2 * np.pi, 40)
        ax.plot(pc[0] + r * np.cos(th), pc[1] + r * np.sin(th), color='#0f172a', linewidth=1.8)
        ax.plot([3.45, 3.45], [pc[1], 4.1], color='#0f172a', linewidth=1.8)
        ax.add_patch(plt.Circle(pc, r, fc='#e2e8f0', ec='#0f172a', linewidth=2, alpha=0.9, zorder=3))
        ax.plot(*pc, 'ko', ms=4, zorder=4)
        ax.plot([pc[0], pc[0]], [pc[1], 1.9], color='#475569', linewidth=2)
        ax.add_patch(Rectangle((2.65, 1.2), 0.7, 0.7, fc='#cbd5e1', ec='#0f172a', linewidth=2, zorder=3))
        ax.text(3.0, 1.55, yuk, fontsize=8, fontweight='bold', ha='center', va='center', zorder=4)
        ax.annotate("", xy=(3.45, 4.5), xytext=(3.45, 3.85), arrowprops=dict(arrowstyle='->', color='#dc2626', lw=2.4), zorder=6)
        ax.text(3.6, 4.15, kt, fontsize=10, fontweight='bold', color='#dc2626', va='center')
    else:
        pc = (3.0, 3.7)
        ax.plot([3.0, 3.0], [4.6, pc[1] + r], color='#0f172a', linewidth=2)
        ax.add_patch(plt.Circle(pc, r, fc='#e2e8f0', ec='#0f172a', linewidth=2, alpha=0.9, zorder=3))
        ax.plot(*pc, 'ko', ms=4, zorder=4)
        ax.plot([2.55, 2.55], [pc[1], 1.9], color='#0f172a', linewidth=1.8)
        ax.add_patch(Rectangle((2.2, 1.2), 0.7, 0.7, fc='#cbd5e1', ec='#0f172a', linewidth=2, zorder=3))
        ax.text(2.55, 1.55, yuk, fontsize=8, fontweight='bold', ha='center', va='center', zorder=4)
        ax.plot([3.45, 3.45], [pc[1], 2.5], color='#0f172a', linewidth=1.8)
        ax.annotate("", xy=(3.45, 1.7), xytext=(3.45, 2.5), arrowprops=dict(arrowstyle='->', color='#dc2626', lw=2.4), zorder=6)
        ax.text(3.6, 2.1, kt, fontsize=10, fontweight='bold', color='#dc2626', va='center')


def _disli_ciz(ax, et):
    sayilar = [max(6, min(int(sayi_cek(x, 20)), 60)) for x in liste_cek(et.get("dislerin_sayisi"))][:3] or [20, 40]
    isimler = (liste_cek(et.get("isimler")) + ["K", "L", "M"])[:len(sayilar)]
    yonler = liste_cek(et.get("yonler"))
    dis_goster = _norm(et.get("dis_goster", "evet")) not in ("hayir", "false", "0")
    s = min(0.06, 5.2 / (2 * sum(sayilar)))
    yaricap = [n * s for n in sayilar]
    cx = 0.45 + yaricap[0]
    cy = 2.5
    phi_onceki, n_onceki = None, None
    for i, (n, r, ad) in enumerate(zip(sayilar, yaricap, isimler)):
        adim = 2 * np.pi / n
        if i == 0:
            phi = 0.0
        else:
            frac = ((0 - phi_onceki) / n_onceki) % 1
            tooth = frac < 0.25 or frac > 0.75
            phi = np.pi + adim / 2 if tooth else np.pi
        pts = []
        for k in range(n):
            a0 = phi + k * adim
            for da, rr in ((-0.32, 0.88), (-0.2, 1.1), (0.2, 1.1), (0.32, 0.88)):
                a = a0 + da * adim
                pts.append((cx + r * rr * np.cos(a), cy + r * rr * np.sin(a)))
        renk = ['#93c5fd', '#fdba74', '#86efac'][i % 3]
        ax.add_patch(Polygon(pts, fc=renk, ec='#0f172a', linewidth=1.6, zorder=3))
        ax.add_patch(plt.Circle((cx, cy), r * 0.13, fc='#ffffff', ec='#0f172a', linewidth=1.2, zorder=4))
        fs_ad = 9 if r < 0.7 else 11
        ax.text(cx, cy + r * 0.62, _t(ad), fontsize=fs_ad, fontweight='bold', ha='center', va='center', zorder=5)
        if dis_goster:
            ax.text(cx, cy - r * 0.62, f"{n} diş", fontsize=7 if r < 0.7 else 8, fontweight='bold', ha='center', va='center', zorder=5)
        yon = _norm(yonler[i]) if i < len(yonler) else ("saat" if i == 0 else "")
        if yon in ("saat", "ters"):
            ra = min(0.3, r * 0.3)
            t = np.radians(np.linspace(50, 300, 30)) if yon == "ters" else np.radians(np.linspace(300, 50, 30))
            px, py = cx + ra * np.cos(t), cy + ra * np.sin(t)
            ax.plot(px[:-1], py[:-1], color='#dc2626', linewidth=1.8, zorder=6)
            ax.annotate("", xy=(px[-1], py[-1]), xytext=(px[-3], py[-3]), arrowprops=dict(arrowstyle='->', color='#dc2626', lw=1.8), zorder=6)
        phi_onceki, n_onceki = phi, n
        if i + 1 < len(sayilar):
            cx += r + yaricap[i + 1]


# --- ANA ÇİZİCİ ---
def _ciz_ic(gorsel_tipi, etiketler):
    et = etiketler if isinstance(etiketler, dict) else {}
    tip = _norm(gorsel_tipi)
    if tip in ("yok", "", "none"):
        return None

    if "tablo" in tip or any(k in tip for k in ("grafik", "veri", "histogram", "sutun", "cizgi")):
        if not any(k in tip for k in ("ay_evre", "dinamometre", "surtunme", "basinc")):
            return _serbest_ciz(tip, et)

    fig, ax = plt.subplots(figsize=(4.5, 3.3))
    ax.set_aspect('equal')
    ax.axis('off')

    cizildi = True
    if any(k in tip for k in ("gunes_dunya_ay", "astronomi", "ay_evre", "evre")):
        ay_evreleri_ciz(ax, et, tip)
    elif "surtunme" in tip:
        _surtunme_ciz(ax, et)
    elif "mevsim" in tip:
        _mevsim_ciz(ax, et)
    elif "dna" in tip or "genetik" in tip:
        _dna_ciz(ax, et)
    elif "caprazlama" in tip or "punnett" in tip:
        _caprazlama_ciz(ax, et)
    elif "direnc" in tip:
        _direnc_ciz(ax, et)
    elif "kaldirac" in tip:
        _kaldirac_ciz(ax, et)
    elif "egik" in tip:
        _egik_duzlem_ciz(ax, et)
    elif "makara" in tip:
        _makara_ciz(ax, et)
    elif "disli" in tip:
        _disli_ciz(ax, et)
    elif "dinamometre" in tip or "kuvvet_hareket" in tip:
        _dinamometre_ciz(ax, et)
    elif "basinc" in tip:
        if "sivi" in tip or _norm(et.get("tur", "")) == "sivi" or et.get("sivi_adi") or et.get("noktalar") or et.get("kap_sayisi"):
            _basinc_sivi(ax, et)
        else:
            _basinc_kati(ax, et)
    elif "cember" in tip or "daire" in tip:
        _cember_ciz(ax, et)
    elif "benzer" in tip:
        _ucgen_benzer(ax, et)
    elif "dik_ucgen" in tip:
        _ucgen_dik(ax, et)
    elif "eskenar" in tip:
        _ucgen_eskenar(ax, et)
    elif "ikizkenar" in tip:
        _ucgen_ikizkenar(ax, et)
    elif "ucgen" in tip:
        _ucgen_cesitkenar(ax, et)
    else:
        cizildi = False

    if not cizildi:
        plt.close(fig)
        return None

    ax.set_xlim(-0.1, 6.1)
    ax.set_ylim(0, 5.0)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=180, transparent=True)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_str}"


# --- VEKTÖREL GÖRSEL ÇİZİCİ ---
def ciz_vektorel_gorsel(gorsel_tipi="yok", etiketler=None):
    try:
        return _ciz_ic(gorsel_tipi, etiketler)
    except Exception:
        plt.close('all')
        return None


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
        "Matematik": ["Tümler ve Bütünler açı","Çokgenler Düzgün Çokgenler"," çokgen çeşitleri","çokgenlerde köşegen ve açılar ","Doğru Doğru Parçası Dikme ve Çember","Çember Çap ve yarıçap uzunlukları"],
        "Fen Bilimleri": ["Güneş, Dünya ve Ay","Hava Direnci ve Su Direnci","Kuvvetin Uygulanması ve Sürtünme","Ayın evreleri", "Dinamometre","Sürtünme kuvveti ", "Kuvveti tanıyalım"],
        "Sosyal Bilgiler": ["Birlikte Yaşamak,Birey ve Toplum", "Kültür ve Ortak Mirasımız", "Evimiz Dünya", "Yaşayan Demokrasimiz", "Hayatımızda Ekonomi", "Teknoloji ve Sosyal Bilimler", "Üretim, Dağıtım ve Tüketim"],
        "Din Kültürü": ["Allah İnancı ve İnsan", "Allahın İsimleri ","Hz. Muhammed ve Aile Hayatı", "İslam'ın Temel İbadetleri","Namaz","Kuran Kerim","Peygamber Kıssaları","Mimarimizde dini Motifler", "Ahlaki Değerler"],
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
    "Tubitak-Olimpiyat": {
        "Sonlu Mat(Kombinatorik)": ["Mantık ve Oyunlar", "Sayma, Permütasyon ve Kombinasyon","Palindromik Sayılar","Olasılık"],
        "Analiz-Cebir)": ["Gerçel sayı denklemleri", "Çarpanlara ayırma", "Diziler","Güvercin Yuvası Prensibi (Pigeonhole Principle)", "Eşitsizlikler"],
        "Sayılar ve Sayılar Teorisi (Temel Seviye)": ["Ardışık Sayılar", "Asal Sayılar", "Sayı Basamakları", "Ebob-Ekok"],
        "Geometri ve Görsel Zeka": ["Açılar", "Çevre ve Alan", "Görsel Algı ve Küpler", "Sihirli Kareler ve Sudoku Tarzı Mantık Oyunları"],
        "Problem Çözme Stratejileri": ["Tersten Gitme", "Şema ve Tablo Çizme","Sudoku", "Örüntüler ve Sihirli Diziler"]
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

# --- SEÇİM CALLBACK'LERİ (Tüm kategori -> tüm üniteleri seçer / seçimi kaldırır) ---
def _tumunu_sec(ders_key, unite_keys):
    deger = bool(st.session_state.get(ders_key, False))
    for k in unite_keys:
        st.session_state[k] = deger

def _ders_durumunu_guncelle(ders_key, unite_keys):
    st.session_state[ders_key] = bool(unite_keys) and all(st.session_state.get(k, False) for k in unite_keys)

def esc(x):
    return html.escape(temizle_latex_metin(x), quote=False)

# --- KENAR ÇUBUĞU ---
with st.sidebar:
    st.markdown("""
    <div class="marka">
        <div class="marka-logo">🔮</div>
        <div><b>Soru Fabrikası</b><span>Yapay zeka destekli sınav modülü</span></div>
    </div>
    """, unsafe_allow_html=True)
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
        "MEB Maarif Modeli",
        "Yeni Nesil Sorular"
    ], key=f"tur_secim_{st.session_state.secim_sifirla_tetikleyici}")

    zorluk_seviyesi = st.selectbox("🎯 Soru Zorluk Seviyesi:", ["Kolay", "Orta", "Zor", "Olimpik","Karma / Dengeli"], key=f"zorluk_secim_{st.session_state.secim_sifirla_tetikleyici}")

    st.markdown("---")
    st.markdown("📚 **Dersler ve Üniteler**")

    mevcut_dersler = MUGREDAT.get(secili_sinif, {})
    secili_ders_unite_haritasi = {}

    trg = st.session_state.secim_sifirla_tetikleyici
    for ders_adi, uniteler_listesi in mevcut_dersler.items():
        ders_key = f"chk_ders_{trg}_{secili_sinif}_{ders_adi}"
        unite_keys = [f"chk_unite_{trg}_{secili_sinif}_{ders_adi}_{u}" for u in uniteler_listesi]
        with st.expander(f"📘 {ders_adi}"):
            st.checkbox(f"Tüm {ders_adi} kategorisini dahil et", key=ders_key,
                        on_change=_tumunu_sec, args=(ders_key, unite_keys))
            secili_alt_uniteler = []
            for unite, uk in zip(uniteler_listesi, unite_keys):
                if st.checkbox(unite, key=uk, on_change=_ders_durumunu_guncelle, args=(ders_key, unite_keys)):
                    secili_alt_uniteler.append(unite)
            st.caption(f"{len(secili_alt_uniteler)} / {len(uniteler_listesi)} ünite seçili")
            if secili_alt_uniteler:
                secili_ders_unite_haritasi[ders_adi] = secili_alt_uniteler

    st.markdown("---")
    soru_sayisi = st.slider("🔢 Soru Sayısı:", 5, 8, 5, key=f"slider_soru_{st.session_state.secim_sifirla_tetikleyici}")

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
            GÖRSEL SORU KURALLARI (ÇOK ÖNEMLİ - ÇİZİM SORUYLA BİREBİR UYUMLU OLMALIDIR):
            Uygulama görseli senin verdiğin `gorsel_tipi` ve `etiketler` değerlerinden ÇİZER. Soru metnindeki TÜM verilen sayılar, harfler ve isimler `etiketler` içinde AYNEN yer almalı; soru metni, şıklar, çözüm ve etiketler birbiriyle çelişmemelidir. Çizim sayısal ölçülere göre ölçeklenir (3-4-5 dik üçgen gerçekten 3-4-5 oranında çizilir); verdiğin ölçüler geometrik olarak TUTARLI olmalıdır (hipotenüs en uzun kenar, açı toplamı 180° vb.).
            Görsel gerektirmeyen sorularda `gorsel_tipi` kesinlikle "yok" olmalıdır. Geometri, fen (Güneş-Dünya-Ay, mevsimler, dinamometre, sürtünme, direnç, basınç, basit makineler, DNA, çaprazlama) ve veri (grafik, tablo) konularındaki sorularda uygun `gorsel_tipi` MUTLAKA atanmalıdır.

            CEVABA İPUCU VERME KURALI (ÇOK ÖNEMLİ): Görsel yalnızca soruda VERİLEN bilgiyi göstermelidir. Sorunun İSTEDİĞİ değer, ad, evre, yön veya sonuç görselde YAZILMAMALI/GÖSTERİLMEMELİDİR. Bilinmeyen büyüklüğü "x" veya "?" ile yaz (ör. "DE": "x"). `deger_yaz`, `deger_goster`, `etiket_goster`, `hucreleri_goster`, `gorunum_goster`, `kuvvet_goster` gibi anahtarları yalnızca o bilgi soruda zaten VERİLİYORSA "evet" yap; aksi halde yazma (varsayılan "hayir"dır).

            GEÇERLİ `gorsel_tipi` DEĞERLERİ VE `etiketler` ŞEMALARI:
            1) "dinamometre": {"kuvvetler": [4], "maks": 10, "yukler": ["400 g"], "isimler": ["K"]}
               - kuvvetler: ibrenin gösterdiği N değerleri (en fazla 3 dinamometre yan yana; ör. [2, 6] ile isimler ["K","L"]). maks: skala üst sınırı (kuvvetler <= maks). yukler: asılı cisim etiketleri. İbre okuması soruda isteniyorsa "deger_yaz" YAZMA.
            2) "surtunme": {"kuvvet": 3, "maks": 10, "yuk": "2 kg", "yuzey": "Pürüzlü yüzey", "surtunme_goster": "evet"}
               - Yatay yüzeyde dinamometre ile çekilen cisim; kuvvet ibrenin gösterdiği N değeridir. Sürtünmenin yönü/büyüklüğü sorulacaksa "surtunme_goster": "hayir" yaz.
            3) "ay_evreleri" (Güneş-Dünya-Ay): varsayılan çizim Ay'ın 8 konumunu (A Yeni Ay, B İlk Hilal, C İlk Dördün, D Şişkin Ay büyüyen, E Dolunay, F Şişkin Ay küçülen, G Son Dördün, H Son Hilal) TARAFSIZ gösterir, hiçbirini vurgulamaz. {"etiket_goster": "hayir"}
               - Soru "Ay C konumundayken Dünya'dan nasıl görülür?" gibi VERİLEN bir konumdan söz ediyorsa "vurgula": "C" ekle (yalnızca soruda verilen harf).
               - Soru bir EVRE ADI verip konum soruyorsa ("İlk dördün hangi konumdadır?") vurgu YAPMA ve evre adını yazma.
               - Soru Ay'ın Dünya'dan görünen ŞEKLİNİ verip evre/konum soruyorsa "gosterim": "sadece_evre" ve "evre" (yeni_ay, ilk_hilal, ilk_dordun, sisman_buyuyen, dolunay, sisman_kuculen, son_dordun, son_hilal) ekle; şekil o evreye göre çizilir (ilk dördün: sağ yarı aydınlık, son dördün: sol yarı aydınlık). "etiket_goster" YAZMA.
               - "gorunum_goster": "evet" (sağda Dünya'dan görünüşü de çizer) yalnızca soru bunu zaten veriyorsa kullanılır.
            4) "grafik": {"tur": "sutun", "baslik": "Sınıfın Sevdiği Sporlar", "kategoriler": ["Futbol","Basketbol","Voleybol"], "degerler": [12, 8, 5], "y_baslik": "Öğrenci Sayısı", "x_baslik": "Spor"}
               - tur: "sutun", "cizgi" veya "daire". İki seri için "degerler2", "seri1_adi", "seri2_adi" ekle. Kategori ve değer sayıları eşit olmalı (en çok 10). Değerler grafikteki ızgaradan okunur; sütun üstüne yazılması için "deger_goster": "evet" yalnızca değerler soruda zaten veriliyorsa kullanılır. Kategori adlarını kısa tut.
            5) "tablo": {"baslik": "Satış Tablosu", "sutunlar": ["Ay","Satış"], "satirlar": [["Ocak","40"],["Şubat","55"]]} (en çok 10 satır; sorulan değeri hücreye yazma, "?" kullan)
            6) Üçgenler. Köşe KONUMLARI sabittir: A üst köşe, B sol alt köşe, C sağ alt köşe. `etiketler` içinde "A","B","C" anahtarlarının DEĞERLERİ ekranda görünecek gerçek köşe harfleridir (ör. KLM üçgeni için {"A":"K","B":"L","C":"M"}). Kenarlar KONUM anahtarlarıyla verilir: "AB" (sol kenar), "BC" (alt kenar), "CA" (sağ kenar). Açılar: "aci_A","aci_B","aci_C" (ör. "40°"). Bilinmeyenler "x" gibi yazılabilir (çizimde ölçeklenmez).
               - "dik_ucgen": dik açı HER ZAMAN B köşesindedir; AB ve BC dik kenarlar, CA hipotenüstür. Örn: {"A":"A","B":"B","C":"C","AB":"6 cm","BC":"8 cm","CA":"x"}
               - "eskenar_ucgen": {"A":"A","B":"B","C":"C","kenar":"5 cm"}
               - "ikizkenar_ucgen": A tepe köşesidir, AB = CA eşit kenarlar, BC tabandır. Örn: {"A":"A","B":"B","C":"C","AB":"7 cm","CA":"7 cm","BC":"5 cm","aci_A":"40°"}
               - "cesitkenar_ucgen": üç kenar veya en az iki açı sayısal verilirse üçgen gerçek ölçüyle çizilir. Örn: {"AB":"5 cm","BC":"7 cm","CA":"6 cm"} veya {"aci_A":"50°","aci_B":"60°"}
               - "benzer_ucgen": iki ayrı benzer üçgen ABC ve DEF: {"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F","AB":"3 cm","BC":"4 cm","CA":"5 cm","DE":"6 cm","EF":"8 cm","FD":"x"}; oran kenarlardan hesaplanır, yoksa "oran": 2 ver. İç içe (DE // BC) şekil için "duzen": "ic_ice" ekle ve kenarları "AD","DB","AE","EC","DE","BC" anahtarlarıyla ver.
            7) "cember": {"M":"M","r":"5 cm","cap":"10 cm","aci":"60°","A":"A","B":"B","yay":"x","kiris":"8 cm","k1":"K","k2":"L"} - yalnızca soruda geçen ögeleri ekle (r, cap, aci+A+B, yay, kiris).
            8) "basinc": Katı: {"cisim":"5 kg","G":"50 N","F":"20 N","S":"100 cm²","durus":"yatay"} (durus: "yatay"/"dikey"). Sıvı: {"sivi_adi":"Su","kap_sayisi":2,"h":"20 cm","P":"P"} veya {"sivi_adi":"Su","noktalar":["K","L","M"],"derinlikler":["10 cm","20 cm","30 cm"]}
            9) "mevsim" (Dünya'nın yörüngesi): {"K":"K","L":"L","M":"M","N":"N","vurgula":"haziran","tarih_goster":"hayir","mevsim_goster":"hayir"} - Konumlar: K=21 Haziran, L=23 Eylül, M=21 Aralık, N=21 Mart. "vurgula" (haziran/eylul/aralik/mart) yalnızca soruda verilen konum içindir; tarih veya mevsim adı sorulacaksa onları gösterme.
            10) "dna": {"baz_dizisi": "ATGCCTAG", "gizle": "tamamlayici"} - baz_dizisi en çok 10 harf (A,T,G,C); tamamlayıcı zincir SORULUYORSA "gizle": "tamamlayici" yaz.
            11) "caprazlama" (Punnett karesi): {"ebeveyn1":"Aa","ebeveyn2":"Aa","hucreleri_goster":"hayir"} - iki özellik için "AaBb". Hücre sonuçları sorulan değerse "hayir" bırak; kare zaten verilmişse "evet".
            12) "hava_direnci" / "su_direnci": {"ortam":"hava","isimler":["K","L"],"alanlar":["genis","dar"],"sekil":"levha"} - alanlar "genis","orta","dar" veya sayı ("20 cm²"); "sekil": "levha" ya da "parasut"; ortam "su" ise su içinde çizilir. Direnç oklarını çizmek için "kuvvet_goster": "evet" yalnızca soru bunu veriyorsa.
            13) "kaldirac": {"tur":"birinci","yuk":"60 N","kuvvet":"F","yuk_kolu":"1 m","kuvvet_kolu":"3 m"} - tur: "birinci","ikinci","ucuncu". Kolların uzunlukları verilmişse oranlı çizilir.
            14) "egik_duzlem": {"uzunluk":"5 m","yukseklik":"3 m","yuk":"100 N","kuvvet":"F"} - bilinmeyeni "x" yaz.
            15) "makara": {"tur":"sabit","yuk":"40 N","kuvvet":"F"} - tur: "sabit" veya "hareketli".
            16) "disli": {"dislerin_sayisi":[20,40],"isimler":["K","L"],"yonler":["saat"]} - en çok 3 dişli; çizim diş sayısına göre ölçeklenir. İlk dişlinin dönüş yönü ("saat"/"ters") verilir, diğerlerinin yönü SORULUYORSA yazma.
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
            class WorkerContext:
                def __init__(self):
                    self.quiz_data = []
                    self.basarili = False
                    self.hata_mesaji = None
                    self.api_tamamlandi = False

            ctx = WorkerContext()
            tahmini_sure_sn = int((soru_sayisi * 1.4) + 5)
            
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
                                temperature=0.7,
                                max_output_tokens=8192,
                            )
                        )
                        if response and response.text:
                            parsed_data = kararli_json_ayikla(response.text)
                            if parsed_data and len(parsed_data) > 0:
                                ctx.quiz_data = parsed_data
                                ctx.basarili = True
                                break
                    except Exception as e:
                        ctx.hata_mesaji = str(e)
                    deneme += 1
                ctx.api_tamamlandi = True

            t = threading.Thread(target=api_cagirici)
            t.start()

            while not ctx.api_tamamlandi:
                gecen_sn = int(time.time() - baslangic_zamani)
                kalan_tahmin = max(1, tahmini_sure_sn - gecen_sn)
                status_placeholder.markdown(f"""
                <div class="uretim-karti">
                    <div class="yukleniyor"></div>
                    <h4>Soru Fabrikası üretimde</h4>
                    <p>Yapay zeka soruları ve görselleri özenle hazırlıyor...</p>
                    <div class="uretim-sure">⏳ Tahmini kalan: {kalan_tahmin} sn <span>(geçen: {gecen_sn} sn)</span></div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.5)

            status_placeholder.empty()
            t.join()

            if ctx.basarili and ctx.quiz_data:
                st.session_state.quiz_data = ctx.quiz_data
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.exam_started = False
                st.session_state.quiz_ready_to_start = True
                st.session_state.current_question = 0
                soru_sayisini_artir(len(ctx.quiz_data))
                st.success(f"🎉 Başarıyla {len(ctx.quiz_data)} adet özgün soru üretildi!")
                st.rerun()
            else:
                hata_detay = ctx.hata_mesaji if ctx.hata_mesaji else "Bilinmeyen API hatası."
                st.error(f"❌ Sorular üretilemedi. Hata: {hata_detay}")

# --- ANA EKRAN / SINAV AKIŞI ---
def gorsel_html(q, yukseklik=260):
    veri = ciz_vektorel_gorsel(q.get('gorsel_tipi', 'yok'), q.get('etiketler', {}))
    if not veri:
        return ""
    return f"<div class='gorsel-sema-kutusu'><img src='{veri}' style='max-height:{yukseklik}px; max-width:100%;'></div>"


if st.session_state.quiz_ready_to_start and st.session_state.quiz_data and not st.session_state.exam_started:
    toplam_soru_sayisi = len(st.session_state.quiz_data)
    otomatik_sure_dk = (toplam_soru_sayisi * 80) // 60
    gorselli = sum(1 for q in st.session_state.quiz_data if str(q.get('gorsel_tipi', 'yok')).lower() != 'yok')
    st.markdown(f"""
    <div class="hero orta">
        <h1>🎓 Sınav Hazır!</h1>
        <p>Sınavınız başarıyla oluşturuldu. Hazır olduğunda başlat butonuna bas; süre başladığında geri sayım çalışır.</p>
        <div class="hero-chipler">
            <div class="hero-chip"><b>{toplam_soru_sayisi}</b><span>Soru</span></div>
            <div class="hero-chip"><b>{otomatik_sure_dk} dk</b><span>Süre (soru başına 80 sn)</span></div>
            <div class="hero-chip"><b>{gorselli}</b><span>Görselli soru</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_A, col_B, col_C = st.columns([1, 2, 1])
    with col_B:
         if st.button("🏁 Sınavı Başlat", use_container_width=True, type="primary"):
             st.session_state.exam_started = True
             st.session_state.start_time = time.time()
             st.session_state.total_duration = toplam_soru_sayisi * 80
             st.rerun()

elif st.session_state.exam_started and st.session_state.quiz_data and not st.session_state.quiz_submitted:
    quiz_data = st.session_state.quiz_data
    toplam_soru = len(quiz_data)

    gecen_sure_sn = time.time() - st.session_state.start_time
    kalan_sure_sn = st.session_state.total_duration - gecen_sure_sn

    if kalan_sure_sn <= 0:
        st.session_state.quiz_submitted = True
        st.warning("⏰ Sınav süresi sona erdi! Cevaplarınız otomatik olarak gönderildi.")
        st.rerun()

    kalan_dk = int(kalan_sure_sn // 60)
    kalan_sn = int(kalan_sure_sn % 60)
    q_idx = st.session_state.current_question
    q = quiz_data[q_idx]
    cevaplanan = sum(1 for i in range(toplam_soru) if st.session_state.user_answers.get(i))
    yuzde = int(((q_idx + 1) / toplam_soru) * 100)

    noktalar = "".join(
        f"<span class='nokta{' cevapli' if st.session_state.user_answers.get(i) else ''}{' aktif' if i == q_idx else ''}'>{i + 1}</span>"
        for i in range(toplam_soru)
    )
    st.markdown(f"""
    <div class="ust-bar">
        <div class="soru-no">Soru {q_idx + 1} <small>/ {toplam_soru}</small></div>
        <div class="sure{' az' if kalan_sure_sn < 60 else ''}">⏳ {kalan_dk:02d}:{kalan_sn:02d}</div>
    </div>
    <div class="ilerleme-cubuk"><div style="width:{yuzde}%"></div></div>
    <div class="nokta-sira">{noktalar}</div>
    <div class="cevap-ozet">{cevaplanan} / {toplam_soru} soru cevaplandı</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="soru-karti">
        <span class="rozet">📘 {html.escape(str(q.get('ders', 'Genel')))}</span>
        <div class="soru-metni-kutusu">{esc(q.get('soru_metni', ''))}</div>
        {gorsel_html(q, 340)}
    </div>
    """, unsafe_allow_html=True)

    secenekler = q.get('secenekler', {})
    secenek_anahtarlari = list(secenekler.keys())

    mevcut_cevap = st.session_state.user_answers.get(q_idx, None)
    secilen_index = secenek_anahtarlari.index(mevcut_cevap) if mevcut_cevap in secenek_anahtarlari else None

    st.markdown("<div class='alt-baslik'>Cevabını seç</div>", unsafe_allow_html=True)
    secim = st.radio(
        "Lütfen cevabınızı seçiniz:",
        options=secenek_anahtarlari,
        format_func=lambda x: f"{x}) {temizle_latex_metin(secenekler[x])}",
        key=f"radio_soru_{q_idx}",
        index=secilen_index,
        label_visibility="collapsed"
    )

    if secim:
        st.session_state.user_answers[q_idx] = secim

    st.markdown("<br>", unsafe_allow_html=True)

    # --- HATASIZ TEKİL NAVİGASYON (ÇİFTE RENDER / YANSIMA ÖNLEYİCİ) ---
    col_nav1, col_nav2, col_nav3 = st.columns(3)

    with col_nav1:
        if q_idx < toplam_soru - 1:
            if st.button("Sonraki Soru ➡️", key=f"btn_next_{q_idx}", use_container_width=True, type="secondary"):
                st.session_state.current_question += 1
                st.rerun()

    with col_nav3:
        # Önceki soru butonu (ilk soru hariç her yerde görünecek)
        if q_idx > 0:
            if st.button("⬅️ Önceki Soru", key=f"btn_prev_{q_idx}", use_container_width=True, type="secondary"):
                st.session_state.current_question -= 1
                st.rerun()

        if st.button("✅ Sınavı Tamamla", key=f"btn_finish_{q_idx}", use_container_width=True, type="primary"):
            st.session_state.quiz_submitted = True
            st.rerun()

elif st.session_state.quiz_submitted and st.session_state.quiz_data:
    quiz_data = st.session_state.quiz_data
    dogru_sayisi = 0
    yanlis_sayisi = 0
    bos_sayisi = 0

    for idx, q in enumerate(quiz_data):
        ogrenci_cevabi = st.session_state.user_answers.get(idx, None)
        dogru_cevap = q.get('dogru_cevap', '').strip().upper()

        if not ogrenci_cevabi:
            bos_sayisi += 1
        elif ogrenci_cevabi.strip().upper() == dogru_cevap:
            dogru_sayisi += 1
        else:
            yanlis_sayisi += 1

    toplam_puan = (dogru_sayisi / len(quiz_data)) * 100 if len(quiz_data) > 0 else 0
    if toplam_puan >= 85:
        mesaj = "Harika! Konulara çok iyi hakimsin 🌟"
    elif toplam_puan >= 60:
        mesaj = "İyi gidiyorsun, birkaç tekrar mükemmel olur 👍"
    else:
        mesaj = "Çözümleri incele ve tekrar dene, gelişeceksin 💪"

    st.markdown(f"""
    <div class="skor-banner">
        <div>
            <div class="skor-puan">{toplam_puan:.0f}<small> / 100</small></div>
            <div class="skor-mesaj">{mesaj}</div>
        </div>
        <div class="skor-chipler">
            <div class="chip"><b>{dogru_sayisi}</b><span>✅ Doğru</span></div>
            <div class="chip"><b>{yanlis_sayisi}</b><span>❌ Yanlış</span></div>
            <div class="chip"><b>{bos_sayisi}</b><span>⭕ Boş</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📋 Soru Soru Detaylı Çözüm İncelemesi")

    for idx, q in enumerate(quiz_data):
        ogrenci_cevabi = st.session_state.user_answers.get(idx, "Boş")
        dogru_cevap = q.get('dogru_cevap', '').strip().upper()
        durum_ikonu = "✅" if ogrenci_cevabi == dogru_cevap else ("⭕" if ogrenci_cevabi == "Boş" else "❌")

        with st.expander(f"Soru {idx + 1} {durum_ikonu} - (Ders: {q.get('ders', 'Genel')})"):
            sikler = ""
            for sec_key, sec_val in q.get('secenekler', {}).items():
                sinif, etiket = "", ""
                if sec_key == dogru_cevap:
                    sinif, etiket = " dogru", "Doğru cevap"
                elif sec_key == ogrenci_cevabi:
                    sinif, etiket = " yanlis", "Senin cevabın"
                sikler += f"<div class='sik{sinif}'><b>{html.escape(str(sec_key))})</b> {esc(sec_val)}<span>{etiket}</span></div>"
            st.markdown(f"""
            <div class="soru-metni-kutusu" style="font-size:18px;">{esc(q.get('soru_metni', ''))}</div>
            {gorsel_html(q, 300)}
            {sikler}
            <div class="cozum">💡 <b>Çözüm:</b> {esc(q.get('cozum_aciklamasi', 'Açıklama bulunmuyor.'))}</div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Yeni Sınav Hazırla", use_container_width=True, type="primary"):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_ready_to_start = False
            st.session_state.exam_started = False
            st.session_state.secim_sifirla_tetikleyici += 1
            st.rerun()

else:
    st.markdown("""
    <div class="hero">
        <h1>🎓 Soru Fabrikası'na Hoş Geldin</h1>
        <p>Sol menüden sınıf seviyesini, sınav türünü ve çalışmak istediğin ders ile üniteleri seç; yapay zeka senin için özgün, görselli sorularla dolu bir sınav hazırlasın.</p>
    </div>
    <div class="ozellik-izgara">
        <div class="ozellik"><div class="ikon">🧩</div><b>Özgün sorular</b><span>Her seferinde farklı, MEB müfredatına uygun sorular üretilir.</span></div>
        <div class="ozellik"><div class="ikon">📐</div><b>Soruyla uyumlu görseller</b><span>Üçgen, grafik, dinamometre, Ay evreleri ve daha fazlası sorudaki verilere göre çizilir.</span></div>
        <div class="ozellik"><div class="ikon">⏱️</div><b>Süreli sınav</b><span>Tablet dostu ekranda geri sayımlı sınav deneyimi.</span></div>
        <div class="ozellik"><div class="ikon">🏆</div><b>Detaylı analiz</b><span>Doğru, yanlış, boş sayıları ve her sorunun çözümü.</span></div>
    </div>
    """, unsafe_allow_html=True)

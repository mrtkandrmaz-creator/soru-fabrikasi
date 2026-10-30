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
        vurgulu = (key == hedef)
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
    if hedef:
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
from matplotlib.patches import Rectangle, Arc, Polygon, Wedge


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


# --- DİNAMOMETRE ---
def _guzel_maks(v):
    for m in (5, 10, 20, 25, 50, 100, 200, 500):
        if v <= m:
            return m
    return float(np.ceil(v / 100) * 100)


def _dinamometre_tek(ax, cx, kuvvet, maks, ad="", yuk="", w=0.8, kucuk=False, deger_yaz=False):
    ust, alt = 4.25, 1.85
    fs = 6 if kucuk else 7
    ax.add_patch(plt.Circle((cx, 4.65), 0.14, fill=False, ec='#475569', linewidth=2.5))
    ax.plot([cx, cx], [4.51, ust], color='#475569', linewidth=3)
    ax.add_patch(Rectangle((cx - w / 2, alt), w, ust - alt, fc='#f1f5f9', ec='#0f172a', linewidth=2, zorder=2))
    s0, s1 = ust - 0.25, alt + 0.25

    def yv(v):
        return s0 - (v / maks) * (s0 - s1)
    step = 1.0 if maks <= 10 else maks / 10
    ticks = np.arange(0, maks + 1e-9, step)
    for v in ticks:
        ax.plot([cx + w / 2 - 0.2, cx + w / 2], [yv(v), yv(v)], color='#0f172a', linewidth=1.3, zorder=3)
        ax.text(cx + w / 2 + 0.07, yv(v), f"{v:g}", fontsize=fs, va='center', ha='left', color='#0f172a', zorder=3)
        if v + step / 2 <= maks + 1e-9:
            ax.plot([cx + w / 2 - 0.1, cx + w / 2], [yv(v + step / 2)] * 2, color='#0f172a', linewidth=0.9, zorder=3)
    ax.text(cx + w / 2 + 0.07, ust - 0.03, "N", fontsize=fs + 1, fontweight='bold', color='#dc2626', va='center')
    kuvvet = min(max(kuvvet, 0), maks)
    yp = yv(kuvvet)
    m = 17
    ys = np.linspace(ust - 0.03, yp, m)
    xs = (cx - w * 0.2) + 0.08 * np.where(np.arange(m) % 2 == 0, 1, -1)
    ax.plot(xs, ys, color='#f97316', linewidth=1.8, zorder=3)
    ax.plot([cx - w / 2 + 0.03, cx + w / 2 - 0.03], [yp, yp], color='#dc2626', linewidth=2.4, zorder=4)
    if deger_yaz:
        ax.text(cx - w / 2 - 0.07, yp, f"{kuvvet:g} N", fontsize=fs + 1, fontweight='bold', color='#dc2626',
                ha='right', va='center')
    ax.plot([cx, cx], [alt, 1.3], color='#475569', linewidth=2.5)
    bw = 0.8 if kucuk else 0.95
    ax.add_patch(Rectangle((cx - bw / 2, 0.5), bw, 0.8, fc='#cbd5e1', ec='#0f172a', linewidth=2, zorder=3))
    ax.text(cx, 0.9, _t(yuk) or "Yük", fontsize=fs + 1, fontweight='bold', ha='center', va='center', color='#0f172a', zorder=4)
    if ad:
        ax.text(cx, 0.22, _t(ad), fontsize=10, fontweight='bold', ha='center', color='#0f172a')


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
                         yukler[i] if i < len(yukler) else "", w=0.8 if n == 1 else 0.7,
                         kucuk=n > 1, deger_yaz=deger_yaz)


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


# --- GRAFİK / TABLO ---
_PALET = ['#38bdf8', '#f97316', '#a855f7', '#22c55e', '#ef4444', '#eab308', '#14b8a6', '#6366f1']


def _grafik_ciz(ax, tip, et):
    kat = [_t(x) for x in liste_cek(et.get("kategoriler") if et.get("kategoriler") is not None else et.get("x_etiketler"))]
    deg = [sayi_cek(x, 0.0) for x in liste_cek(et.get("degerler"))]
    if not deg:
        kat = [_t(et.get(k)) for k in ("X1", "X2", "X3") if et.get(k)]
        deg = [3.0, 5.0, 2.0][:len(kat)] if kat else []
    if not deg:
        kat, deg = ["A", "B", "C"], [3.0, 5.0, 2.0]
    if not kat:
        kat = [str(i + 1) for i in range(len(deg))]
    n = min(len(kat), len(deg))
    kat, deg = kat[:n], deg[:n]
    deg2 = [sayi_cek(x, 0.0) for x in liste_cek(et.get("degerler2"))][:n]
    tur = _norm(et.get("tur", ""))
    if not tur:
        tur = "cizgi" if "cizgi" in tip else ("daire" if ("daire" in tip or "pasta" in tip) else "sutun")
    goster = _norm(et.get("deger_goster", "evet")) not in ("hayir", "false", "0")
    baslik = _t(et.get("baslik", ""))
    if baslik:
        ax.text(0.5, 0.97, baslik, fontsize=9, fontweight='bold', ha='center', va='top', color='#0f172a', transform=ax.transAxes)

    if tur in ("daire", "pasta"):
        iax = ax.inset_axes([0.22, 0.02, 0.56, 0.8])
        etik = [f"{k} ({d:g})" if goster else k for k, d in zip(kat, deg)]
        iax.pie(deg, labels=etik, colors=[_PALET[i % len(_PALET)] for i in range(n)],
                textprops={'fontsize': 8, 'fontweight': 'bold'}, wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
        return

    iax = ax.inset_axes([0.15, 0.2, 0.8, 0.6])
    iax.spines[['top', 'right']].set_visible(False)
    iax.set_axisbelow(True)
    iax.grid(axis='y', color='#e2e8f0', linewidth=0.8)
    iax.tick_params(labelsize=7)
    xs = np.arange(n)
    ust = max(deg + (deg2 or [0]))
    iax.set_ylim(0, ust * 1.22 if ust > 0 else 1)
    if tur == "cizgi":
        iax.plot(xs, deg, marker='o', color='#2563eb', linewidth=2.2, label=_t(et.get("seri1_adi", "")) or None)
        if deg2:
            iax.plot(xs, deg2, marker='s', color='#f97316', linewidth=2.2, label=_t(et.get("seri2_adi", "")) or None)
        if goster:
            for x, d in zip(xs, deg):
                iax.annotate(f"{d:g}", (x, d), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=7, fontweight='bold')
    else:
        if deg2:
            bw = 0.38
            b1 = iax.bar(xs - bw / 2, deg, bw, color='#38bdf8', ec='#0f172a', linewidth=1.2, label=_t(et.get("seri1_adi", "")) or None)
            b2 = iax.bar(xs + bw / 2, deg2, bw, color='#f97316', ec='#0f172a', linewidth=1.2, label=_t(et.get("seri2_adi", "")) or None)
            gruplar = [(b1, deg), (b2, deg2)]
        else:
            b1 = iax.bar(xs, deg, 0.6, color=[_PALET[i % len(_PALET)] for i in range(n)], ec='#0f172a', linewidth=1.2)
            gruplar = [(b1, deg)]
        if goster:
            for bars, vals in gruplar:
                for b, d in zip(bars, vals):
                    iax.text(b.get_x() + b.get_width() / 2, d + ust * 0.02, f"{d:g}", ha='center', va='bottom', fontsize=7, fontweight='bold')
    iax.set_xticks(xs)
    iax.set_xticklabels(kat, fontsize=7, rotation=0 if max(len(k) for k in kat) <= 8 else 30)
    if et.get("y_baslik"):
        iax.set_ylabel(_t(et["y_baslik"]), fontsize=7)
    if et.get("seri1_adi") or et.get("seri2_adi"):
        iax.legend(fontsize=7, frameon=False, loc='upper right')


def _tablo_ciz(ax, et):
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
        return False
    m = max(len(r) for r in satirlar + ([sut] if sut else []))
    satirlar = [r + [""] * (m - len(r)) for r in satirlar]
    sut = (sut + [""] * (m - len(sut))) if sut else None
    baslik = _t(et.get("baslik", ""))
    if baslik:
        ax.text(0.5, 0.97, baslik, fontsize=9, fontweight='bold', ha='center', va='top', transform=ax.transAxes)
    tbl = ax.table(cellText=satirlar, colLabels=sut, loc='center', cellLoc='center', bbox=[0.04, 0.1, 0.92, 0.72])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor('#0f172a')
        cell.set_linewidth(1.2)
        if sut and r == 0:
            cell.set_facecolor('#e0e7ff')
            cell.set_text_props(fontweight='bold')
    return True


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


# --- ANA ÇİZİCİ ---
def _ciz_ic(gorsel_tipi, etiketler):
    et = etiketler if isinstance(etiketler, dict) else {}
    tip = _norm(gorsel_tipi)
    if tip in ("yok", "", "none"):
        return None

    fig, ax = plt.subplots(figsize=(4.5, 3.3))
    ax.set_aspect('equal')
    ax.axis('off')

    cizildi = True
    if any(k in tip for k in ("gunes_dunya_ay", "astronomi", "ay_evre", "evre")):
        ay_evreleri_ciz(ax, et, tip)
    elif "surtunme" in tip:
        _surtunme_ciz(ax, et)
    elif "dinamometre" in tip or "kuvvet_hareket" in tip:
        _dinamometre_ciz(ax, et)
    elif "tablo" in tip:
        cizildi = _tablo_ciz(ax, et)
    elif any(k in tip for k in ("grafik", "veri", "histogram", "sutun", "cizgi")):
        _grafik_ciz(ax, tip, et)
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
        "MEB Maarif Modeli",
        "Yeni Nesil Sorular"
    ], key=f"tur_secim_{st.session_state.secim_sifirla_tetikleyici}")

    zorluk_seviyesi = st.selectbox("🎯 Soru Zorluk Seviyesi:", ["Kolay", "Orta", "Zor", "Olimpik","Karma / Dengeli"], key=f"zorluk_secim_{st.session_state.secim_sifirla_tetikleyici}")

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
            Uygulama görseli senin verdiğin `gorsel_tipi` ve `etiketler` değerlerinden ÇİZER. Bu yüzden soru metnindeki TÜM sayılar, harfler ve isimler `etiketler` içinde AYNEN yer almalı; soru metni, şıklar, çözüm ve etiketler birbiriyle çelişmemelidir. Çizim sayısal ölçülere göre ölçeklenir (ör. 3-4-5 dik üçgen gerçekten 3-4-5 oranında çizilir), bu yüzden verdiğin ölçüler geometrik olarak TUTARLI olmalıdır (hipotenüs en uzun kenar, açı toplamı 180° vb.).
            Görsel gerektirmeyen sorularda `gorsel_tipi` kesinlikle "yok" olmalıdır. Geometri, fen (Güneş-Dünya-Ay, dinamometre, sürtünme, basınç) ve veri (grafik, tablo) konularındaki sorularda uygun `gorsel_tipi` MUTLAKA atanmalıdır.
            Sorunun cevabı görselden okunacaksa (ör. "ibre kaç N gösteriyor?") cevabı etiket olarak çizime YAZDIRMA; ölçüyü yalnızca çizimi belirleyen sayısal alana yaz.

            GEÇERLİ `gorsel_tipi` DEĞERLERİ VE `etiketler` ŞEMALARI:
            1) "dinamometre": {"kuvvetler": [4], "maks": 10, "yukler": ["400 g"], "isimler": ["K"], "deger_yaz": "hayir"}
               - kuvvetler: ibrenin gösterdiği N değerleri (en fazla 3 dinamometre yan yana; ör. [2, 6] ile isimler ["K","L"]). maks: skala üst sınırı (kuvvetler <= maks). yukler: asılı cisim etiketleri. deger_yaz "evet" ise okunan değer çizimde yazar.
            2) "surtunme": {"kuvvet": 3, "maks": 10, "yuk": "2 kg", "yuzey": "Pürüzlü yüzey", "surtunme_goster": "evet"}
               - Yatay yüzeyde dinamometre ile çekilen cisim; kuvvet ibrenin gösterdiği N değeridir.
            3) "ay_evreleri" (Güneş-Dünya-Ay): {"evre": "ilk_dordun", "etiket_goster": "hayir"}
               - evre değerleri: "yeni_ay","ilk_hilal","ilk_dordun","sisman_buyuyen","dolunay","sisman_kuculen","son_dordun","son_hilal". Soru hangi evreyi anlatıyorsa AYNISI yazılmalıdır. Konum harfleri: A Yeni Ay, B İlk Hilal, C İlk Dördün, D Şişkin Ay (büyüyen), E Dolunay, F Şişkin Ay (küçülen), G Son Dördün, H Son Hilal. Yalnızca Dünya'dan görünen şekil için "gosterim": "sadece_evre" ekle. Evre adı cevabı veriyorsa etiket_goster "hayir" bırak.
            4) "grafik": {"tur": "sutun", "baslik": "Sınıfın Sevdiği Sporlar", "kategoriler": ["Futbol","Basketbol","Voleybol"], "degerler": [12, 8, 5], "y_baslik": "Öğrenci Sayısı", "deger_goster": "evet"}
               - tur: "sutun", "cizgi" veya "daire". İki seri için "degerler2", "seri1_adi", "seri2_adi" ekle. Kategori ve değer sayıları eşit olmalı. Soru metnindeki sayılar grafikteki değerlerle aynı olmalı.
            5) "tablo": {"baslik": "Satış Tablosu", "sutunlar": ["Ay","Satış"], "satirlar": [["Ocak","40"],["Şubat","55"]]}
            6) Üçgenler. Köşe KONUMLARI sabittir: A üst köşe, B sol alt köşe, C sağ alt köşe. `etiketler` içinde "A","B","C" anahtarlarının DEĞERLERİ ekranda görünecek gerçek köşe harfleridir (ör. KLM üçgeni için {"A":"K","B":"L","C":"M"}). Kenarlar KONUM anahtarlarıyla verilir: "AB" (sol kenar), "BC" (alt kenar), "CA" (sağ kenar). Açılar: "aci_A","aci_B","aci_C" (ör. "40°"). Bilinmeyenler "x" gibi yazılabilir (çizimde ölçeklenmez).
               - "dik_ucgen": dik açı HER ZAMAN B köşesindedir; AB ve BC dik kenarlar, CA hipotenüstür. Örn: {"A":"A","B":"B","C":"C","AB":"6 cm","BC":"8 cm","CA":"10 cm"}
               - "eskenar_ucgen": {"A":"A","B":"B","C":"C","kenar":"5 cm"} (tüm kenarlar eşit işaretlenir; açı etiketi gerekirse aci_A vb.)
               - "ikizkenar_ucgen": A tepe köşesidir, AB = CA eşit kenarlar, BC tabandır. Örn: {"A":"A","B":"B","C":"C","AB":"7 cm","CA":"7 cm","BC":"5 cm","aci_A":"40°"} (tepe açısı verilirse ona göre çizilir)
               - "cesitkenar_ucgen": üç kenar veya en az iki açı sayısal verilirse üçgen gerçek ölçüyle çizilir. Örn: {"AB":"5 cm","BC":"7 cm","CA":"6 cm"} veya {"aci_A":"50°","aci_B":"60°"}
               - "benzer_ucgen": iki ayrı benzer üçgen ABC ve DEF: {"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F","AB":"3 cm","BC":"4 cm","CA":"5 cm","DE":"6 cm","EF":"8 cm","FD":"10 cm"}; oran kenarlardan hesaplanır, yoksa "oran": 2 ver. İç içe (DE // BC) şekil için "duzen": "ic_ice" ekle ve kenarları "AD","DB","AE","EC","DE","BC" anahtarlarıyla ver (D, AB üzerinde; E, AC üzerinde).
            7) "cember": {"M":"M","r":"5 cm","cap":"10 cm","aci":"60°","A":"A","B":"B","yay":"20π cm","kiris":"8 cm","k1":"K","k2":"L"}
               - Yalnızca soruda geçen ögeleri ekle: r (yarıçap), cap (çap, uç noktalar "uc1","uc2"), aci (merkez açı; A ve B uç noktaları, "yay" ile yay uzunluğu), kiris (alt kiriş, k1/k2 uç harfleri).
            8) "basinc":
               - Katı basıncı: {"cisim":"5 kg","G":"50 N","F":"20 N","S":"100 cm²","durus":"yatay"} (durus: "yatay" geniş yüzey üstte durur, "dikey" dar yüzey üstte durur; F yalnızca ek kuvvet varsa)
               - Sıvı basıncı: {"sivi_adi":"Su","kap_sayisi":2,"h":"20 cm","P":"P"} veya aynı kapta farklı derinlikler için {"sivi_adi":"Su","noktalar":["K","L","M"],"derinlikler":["10 cm","20 cm","30 cm"]}
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
                <div style="background-color: #ffffff; border: 2px solid #cbd5e1; padding: 22px; border-radius: 14px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px;">
                    <h4 style="color: #4f46e5; margin-bottom: 8px;">🤖 Soru Fabrikası Üretim Aşamasında</h4>
                    <p style="font-size: 17px; color: #1e293b; font-weight: 600;">Yapay zeka senin için harika soruları özenle tasarlıyor ve derliyor...</p>
                    <p style="font-size: 18px; color: #f97316; font-weight: 700; margin-top: 10px;">⏳ Tahmini Kalan Süre: {kalan_tahmin} saniye <span style="font-size: 14px; color: #64748b; font-weight: normal;">(Geçen: {gecen_sn} sn)</span></p>
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
if st.session_state.quiz_ready_to_start and st.session_state.quiz_data and not st.session_state.exam_started:
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>🎓 Sınav Hazır!</h2>", unsafe_allow_html=True)
    toplam_soru_sayisi = len(st.session_state.quiz_data)
    otomatik_sure_dk = (toplam_soru_sayisi * 80) // 60
    st.markdown(f"<p style='text-align: center; font-size: 18px;'>Toplam <b>{toplam_soru_sayisi}</b> sorudan oluşan sınavınız başarıyla oluşturulmuştur.<br>Sınav süresi her soru için <b>120 saniye</b> hesaba katılarak otomatik olarak <b>{otomatik_sure_dk} dakika</b> olarak ayarlanmıştır.</p>", unsafe_allow_html=True)
    
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

    st.markdown(f"### 📝 Soru {st.session_state.current_question + 1} / {toplam_soru}")
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%); border: 2px solid #f97316; padding: 14px; border-radius: 12px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(249,115,22,0.12);">
        <span style="font-size: 22px; font-weight: 800; color: #c2410c;">⏳ Kalan Sınav Süresi: {kalan_dk:02d} Dakika {kalan_sn:02d} Saniye</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress((st.session_state.current_question + 1) / toplam_soru)
    st.markdown("---")

    q_idx = st.session_state.current_question
    q = quiz_data[q_idx]

    st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 14px; font-weight: bold; color: #4f46e5;'>Ders / Kategori: {q.get('ders', 'Genel')}</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='soru-metni-kutusu'>{temizle_latex_metin(q.get('soru_metni', ''))}</div>", unsafe_allow_html=True)

    gorsel_tipi = q.get('gorsel_tipi', 'yok')
    etiketler = q.get('etiketler', {})
    gorsel_veri = ciz_vektorel_gorsel(gorsel_tipi, etiketler)
    if gorsel_veri:
        st.markdown(f"<div class='gorsel-sema-kutusu'><img src='{gorsel_veri}' style='max-height: 250px;'></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    secenekler = q.get('secenekler', {})
    secenek_anahtarlari = list(secenekler.keys())
    
    mevcut_cevap = st.session_state.user_answers.get(q_idx, None)
    secilen_index = secenek_anahtarlari.index(mevcut_cevap) if mevcut_cevap in secenek_anahtarlari else None

    secim = st.radio(
        "Lütfen cevabınızı seçiniz:",
        options=secenek_anahtarlari,
        format_func=lambda x: f"{x}) {temizle_latex_metin(secenekler[x])}",
        key=f"radio_soru_{q_idx}",
        index=secilen_index
    )

    if secim:
        st.session_state.user_answers[q_idx] = secim

    st.markdown("</div>", unsafe_allow_html=True)

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
        
        # Sınavı tamamlama butonu (sadece en son soruda görünecek)
        if q_idx == toplam_soru - 1:
            if st.button("✅ Sınavı Tamamla", key=f"btn_finish_{q_idx}", use_container_width=True, type="primary"):
                st.session_state.quiz_submitted = True
                st.rerun()
        else:
            if st.button("✅ Sınavı Tamamla", key=f"btn_finish_{q_idx}", use_container_width=True, type="primary"):
                st.session_state.quiz_submitted = True
                st.rerun()

elif st.session_state.quiz_submitted and st.session_state.quiz_data:
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>🏆 Sınav Sonuçları ve Çözüm Analizi</h2>", unsafe_allow_html=True)
    
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

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("🎯 Toplam Puan", f"{toplam_puan:.1f} / 100")
    col_m2.metric("✅ Doğru Sayısı", dogru_sayisi)
    col_m3.metric("❌ Yanlış Sayısı", yanlis_sayisi)
    col_m4.metric("⭕ Boş Sayısı", bos_sayisi)

    st.markdown("---")
    st.markdown("### 📋 Soru Soru Detaylı Çözüm İncelemesi")

    for idx, q in enumerate(quiz_data):
        ogrenci_cevabi = st.session_state.user_answers.get(idx, "Boş")
        dogru_cevap = q.get('dogru_cevap', '').strip().upper()
        durum_ikonu = "✅" if ogrenci_cevabi == dogru_cevap else "❌"
        
        with st.expander(f"Soru {idx + 1} {durum_ikonu} - (Ders: {q.get('ders', 'Genel')})"):
            st.markdown(f"**Soru:** {temizle_latex_metin(q.get('soru_metni', ''))}")
            
            gorsel_tipi = q.get('gorsel_tipi', 'yok')
            etiketler = q.get('etiketler', {})
            gorsel_veri = ciz_vektorel_gorsel(gorsel_tipi, etiketler)
            if gorsel_veri:
                st.markdown(f"<div class='gorsel-sema-kutusu'><img src='{gorsel_veri}' style='max-height: 200px;'></div>", unsafe_allow_html=True)
                
            st.markdown("---")
            for sec_key, sec_val in q.get('secenekler', {}).items():
                isaret = ""
                if sec_key == dogru_cevap:
                    isaret = " 🟢 (Doğru Cevap)"
                elif sec_key == ogrenci_cevabi:
                    isaret = " 🔴 (Sizin Cevabınız)"
                st.markdown(f"- **{sec_key})** {temizle_latex_metin(sec_val)}{isaret}")
            
            st.markdown(f"💡 **Çözüm Açıklaması:** {temizle_latex_metin(q.get('cozum_aciklamasi', 'Açıklama bulunmuyor.'))}")

    st.markdown("---")
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
    st.markdown("<div class='custom-card' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h1>🎓 Soru Fabrikası Tablet Sınav Modülüne Hoş Geldiniz!</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 18px; color: #475569;'>Sol menüden sınıf seviyesini, sınav türünü ve çalışmak istediğiniz dersleri/üniteleri seçerek anında yapay zeka destekli özgün sınavlar üretebilir ve çözebilirsiniz.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st
import json
import random
import re
import os
import sys
import time
from google import genai
from google.genai import types
from streamlit_drawable_canvas import st_canvas

# --- RENDER / SAYFA AYARI ---
st.set_page_config(
    page_title="Soru Fabrikası & Tablet Sınav Modülü",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN TASARIM VE ÖZEL CSS ---
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .custom-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        text-align: center;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    h1, h2, h3 {
        color: #1e293b;
        font-family: 'Segoe UI', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- MEB MÜFREDATI ---
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
        "Matematik": ["Doğal Sayılarla İşlemler", "Kesirler", "Ondalık Gösterimler", "Yüzdeler", "Üçgen ve Dörtgenler", "Veri İşleme", "Temel Geometrik Kavramlar ve Doğrular"],
        "Fen Bilimleri": ["Güneş, Dünya ve Ay", "Canlılar Dünyası", "Kuvvetin Uygulanması ve Sürtünme", "Maddenin Hâl Değişimi ve Isı", "Işığın Yayılması"],
        "Sosyal Bilgiler": ["Birey ve Toplum", "Kültür ve Miras", "İnsanlar, Yerler ve Çevre", "Bilim, Teknoloji ve Toplum", "Üretim, Dağıtım ve Tüketim"],
        "Din Kültürü": ["Allah İnancı ve İnsan", "Hz. Muhammed ve Aile Hayatı", "İslam'ın Temel İbadetleri", "Ahlaki Değerler"],
        "İngilizce": ["Hello!", "My Town", "Games and Hobbies", "My Daily Routine", "Health", "Movies"]
    },
    "6. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragraf Bilgisi", "Metin Türleri", "Fiiller"],
        "Matematik": ["Çarpanlar ve Katlar", "Kümeler", "Tam Sayılar", "Kesirlerle İşlemler", "Cebirsel İfadeler", "Açılar"],
        "Fen Bilimleri": ["Güneş Sistemi ve Tutulmalar", "Vücudumuzdaki Sistemler", "Kuvvet ve Hareket", "Madde ve Isı", "Ses ve Özellikleri"],
        "Sosyal Bilgiler": ["Biz ve Toplum", "Yeryüzünde Yaşam", "Türklerin Tarihsel Yolculuğu", "Ussal Ekonomi", "Yönetimimiz ve Demokrasi"],
        "Din Kültürü": ["Peygamber ve İlahi Kitaplar", "Namaz İbadeti", "Hz. Muhammed'in Hayatı", "Ahlaki Tutum ve Davranışlar"],
        "İngilizce": ["Life", "Yummy Breakfast", "Downtown", "Weather and Emotions", "At the Fair", "Vacations"]
    },
    "7. Sınıf": {
        "Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Cümlenin Ögeleri", "Fiilimsiler", "Anlatım Bozuklukları"],
        "Matematik": ["Tam Sayılarla İşlemler", "Rasyonel Sayılar", "Cebirsel İfadeler", "Eşitlik ve Denklem", "Oran ve Orantı", "Açılar ve Çokgenler"],
        "Fen Bilimleri": ["Güneş Sistemi ve Ötesi", "Hücre ve Bölünmeler", "Kuvvet ve Enerji", "Saf Madde ve Karışımlar", "Işığın Soğurulması"],
        "Sosyal Bilgiler": ["Birlikte Yaşamak", "Ülkemizde Nüfus", "Tarihte Yolculuk", "Ekonomi ve Sosyal Hayat", "Yaşayan Demokrasi"],
        "Din Kültürü": ["Melek ve Ahiret İnancı", "Hac ve Kurban", "Ahlaki Davranışlar", "İslam Düşüncesinde Yorumlar"],
        "İngilizce": ["Appearance and Personality", "Sports", "Biographies", "Wild Animals", "Television", "Celebrations"]
    },
    "8. Sınıf": {
        "Türkçe": ["Fiilimsiler", "Cümlenin Ögeleri", "Cümle Türleri", "Yazım Kuralları", "Sözel Mantık ve Muhakeme", "Paragraf Analizi"],
        "Matematik": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Basit Olayların Olma Olasılığı", "Doğrusal Denklemler", "Üçgenler"],
        "Fen Bilimleri": ["Mevsimlerin Oluşumu ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler", "Enerji Dönüşümleri"],
        "Sosyal Bilgiler": ["Bir Demokrasi Kahramanı: Atatürk", "Milli Uyanış", "Ya İstiklal Ya Ölüm", "Atatürkçülük ve Çağdaşlaşan Türkiye"],
        "Din Kültürü": ["Kader İnancı", "Zekat ve Sadaka", "Din ve Hayat", "Hz. Muhammed'in Örnekliği"],
        "İngilizce": ["Friendship", "Teen Life", "In the Kitchen", "On the Phone", "The Internet", "Adventures"]
    },
    "LGS Hazırlık": {
        "Türkçe": ["Sözel Mantık ve Muhakeme", "Paragraf Analizi", "Dil Bilgisi Karma Denemeleri"],
        "Matematik": ["LGS Pro Matematik Karma", "Yeni Nesil Beceri Temelli Sorular", "Geometri Denemeleri"],
        "Fen Bilimleri": ["LGS Fen Bilimleri Kapsamlı Karma Denemeler", "Mevsimler, DNA ve Basınç Tekrarı"],
        "Sosyal Bilgiler": ["T.C. İnkılap Tarihi ve Atatürkçülük Karma Tekrar"],
        "Din Kültürü": ["LGS Din Kültürü Karma Denemeleri ve Yorum Soruları"],
        "İngilizce": ["LGS İngilizce Vocabulary & Reading Comprehension Testleri"]
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
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', text)
    text = text.replace('\\%', '%').replace('$', '').strip()
    return text

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

# --- KENAR ÇUBUĞU (PARAMETRELER) ---
with st.sidebar:
    st.markdown("### 🔮 Sınav Parametreleri")
    st.markdown("---")

    if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
        st.warning("⚠️ `.streamlit/secrets.toml` dosyasına geçerli Gemini API anahtarınızı ekleyin.")

    secili_sinif = st.selectbox("Eğitim Seviyesi:", list(MUGREDAT.keys()))
    sinav_turu = st.selectbox("Sınav Türü:", [
        "Konu Tarama Soruları",
        "Yeni Nesil ve Karma Soru Çeşitleri",
        "Genel Değerlendirme Soruları",
        "LGS Hazırlık Soruları"
    ])

    mevcut_dersler = list(MUGREDAT.get(secili_sinif, {}).keys())
    secili_dersler = st.multiselect("📚 Dersler:", mevcut_dersler, default=mevcut_dersler[:1])

    tum_uniteler = []
    if secili_dersler:
        for d in secili_dersler:
            for u in MUGREDAT[secili_sinif].get(d, []):
                tum_uniteler.append(f"[{d}] {u}")

    secili_uniteler = st.multiselect("📖 Üniteler ve Konular:", tum_uniteler)
    soru_sayisi = st.slider("🔢 Soru Sayısı:", 1, 30, 3)

    st.markdown("---")
    if st.button("🚀 Soru Üretimini Başlat", use_container_width=True, type="primary"):
        if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
            st.error("Geçerli bir API anahtarı bulunamadı!")
        elif not secili_dersler:
            st.error("Lütfen en az bir ders seçiniz!")
        else:
            prompt = f"""
Sen MEB müfredatına ve kazanımlarına tam hakim, alanında uzman profesyonel bir soru hazırlama yapay zekasısın.
{secili_sinif} seviyesinde, {sinav_turu} kapsamında, seçilen dersler ve üniteler doğrultusunda tam {soru_sayisi} adet son derece nitelikli, özgün, mantık hatası içermeyen ve gerçek sınav kalitesinde çoktan seçmeli soru üret.
Seçilen Dersler: {", ".join(secili_dersler)}
Seçilen Üniteler: {", ".join(secili_uniteler) if secili_uniteler else "Tüm müfredat"}

Her soru için mutlaka detaylı bir çözüm açıklaması (cozum_aciklamasi) da ekle.
Yanıtı kesinlikle ve sadece şu JSON formatında ver (başka hiçbir markdown veya metin ekleme):
[
  {{
    "soru_metni": "Soru metni...",
    "secenekler": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "dogru_cevap": "A",
    "cozum_aciklamasi": "Bu sorunun çözüm açıklaması...",
    "ders": "Ders Adı"
  }}
]
"""
            basarili = False
            quiz_data = []
            hata_mesaji = None

            with st.spinner("⏳ Yapay zeka soruları ve çözümleri hazırlıyor..."):
                for _ in range(max(1, len(api_manager.keys))):
                    current_key = api_manager.get_next_key()
                    if not current_key:
                        hata_mesaji = "API anahtarı okunamadı."
                        break
                    try:
                        client = genai.Client(api_key=current_key)
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.7,
                                response_mime_type="application/json"
                            )
                        )
                        if response and response.text:
                            raw_text = response.text.strip()
                            match = re.search(r'(\[.*\]|\{.*\})', raw_text, re.DOTALL)
                            if match:
                                raw_text = match.group(1)
                            parsed = json.loads(raw_text)

                            if isinstance(parsed, dict):
                                quiz_data = [parsed]
                            elif isinstance(parsed, list):
                                quiz_data = parsed

                            if quiz_data:
                                for idx, item in enumerate(quiz_data):
                                    item["soru_no"] = idx + 1
                                    if "ders" not in item:
                                        item["ders"] = secili_dersler[0]
                                basarili = True
                                break
                    except Exception as e:
                        hata_mesaji = str(e)

            if basarili and quiz_data:
                st.session_state.quiz_data = quiz_data
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.exam_started = False
                st.session_state.start_time = None
                st.session_state.total_duration = None
                st.session_state.current_question = 0
                st.success(f"{len(quiz_data)} soru başarıyla üretildi!")
                st.rerun()
            else:
                st.error(f"Hata oluştu: {hata_mesaji}")

# --- ANA İÇERİK EKRANI ---
st.title("🎓 Soru Fabrikası & Tablet Sınav Modülü")
st.markdown("---")

if st.session_state.quiz_data is None:
    st.info("Sol taraftaki panelden ayarlarınızı yapıp **'Soru Üretimini Başlat'** butonuna tıklayarak sorularınızı oluşturun.")

elif not st.session_state.exam_started:
    # --- MODERN BAŞLAT EKRANI ---
    toplam_soru_sayisi = len(st.session_state.quiz_data)
    toplam_sure_sn = toplam_soru_sayisi * 80
    dakika_gosterim = toplam_sure_sn // 60

    st.markdown(f"""
    <div class="custom-card">
        <h2>✨ Sınavınız Hazır!</h2>
        <p style="color: #64748b; font-size: 16px;">Üretilen Soru Sayısı: <b>{toplam_soru_sayisi}</b> | Toplam Süre: <b>{dakika_gosterim} Dakika ({toplam_sure_sn} Saniye)</b></p>
        <p style="color: #64748b; font-size: 14px;">Her soru için ortalama <b>80 saniye</b> süre tanınmaktadır. Sınav esnasında sayaç geriye sayacaktır.</p>
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

    # --- HER SORU İÇİN 80 SANİYE HESABI (TOPLAM SAYAÇ) ---
    toplam_izin_verilen_sure = toplam_soru * 80
    gecen_sn = int(time.time() - st.session_state.start_time)
    kalan_sn = toplam_izin_verilen_sure - gecen_sn

    if kalan_sn <= 0:
        # Süre bittiğinde otomatik bitir
        st.session_state.quiz_submitted = True
        st.session_state.total_duration = f"{toplam_izin_verilen_sure // 60:02d}:00"
        st.rerun()

    kalan_dakika = kalan_sn // 60
    kalan_saniye = kalan_sn % 60

    # Üst Bilgi / Sayaç ve İlerleme Göstergesi
    col_time, col_progress = st.columns([1, 3])
    with col_time:
        st.metric(label="⏳ Kalan Sınav Süresi", value=f"{kalan_dakika:02d}:{kalan_saniye:02d}")
    with col_progress:
        st.write(f"**Soru {curr_idx + 1} / {toplam_soru}**")
        st.progress((curr_idx + 1) / toplam_soru)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TEK SORU GÖSTERİMİ (KART İÇİNDE) ---
    q = quiz_data[curr_idx]
    
    with st.container(border=True):
        st.markdown(f"### Soru {curr_idx + 1} &nbsp;&nbsp;|&nbsp;&nbsp; *{q.get('ders', 'Genel')}*")
        st.markdown("<br>", unsafe_allow_html=True)
        st.write(temizle_latex_metin(q.get("soru_metni", "")))
        st.markdown("<br>", unsafe_allow_html=True)

        secenekler = q.get("secenekler", {})
        keys_list = sorted(secenekler.keys())
        options_list = [f"{k}) {temizle_latex_metin(secenekler[k])}" for k in keys_list]

        kayitli_cevap = st.session_state.user_answers.get(curr_idx, None)
        default_idx = keys_list.index(kayitli_cevap) if kayitli_cevap in keys_list else None

        secim = st.radio(
            label="Cevabınızı seçin:",
            options=options_list,
            index=default_idx,
            key=f"radio_soru_{curr_idx}"
        )

        if secim:
            secilen_harf = secim.split(")")[0].strip()
            st.session_state.user_answers[curr_idx] = secilen_harf

    # Karalama / Çözüm Tahtası
    with st.expander("✍️ Çözüm / Karalama Tahtası (Aç / Kapat)"):
        col1, col2 = st.columns([2, 1])
        with col1:
            pen_color = st.color_picker("Kalem Rengi", "#4F46E5", key=f"color_{curr_idx}")
        with col2:
            pen_width = st.slider("Kalem Kalınlığı", 1, 15, 3, key=f"width_{curr_idx}")

        st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=pen_width,
            stroke_color=pen_color,
            background_color="#FFFFFF",
            height=240,
            width=700,
            drawing_mode="freedraw",
            key=f"canvas_{curr_idx}",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GEZİNME BUTONLARI ---
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
                st.rerun()

    # Sayacın her saniye güncellenmesi için tetikleyici
    time.sleep(1)
    st.rerun()

else:
    # --- SINAV SONUÇ VE KARNE EKRANI ---
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
    c4.metric("⏱️ Toplam Süre", st.session_state.total_duration or "00:00")

    st.markdown("---")
    st.markdown("### 📋 Soru Detayları ve Çözümler")

    for idx, q in enumerate(quiz_data):
        dogru = q.get("dogru_cevap")
        ogrenci = st.session_state.user_answers.get(idx, "Boş")

        renk = "🟢" if ogrenci == dogru else ("⚪" if ogrenci == "Boş" else "🔴")
        with st.container(border=True):
            with st.expander(f"{renk} Soru {idx + 1} | Senin Cevabın: **{ogrenci}** — Doğru Cevap: **{dogru}**"):
                st.write(temizle_latex_metin(q.get("soru_metni", "")))
                st.markdown("<br>", unsafe_allow_html=True)
                secenekler = q.get("secenekler", {})
                for k in sorted(secenekler.keys()):
                    st.write(f"**{k})** {temizle_latex_metin(secenekler[k])}")
                st.markdown("---")
                st.markdown(f"**💡 Çözüm Açıklaması:** {temizle_latex_metin(q.get('cozum_aciklamasi', 'Açıklama bulunamadı.'))}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Yeni Sınav Başlat", use_container_width=True, type="primary"):
        st.session_state.quiz_data = None
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.exam_started = False
        st.session_state.start_time = None
        st.session_state.total_duration = None
        st.session_state.current_question = 0
        st.rerun()
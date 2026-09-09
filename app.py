import streamlit as st
import json
import random
import re
import os
import sys
import time
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas

# --- RENDER / SAYFA AYARI ---
st.set_page_config(
    page_title="Soru Fabrikası & MEB Müfredat Modülü",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "total_duration" not in st.session_state:
    st.session_state.total_duration = None
if "current_question" not in st.session_state:
    st.session_state.current_question = 0

# --- KENAR ÇUBUĞU (PARAMETRELER) ---
st.sidebar.title("🔮 Sınav Parametreleri")

if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
    st.sidebar.warning("⚠️ `.streamlit/secrets.toml` dosyasına geçerli Gemini API anahtarınızı ekleyin.")

secili_sinif = st.sidebar.selectbox("Eğitim Seviyesi:", list(MUGREDAT.keys()))
sinav_turu = st.sidebar.selectbox("Sınav Türü:", [
    "Konu Tarama Soruları",
    "Yeni Nesil ve Karma Soru Çeşitleri",
    "Genel Değerlendirme Soruları",
    "LGS Hazırlık Soruları"
])

mevcut_dersler = list(MUGREDAT.get(secili_sinif, {}).keys())
secili_dersler = st.sidebar.multiselect("📚 Dersler:", mevcut_dersler, default=mevcut_dersler[:1])

tum_uniteler = []
if secili_dersler:
    for d in secili_dersler:
        for u in MUGREDAT[secili_sinif].get(d, []):
            tum_uniteler.append(f"[{d}] {u}")

secili_uniteler = st.sidebar.multiselect("📖 Üniteler ve Konular:", tum_uniteler)
soru_sayisi = st.sidebar.slider("🔢 Soru Sayısı:", 1, 30, 3)

if st.sidebar.button("🚀 Soru Üretimini Başlat", use_container_width=True):
    if not API_KEYS or "buraya_gercek" in API_KEYS[0]:
        st.sidebar.error("Geçerli bir API anahtarı bulunamadı! Lütfen `.streamlit/secrets.toml` dosyasını kontrol edin.")
    elif not secili_dersler:
        st.sidebar.error("Lütfen en az bir ders seçiniz!")
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

        with st.spinner("⏳ Yapay zeka soruları ve çözümleri hazırlıyor, lütfen bekleyin..."):
            for _ in range(max(1, len(api_manager.keys))):
                current_key = api_manager.get_next_key()
                if not current_key:
                    hata_mesaji = "API anahtarı okunamadı."
                    break
                try:
                    genai.configure(api_key=current_key)
                    model = genai.GenerativeModel(
                        model_name="gemini-3.6-flash",
                        generation_config={"temperature": 0.7, "response_mime_type": "application/json"}
                    )
                    response = model.generate_content(prompt)
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
            st.session_state.start_time = time.time()
            st.session_state.total_duration = None
            st.session_state.current_question = 0
            st.success(f"{len(quiz_data)} adet soru başarıyla üretildi!")
            st.rerun()
        else:
            st.error(f"Sorular üretilirken hata oluştu: {hata_mesaji}")

# --- ANA İÇERİK EKRANI ---
st.title("🎓 Soru Fabrikası & Tablet Sınav Modülü")

if st.session_state.quiz_data is None:
    st.info("Sol taraftaki panelden ayarlarınızı yapıp **'Soru Üretimini Başlat'** butonuna tıklayarak sınava başlayabilirsiniz.")
elif not st.session_state.quiz_submitted:
    quiz_data = st.session_state.quiz_data
    toplam_soru = len(quiz_data)
    curr_idx = st.session_state.current_question

    # --- SAYAÇ VE İLERLEME GÖSTERGESİ ---
    if st.session_state.start_time:
        gecen_sn = int(time.time() - st.session_state.start_time)
        dakika = gecen_sn // 60
        saniye = gecen_sn % 60
        col_time, col_progress = st.columns([1, 3])
        with col_time:
            st.metric(label="⏱️ Geçen Süre", value=f"{dakika:02d}:{saniye:02d}")
        with col_progress:
            st.write(f"**Soru {curr_idx + 1} / {toplam_soru}**")
            st.progress((curr_idx + 1) / toplam_soru)

    st.markdown("---")

    # --- TEK SORU GÖSTERİMİ ---
    q = quiz_data[curr_idx]
    st.markdown(f"### Soru {curr_idx + 1} *({q.get('ders', 'Genel')})*")
    st.write(temizle_latex_metin(q.get("soru_metni", "")))

    secenekler = q.get("secenekler", {})
    keys_list = sorted(secenekler.keys())
    options_list = [f"{k}) {temizle_latex_metin(secenekler[k])}" for k in keys_list]

    # Mevcut seçilmiş cevap var mı kontrol et
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
    with st.expander("✍️ Çözüm / Karalama Tahtası"):
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
            height=220,
            width=650,
            drawing_mode="freedraw",
            key=f"canvas_{curr_idx}",
        )

    st.markdown("---")

    # --- GEZİNME BUTONLARI (Önceki / Sonraki / Bitir) ---
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
                if st.session_state.start_time:
                    gecen = int(time.time() - st.session_state.start_time)
                    st.session_state.total_duration = f"{gecen // 60:02d}:{gecen % 60:02d}"
                st.session_state.quiz_submitted = True
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
        with st.expander(f"{renk} Soru {idx + 1}: Senin Cevabın: {ogrenci} | Doğru Cevap: {dogru}"):
            st.write(temizle_latex_metin(q.get("soru_metni", "")))
            secenekler = q.get("secenekler", {})
            for k in sorted(secenekler.keys()):
                st.write(f"**{k})** {temizle_latex_metin(secenekler[k])}")
            st.markdown(f"**💡 Çözüm Açıklaması:** {temizle_latex_metin(q.get('cozum_aciklamasi', 'Açıklama bulunamadı.'))}")

    if st.button("🔄 Yeni Sınav Başlat", use_container_width=True):
        st.session_state.quiz_data = None
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.start_time = None
        st.session_state.total_duration = None
        st.session_state.current_question = 0
        st.rerun()

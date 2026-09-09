import streamlit as st
import json
import random
import re
import os
import sys
import time
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
        "Matematik": ["Doğal Sayılarla İşlemler", "Kesirler", "Ondalık Gösterimler", "Yüzdeler", "Üçgen ve Dörtgenler", "Veri İşleme","Temel Geometrik Kavramlar ve Doğrular"],
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

# --- API ANAHTARLARI VE YÜK DENGELEME ---
API_KEYS = [
    "AIzaSy... (kendi çalışan anahtarınızı buraya yazabilirsiniz)"
]

class APIKeyManager:
    def __init__(self, keys):
        self.keys = [k.strip() for k in keys if k.strip()]
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

# --- KENAR ÇUBUĞU (PARAMETRELER) ---
st.sidebar.title("🔮 Sınav Parametreleri")

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
    if not secili_dersler:
        st.sidebar.error("Lütfen en az bir ders seçiniz!")
    else:
        prompt = f"""
        Sen MEB müfredatına ve kazanımlarına tam hakim, alanında uzman profesyonel bir soru hazırlama yapay zekasısın.
        {secili_sinif} seviyesinde, {sinav_turu} kapsamında, seçilen dersler ve üniteler doğrultusunda tam {soru_sayisi} adet son derece nitelikli, özgün, mantık hatası içermeyen ve gerçek sınav kalitesinde çoktan seçmeli soru üret.
        Seçilen Dersler: {", ".join(secili_dersler)}
        Seçilen Üniteler: {", ".join(secili_uniteler) if secili_uniteler else "Tüm müfredat"}
        
        Her soru için mutlaka detaylı bir çözüm açıklaması (cozum_aciklamasi) da ekle.
        Yanıtı kesinlikle ve sadece şu JSON formatında ver (başka hiçbir açıklama ekleme):
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
        
        import google.generativeai as genai
        basarili = False
        quiz_data = []
        
        with st.spinner("⏳ Yapay zeka soruları ve çözümleri hazırlıyor, lütfen bekleyin..."):
            for _ in range(max(1, len(API_KEYS))):
                current_key = api_manager.get_next_key()
                if not current_key or "AIzaSy..." in current_key:
                    break
                try:
                    genai.configure(api_key=current_key)
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        generation_config={"temperature": 0.75, "response_mime_type": "application/json"}
                    )
                    response = model.generate_content(prompt)
                    if response and response.text:
                        raw_text = response.text.strip()
                        match = re.search(r'(\[.*\]|\{.*\})', raw_text, re.DOTALL)
                        if match:
                            raw_text = match.group(1)
                        quiz_data = json.loads(raw_text)
                        if isinstance(quiz_data, list) and len(quiz_data) > 0:
                            for idx, item in enumerate(quiz_data):
                                item["soru_no"] = idx + 1
                                if "ders" not in item:
                                    item["ders"] = secili_dersler[0]
                            basarili = True
                            break
                except Exception as e:
                    continue

        if basarili and quiz_data:
            st.session_state.quiz_data = quiz_data
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.start_time = time.time()
            st.success(f"{len(quiz_data)} adet soru başarıyla üretildi!")
        else:
            st.error("Lütfen kod içerisindeki `API_KEYS` listesine geçerli Gemini API anahtarınızı ekleyin.")

# --- ANA İÇERİK EKRANI ---
st.title("🎓 Soru Fabrikası & Tablet Sınav Modülü")

if st.session_state.quiz_data is None:
    st.info("Sol taraftaki panelden ayarlarınızı yapıp **'Soru Üretimini Başlat'** butonuna tıklayarak sınava başlayabilirsiniz.")
else:
    quiz_data = st.session_state.quiz_data
    
    # Süre Tutucu / Kronometre Göstergesi
    if not st.session_state.quiz_submitted and st.session_state.start_time:
        gecen_sure = int(time.time() - st.session_state.start_time)
        dakika = gecen_sure // 60
        saniye = gecen_sure % 60
        st.markdown(f"⏱️ **Geçen Süre:** `{dakika:02d}:{saniye:02d}`")
    
    for idx, q in enumerate(quiz_data):
        st.markdown(f"### Soru {idx + 1} *({q.get('ders', 'Genel')})*")
        st.write(temizle_latex_metin(q.get("soru_metni", "")))
        
        secenekler = q.get("secenekler", {})
        options_list = [f"{k}) {temizle_latex_metin(v)}" for k, v in sorted(secenekler.items())]
        keys_list = sorted(secenekler.keys())
        
        current_val = st.session_state.user_answers.get(idx, None)
        default_index = keys_list.index(current_val) if current_val in keys_list else 0
        
        secim = st.radio(
            f"Seçiminizi yapın (Soru {idx + 1}):",
            options_list,
            index=default_index if current_val else 0,
            key=f"q_{idx}"
        )
        
        secilen_harf = secim.split(")")[0].strip()
        st.session_state.user_answers[idx] = secilen_harf

        # Çözüm Açıklaması (Sınav tamamlandıktan sonra görünür)
        if st.session_state.quiz_submitted:
            dogru_cevap = q.get("dogru_cevap")
            ogrenci_cevap = st.session_state.user_answers.get(idx)
            
            if ogrenci_cevap == dogru_cevap:
                st.success(f"✅ Doğru! Cevap: {dogru_cevap}")
            else:
                st.error(f"❌ Yanlış. Senin cevabın: {ogrenci_cevap} | Doğru Cevap: {dogru_cevap}")
            
            with st.expander(f"💡 Soru {idx + 1} - Çözüm Açıklaması"):
                st.write(temizle_latex_metin(q.get("cozum_aciklamasi", "Açıklama bulunmuyor.")))

        # Çözüm İçin Çizim Tahtası (Canvas)
        with st.expander(f"✍️ Soru {idx + 1} - Çözüm / Karalama Tahtası"):
            col1, col2 = st.columns([2, 1])
            with col1:
                pen_color = st.color_picker("Kalem Rengi", "#4F46E5", key=f"color_{idx}")
            with col2:
                pen_width = st.slider("Kalem Kalınlığı", 1, 15, 3, key=f"width_{idx}")
            
            st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=pen_width,
                stroke_color=pen_color,
                background_color="#FFFFFF",
                height=200,
                width=650,
                drawing_mode="freedraw",
                key=f"canvas_{idx}",
            )

        st.markdown("---")

    if not st.session_state.quiz_submitted:
        if st.button("📊 Sınavı Tamamla ve Sonuçları Gör", type="primary", use_container_width=True):
            st.session_state.quiz_submitted = True
            st.rerun()
    else:
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
        st.success(f"Sınav Tamamlandı!\n\n✅ Doğru: {dogru_sayisi}\n❌ Yanlış: {yanlis_sayisi}\n⚪ Boş: {bos_sayisi}")
        
        if st.button("🔄 Yeni Sınav Başlat", use_container_width=True):
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.rerun()
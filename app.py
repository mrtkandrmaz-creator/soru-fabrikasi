import streamlit as st
import google.generativeai as genai
import json

# Tablet ve mobil cihazlara uygun sayfa düzeni
st.set_page_config(page_title="5. Sınıf Yapay Zeka Testi", layout="centered", page_icon="🎓")

# Tablet dokunmatiğine uygun buton ve metin boyutlandırması
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3.2em;
        font-size: 18px !important;
        margin-top: 10px;
        border-radius: 10px;
    }
    .stRadio label {
        font-size: 18px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 5. Sınıf AI Soru Oluşturucu")

# API Key'i Streamlit Secrets üzerinden alma
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

# Sol Menü Ayarları
with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    # Eğer secrets'ta tanımlı değilse kenar çubuğundan yedek girdi sunar
    if not api_key:
        api_key = st.text_input("Gemini API Key Giriniz:", type="password")
        st.caption("Not: Streamlit Secrets ayarlarından ekleyerek bu adımı otomatikleştirebilirsiniz.")
    else:
        st.success("🔑 API Anahtarı yüklendi.")
    
    lesson = st.selectbox(
        "Ders Seçiniz:",
        ["Matematik", "Fen Bilimleri", "Türkçe", "Sosyal Bilgiler", "İngilizce", "Din Kültürü"]
    )
    question_count = st.slider("Soru Sayısı:", min_value=3, max_value=10, value=5)

# Yapay Zekadan 5. Sınıf Seviyesinde Soru Üretme Fonksiyonu
def generate_questions(key, lesson_name, count):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Sen Türkiye 5. Sınıf MEB müfredatına hakim bir öğretmensin.
    Bana {lesson_name} dersinden 5. sınıf seviyesine uygun {count} adet çoktan seçmeli soru hazırla.
    
    Yanıtı SADECE aşağıdaki JSON formatında ver, başka hiçbir açıklama yazısı ekleme:
    [
      {{
        "id": 1,
        "question": "Soru metni buraya",
        "options": ["A şıkkı", "B şıkkı", "C şıkkı", "D şıkkı"],
        "answer": "Doğru olan şıkkın tam metni"
      }}
    ]
    """
    
    response = model.generate_content(prompt)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

# Uygulama Durumlarını (State) Başlatma
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'completed' not in st.session_state:
    st.session_state.completed = False

# SORU ÜRETME BUTONU (BAŞLANGIÇ EKRANI)
if not st.session_state.questions:
    st.info("💡 Dersinizi seçin ve yapay zekanın 5. sınıf müfredatına uygun sorular üretmesi için aşağıdaki butona basın.")
    
    if st.button("✨ Yapay Zeka İle Soruları Hazırla"):
        if not api_key:
            st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets üzerinden ekleyin veya kenar çubuğundan girin.")
        else:
            with st.spinner(f"5. Sınıf {lesson} soruları hazırlanıyor..."):
                try:
                    st.session_state.questions = generate_questions(api_key, lesson, question_count)
                    st.session_state.current_step = 0
                    st.session_state.user_answers = {}
                    st.session_state.completed = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Soru üretilirken bir hata oluştu: {e}")

# TEST TAMAMLANDI EKRANI
elif st.session_state.completed:
    st.balloons()
    st.success("🎉 Test Tamamlandı!")
    
    score = 0
    questions = st.session_state.questions
    for idx, q in enumerate(questions):
        if st.session_state.user_answers.get(idx) == q["answer"]:
            score += 1

    st.metric(label="Başarı Puanınız", value=f"{score} / {len(questions)}")
    
    st.write("---")
    st.subheader("📊 Soru Detayları ve Doğru Cevaplar:")
    for idx, q in enumerate(questions):
        user_ans = st.session_state.user_answers.get(idx, "Boş")
        is_correct = user_ans == q["answer"]
        status = "✅ Doğru" if is_correct else f"❌ Yanlış (Doğru Cevap: {q['answer']})"
        
        st.markdown(f"**Soru {idx+1}:** {q['question']}")
        st.write(f"Cevabınız: *{user_ans}* — **{status}**")
        st.write("")

    if st.button("🔄 Yeni Sorular İle Tekrar Başla"):
        st.session_state.questions = []
        st.session_state.completed = False
        st.rerun()

# TEST EKRANI
else:
    questions = st.session_state.questions
    current_q = questions[st.session_state.current_step]
    
    # İlerleme Çubuğu
    progress = (st.session_state.current_step + 1) / len(questions)
    st.progress(progress)
    st.caption(f"Soru {st.session_state.current_step + 1} / {len(questions)}")

    st.markdown(f"### {current_q['question']}")

    # Şık Seçimi
    selected_option = st.radio(
        "Cevabınızı seçiniz:",
        current_q["options"],
        index=None if st.session_state.current_step not in st.session_state.user_answers 
              else current_q["options"].index(st.session_state.user_answers[st.session_state.current_step])
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.current_step > 0:
            if st.button("⬅️ Önceki Soru"):
                st.session_state.current_step -= 1
                st.rerun()

    with col2:
        if st.session_state.current_step < len(questions) - 1:
            if st.button("Sonraki Soru ➡️"):
                if selected_option:
                    st.session_state.user_answers[st.session_state.current_step] = selected_option
                    st.session_state.current_step += 1
                    st.rerun()
                else:
                    st.warning("Lütfen bir şık seçiniz.")
        else:
            if st.button("Testi Bitir 🏁"):
                if selected_option:
                    st.session_state.user_answers[st.session_state.current_step] = selected_option
                    st.session_state.completed = True
                    st.rerun()
                else:
                    st.warning("Lütfen bir şık seçiniz.")
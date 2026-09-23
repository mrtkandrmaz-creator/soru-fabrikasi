import os
import io
import json
import streamlit as st
from google import genai
from google.genai import types
from docx import Document

# ---------------------------------------------------------
# 1. STREAMLIT SAYFA AYARLARI
# ---------------------------------------------------------
st.set_page_config(
    page_title="MEB 5. Sınıf Soru Hazırlama Asistanı",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 MEB 5. Sınıf Matematik Soru Üretici")
st.caption("MEB müfredatına %100 uyumlu, çözümlü ve indirilmeye hazır test belgesi oluşturucu.")

# ---------------------------------------------------------
# 2. STREAMLIT SECRETS / ORTAM DEĞİŞKENİNDEN API KEY ALMA
# ---------------------------------------------------------
def get_api_key():
    """API Key'i Streamlit secrets veya sistem ortam değişkeninden alır."""
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    elif "GEMINI_API_KEY" in os.environ:
        return os.environ["GEMINI_API_KEY"]
    return None

API_KEY = get_api_key()

# ---------------------------------------------------------
# 3. MEB 5. SINIF MÜFREDAT KAZANIMLARI
# ---------------------------------------------------------
MUFREDAT = {
    "Matematik": {
        "Doğal Sayılar ve İşlemler": [
            "En çok 9 basamaklı doğal sayıları okur ve yazar.",
            "En çok 9 basamaklı doğal sayıların bölüklerini, basamaklarını ve basamak değerlerini belirtir.",
            "Kuralı verilen sayı ve şekil örüntülerinin istenen adımlarını belirler.",
            "Doğal sayılarla toplama ve çıkarma işlemlerini yapar.",
            "En çok üç basamaklı iki doğal sayının çarpma işlemini yapar.",
            "En çok dört basamaklı bir doğal sayıyı, en çok iki basamaklı bir doğal sayıya böler."
        ],
        "Kesirler": [
            "Birim kesirleri sıralar ve sayı doğrusunda gösterir.",
            "Tam sayılı kesrin, bir bileşik kesir; bileşik kesrin de bir tam sayılı kesir olduğunu anlar.",
            "Paydaları eşit veya birinin paydası diğerinin katı olan kesirlerle toplama ve çıkarma işlemleri yapar."
        ],
        "Ondalık Gösterim": [
            "Paydası 10, 100 veya 1000 olan kesirleri ondalık gösterim olarak ifade eder.",
            "Ondalık gösterimi verilen sayıların basamak isimlerini ve basamak değerlerini belirtir.",
            "Ondalık gösterimleri verilen sayıları karşılaştırır ve sıralar."
        ],
        "Yüzdeler": [
            "Yüzde sembolünü (%) anlar ve verilen bir yüzdeyi kesir veya ondalık gösterimle ilişkilendirir.",
            "Bir çokluğun belirtilen bir yüzdesine karşılık gelen miktarını bulur."
        ],
        "Temel Geometrik Kavramlar ve Çizimler": [
            "Doğru, doğru parçası, ışın kavramlarını açıklar ve sembolle gösterir.",
            "Bir noktanın diğer bir noktaya göre konumunu yön ve birim kullanarak ifade eder.",
            "Açı çeşitlerini (dar, dik, geniş, doğru) belirler ve iletki/gönye ile ölçer veya çizer."
        ],
        "Üçgen ve Dörtgenler": [
            "Üçgenleri kenar ve açı özelliklerine göre sınıflandırır.",
            "Dörtgenlerin (paralelkenar, eşkenar dörtgen, yamuk, dikdörtgen, kare) temel özelliklerini belirler.",
            "Üçgen ve dörtgenlerin iç açılarının ölçüleri toplamını belirler ve verilmeyen açıyı bulur."
        ],
        "Veri İşleme ve Ölçme": [
            "Araştırma soruları oluşturur, veri toplar, sıklık tablosu ve sütun grafiği ile gösterir.",
            "Uzunluk ve zaman ölçme birimlerini tanır, dönüştürmeler yapar."
        ]
    }
}

# ---------------------------------------------------------
# 4. YAN MENÜ (SIDEBAR) SEÇİMLERİ
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Soru Üretim Ayarları")
    
    ders = st.selectbox("Ders Seçin", list(MUFREDAT.keys()))
    unite = st.selectbox("Ünite / Konu Seçin", list(MUFREDAT[ders].keys()))
    kazanimlar = MUFREDAT[ders][unite]
    kazanim = st.selectbox("Kazanım Seçin", kazanimlar)
    
    zorluk = st.select_slider("Zorluk Seviyesi", options=["Kolay", "Orta", "Zor", "LGS/Yeni Nesil"])
    soru_sayisi = st.slider("Soru Sayısı", min_value=1, max_value=10, value=5)
    
    st.markdown("---")
    if API_KEY:
        st.success("🔑 API Anahtarı Streamlit Secrets üzerinden bağlandı.")
    else:
        st.error("⚠️ API Key bulunamadı! Lütfen Streamlit Cloud Secrets ayarlarınıza `GEMINI_API_KEY` ekleyin.")

# ---------------------------------------------------------
# 5. YARDIMCI FONKSİYONLAR (WORD VE HTML/PRINT PDF)
# ---------------------------------------------------------
def generate_docx(questions_data, ders_adi, konu_adi):
    """Soruları Microsoft Word (.docx) formatında hazırlar."""
    doc = Document()
    doc.add_heading(f"5. Sınıf {ders_adi} Testi", level=0)
    doc.add_paragraph(f"Konu: {konu_adi}\n")
    
    for i, q in enumerate(questions_data, 1):
        doc.add_heading(f"Soru {i}", level=2)
        doc.add_paragraph(q.get('soru_metni', ''))
        
        secenekler = q.get('secenekler', {})
        for harf in ['A', 'B', 'C', 'D']:
            doc.add_paragraph(f"{harf}) {secenekler.get(harf, '')}")
        doc.add_paragraph()

    doc.add_heading("Cevap Anahtarı ve Çözümler", level=1)
    for i, q in enumerate(questions_data, 1):
        p = doc.add_paragraph()
        p.add_run(f"{i}. Soru Doğru Cevap: {q.get('dogru_cevap', '')}\n").bold = True
        p.add_run(f"Çözüm: {q.get('cozum', '')}\n")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generate_html_printable(questions_data, ders_adi, konu_adi):
    """A4 formatında yazdırılabilir ve PDF olarak kaydedilebilir HTML belgesi üretir."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>5. Sınıf {ders_adi} Testi</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; color: #111; line-height: 1.5; }}
            .header {{ text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; margin-bottom: 20px; }}
            .header h1 {{ color: #1E3A8A; margin: 0; font-size: 22px; }}
            .header h3 {{ color: #4B5563; margin: 5px 0 0 0; font-size: 14px; }}
            .question-box {{ margin-bottom: 20px; page-break-inside: avoid; }}
            .q-title {{ font-weight: bold; margin-bottom: 8px; color: #1F2937; }}
            .options-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-left: 15px; }}
            .solutions {{ margin-top: 40px; page-break-before: always; border-top: 2px dashed #6B7280; padding-top: 20px; }}
            .sol-item {{ margin-bottom: 12px; font-size: 13px; }}
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="margin-bottom: 20px; text-align: right;">
            <button onclick="window.print()" style="padding: 10px 20px; background-color: #1E3A8A; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
                🖨️ Yazdır / PDF Olarak Kaydet
            </button>
        </div>
        
        <div class="header">
            <h1>5. SINIF {ders_adi.upper()} TESTİ</h1>
            <h3>Konu: {konu_adi}</h3>
        </div>
    """
    
    for i, q in enumerate(questions_data, 1):
        sec = q.get('secenekler', {})
        html_content += f"""
        <div class="question-box">
            <div class="q-title">Soru {i}: {q.get('soru_metni', '')}</div>
            <div class="options-grid">
                <div><b>A)</b> {sec.get('A', '')}</div>
                <div><b>B)</b> {sec.get('B', '')}</div>
                <div><b>C)</b> {sec.get('C', '')}</div>
                <div><b>D)</b> {sec.get('D', '')}</div>
            </div>
        </div>
        """
        
    html_content += """
        <div class="solutions">
            <h2 style="color: #1E3A8A; text-align: center;">CEVAP ANAHTARI VE ÇÖZÜMLER</h2>
    """
    
    for i, q in enumerate(questions_data, 1):
        html_content += f"""
        <div class="sol-item">
            <b>{i}. Soru Cevabı: {q.get('dogru_cevap', '')}</b><br>
            <i>Çözüm:</i> {q.get('cozum', '')}
        </div>
        """
        
    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content

# ---------------------------------------------------------
# 6. GEMINI API ILE SORU URETME MOTORU
# ---------------------------------------------------------
def generate_questions_with_gemini(api_key, ders, konu, kazanim, zorluk, soru_sayisi):
    """Google GenAI SDK kullanarak MEB formatında JSON soru listesi oluşturur."""
    client = genai.Client(api_key=api_key)
    
    system_instruction = """
    Sen Türkiye Milli Eğitim Bakanlığı (MEB) 5. Sınıf müfredatına %100 hakim uzman bir öğretmen ve ölçme-değerlendirme uzmanısın.
    Görevin, belirtilen ders, konu ve kazanıma tam uygun, 5. sınıf seviyesine hitap eden sorular hazırlamaktır.
    Cevap formatın SADECE geçerli bir JSON listesi olmalıdır. Ek açıklama veya markdown etiketi ekleme.
    """

    prompt = f"""
    Ders: {ders}
    Ünite/Konu: {konu}
    Hedef Kazanım: {kazanim}
    Zorluk Seviyesi: {zorluk}
    Soru Sayısı: {soru_sayisi}

    Lütfen yukarıdaki kriterlere göre {soru_sayisi} adet 4 seçenekli (A, B, C, D) soru oluştur.

    İstenen JSON Yapısı:
    [
      {{
        "soru_metni": "Soru metni buraya yazılacak.",
        "secenekler": {{
          "A": "A şıkkı",
          "B": "B şıkkı",
          "C": "C şıkkı",
          "D": "D şıkkı"
        }},
        "dogru_cevap": "A/B/C/D harflerinden sadece biri",
        "cozum": "Sorunun adım adım anlaşılır çözümü."
      }}
    ]
    """

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            response_mime_type="application/json"
        ),
    )
    
    return json.loads(response.text)

# ---------------------------------------------------------
# 7. ANA EKRAN VE ISLEM AKISI
# ---------------------------------------------------------
st.markdown("### 🎯 Seçilen Kazanım")
st.info(f"**{unite}** — {kazanim}")

generate_btn = st.button("🚀 Soruları Üret", type="primary", use_container_width=True)

if generate_btn:
    if not API_KEY:
        st.error("❌ API Key bulunamadı! Lütfen Streamlit Cloud Secrets ayarlarınıza `GEMINI_API_KEY` ekleyin.")
    else:
        with st.spinner("MEB müfredatına uygun sorular hazırlanıyor..."):
            try:
                questions = generate_questions_with_gemini(
                    API_KEY, ders, unite, kazanim, zorluk, soru_sayisi
                )
                st.session_state['generated_questions'] = questions
                st.success(f"✅ {len(questions)} adet soru başarıyla üretildi!")
            except Exception as e:
                st.error(f"Soru üretimi sırasında hata oluştu: {str(e)}")

# ---------------------------------------------------------
# 8. SONUÇLAR VE İNDİRME ALANI
# ---------------------------------------------------------
if 'generated_questions' in st.session_state and st.session_state['generated_questions']:
    questions = st.session_state['generated_questions']
    
    st.markdown("---")
    st.subheader("📝 Üretilen Soru Bankası")
    
    tab1, tab2 = st.tabs(["📄 Sorular ve Çözümler", "📥 İndirme ve Yazdırma"])
    
    with tab1:
        for idx, q in enumerate(questions, 1):
            with st.container():
                st.markdown(f"#### Soru {idx}")
                st.write(q.get("soru_metni", ""))
                
                sec = q.get("secenekler", {})
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**A)** {sec.get('A', '')}")
                    st.write(f"**C)** {sec.get('C', '')}")
                with c2:
                    st.write(f"**B)** {sec.get('B', '')}")
                    st.write(f"**D)** {sec.get('D', '')}")
                
                with st.expander("💡 Doğru Cevap ve Detaylı Çözüm"):
                    st.markdown(f"**Doğru Cevap:** `:green[{q.get('dogru_cevap', '')}]`")
                    st.write(f"**Çözüm:** {q.get('cozum', '')}")
                st.divider()

    with tab2:
        st.markdown("#### Test Belgenizi İndirin / Yazdırın")
        
        docx_data = generate_docx(questions, ders, unite)
        html_print_data = generate_html_printable(questions, ders, unite)
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label="📝 Word (.docx) Olarak İndir",
                data=docx_data,
                file_name=f"5_Sinif_{ders}_{unite}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with d_col2:
            st.download_button(
                label="🌐 Yazdırılabilir HTML / PDF Şablonu İndir",
                data=html_print_data,
                file_name=f"5_Sinif_{ders}_{unite}.html",
                mime="text/html",
                use_container_width=True
            )
            
        st.caption("💡 **Not:** İndirdiğiniz HTML belgesini tarayıcınızda açıp 'Yazdır / PDF Olarak Kaydet' butonuna basarak tek tıkla mükemmel düzenli PDF çıktısı alabilirsiniz.")
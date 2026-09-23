import os
import io
import json
import streamlit as st
from google import genai
from google.genai import types
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
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
        st.success("🔑 API Anahtarı Streamlit Secrets üzerinden doğrulandı.")
    else:
        st.error("⚠️ API Key bulunamadı! Lütfen `.streamlit/secrets.toml` dosyasına `GEMINI_API_KEY` ekleyin.")

# ---------------------------------------------------------
# 5. YARDIMCI FONKSİYONLAR (PDF VE DOCX ÜRETİMİ)
# ---------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    """PDF için dinamik sayfa numaralandırması sağlayan alt bilgi canvası."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#666666"))
        self.drawString(40, 20, "MEB 5. Sınıf Soru Bankası - Yapay Zeka Tarafından Oluşturuldu")
        self.drawRightString(555, 20, f"Sayfa {self._pageNumber} / {page_count}")

def generate_pdf(questions_data, ders_adi, konu_adi):
    """Soruları ReportLab kullanarak PDF formatına dönüştürür."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=colors.HexColor("#1E3A8A")
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#4B5563")
    )
    q_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        spaceAfter=6,
        textColor=colors.HexColor("#1F2937")
    )
    opt_style = ParagraphStyle(
        'OptionStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#374151")
    )
    ans_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#065F46")
    )

    story = []
    
    # Başlık
    story.append(Paragraph(f"5. SINIF {ders_adi.upper()} TESTİ", title_style))
    story.append(Paragraph(f"Konu: {konu_adi}", subtitle_style))
    story.append(Spacer(1, 15))

    # Sorular
    for i, q in enumerate(questions_data, 1):
        q_text = f"<b>Soru {i}:</b> {q.get('soru_metni', '')}"
        story.append(Paragraph(q_text, q_style))
        
        secenekler = q.get('secenekler', {})
        opt_a = f"<b>A)</b> {secenekler.get('A', '')}"
        opt_b = f"<b>B)</b> {secenekler.get('B', '')}"
        opt_c = f"<b>C)</b> {secenekler.get('C', '')}"
        opt_d = f"<b>D)</b> {secenekler.get('D', '')}"
        
        table_data = [
            [Paragraph(opt_a, opt_style), Paragraph(opt_b, opt_style)],
            [Paragraph(opt_c, opt_style), Paragraph(opt_d, opt_style)]
        ]
        
        t = Table(table_data, colWidths=[250, 250])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))

    # Cevap Anahtarı ve Çözümler
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>CEVAP ANAHTARI VE ÇÖZÜMLER</b>", title_style))
    story.append(Spacer(1, 10))

    for i, q in enumerate(questions_data, 1):
        dogru_cevap = q.get('dogru_cevap', '')
        cozum = q.get('cozum', '')
        ans_text = f"<b>{i}. Soru Cevabı: {dogru_cevap}</b> - Çözüm: {cozum}"
        story.append(Paragraph(ans_text, ans_style))
        story.append(Spacer(1, 4))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer

def generate_docx(questions_data, ders_adi, konu_adi):
    """Soruları Microsoft Word (.docx) formatında hazırlar."""
    doc = Document()
    doc.add_heading(f"5. Sınıf {ders_adi} Testi", level=0)
    doc.add_paragraph(f"Konu: {konu_adi}")
    
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
        p.add_run(f"Çözüm: {q.get('cozum', '')}")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

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
        st.error("❌ API Key bulunamadı! Lütfen Streamlit secrets veya ortam değişkenlerinizi kontrol edin.")
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
    
    tab1, tab2 = st.tabs(["📄 Sorular ve Çözümler", "📥 İndirme Seçenekleri"])
    
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
        st.markdown("#### Test Belgenizi İndirin")
        
        pdf_data = generate_pdf(questions, ders, unite)
        docx_data = generate_docx(questions, ders, unite)
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label="📄 PDF Olarak İndir",
                data=pdf_data,
                file_name=f"5_Sinif_{ders}_{unite}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with d_col2:
            st.download_button(
                label="📝 Word (.docx) Olarak İndir",
                data=docx_data,
                file_name=f"5_Sinif_{ders}_{unite}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
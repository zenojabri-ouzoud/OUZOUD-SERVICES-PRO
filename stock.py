import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
from gtts import gTTS
import os
import base64
import plotly.express as px

# --- إعدادات المنظر ---
st.set_page_config(page_title="نظام أوزود المتكامل", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: url('https://upload.wikimedia.org/wikipedia/commons/e/e0/Ouzoud_Falls_1.jpg'); 
        background-size: cover;
        background-attachment: fixed;
    }
    .main {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- دوال النظام ---
def play_voice_alert(text):
    tts = gTTS(text=text, lang='ar')
    tts.save("alert.mp3")
    with open("alert.mp3", "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" autoplay="true"></audio>', unsafe_allow_html=True)

def check_stock_level(product_name, qty):
    if qty <= 5:
        alert_msg = f"تنبيه! المنتج {product_name} أوشك على النفاذ، تبقى منه {qty} فقط"
        st.error(alert_msg) 
        play_voice_alert(alert_msg) 

# --- واجهة النظام ---
st.title("🖨️ نظام ورّاقة أوزود - النسخة الشاملة")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🛒 البيع", "📦 المخزون", "💳 الكريدي", "🖨️ الطباعة", "📊 التحقيق المالي", "⚙️ الإعدادات"
])

with tab1:
    st.header("نقطة البيع (POS)")
    scan = st.text_input("امسح الكود (QR/Barcode):")
    qty_sell = st.number_input("الكمية", min_value=1, value=1)
    if st.button("إتمام البيع"):
        if scan:
            st.success(f"تم تسجيل بيع: {scan}")
            play_voice_alert("تم البيع بنجاح")

with tab2:
    st.header("إدارة المخزون")
    p_name = st.text_input("اسم المنتج")
    p_qty = st.number_input("الكمية", min_value=0)
    if st.button("تحديث المخزون"):
        if p_name:
            st.success(f"تم تحديث مخزون '{p_name}'")
            check_stock_level(p_name, p_qty)

with tab3:
    st.header("سجل الكريدي")
    c_name = st.text_input("اسم الزبون")
    c_amt = st.number_input("المبلغ", min_value=0.0)
    if st.button("حفظ الكريدي"):
        st.info(f"تم تسجيل دين لـ {c_name}")

with tab4:
    st.header("الطباعة")
    invoice_client = st.text_input("اسم الزبون للفاتورة:")
    if st.button("إنشاء فاتورة PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(200, 10, txt="Facture - Papeterie Ouzoud", ln=True, align='C')
        pdf.output("invoice.pdf")
        st.success("تم إنشاء الفاتورة!")

with tab5:
    st.header("التقرير المالي")
    df = pd.DataFrame({"المنتج": ["ورق", "أقلام"], "المدخول": [300, 50]})
    fig = px.bar(df, x="المنتج", y="المدخول")
    st.plotly_chart(fig)
    if st.button("تحويل لـ Excel"):
        df.to_excel("data.xlsx")
        st.success("تم الحفظ!")

with tab6:
    st.header("⚙️ الإعدادات")
    if st.button("اختبار الصوت"):
        play_voice_alert("نظام ورّاقة أوزود جاهز للعمل")

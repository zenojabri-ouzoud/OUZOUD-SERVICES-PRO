import streamlit as st
import pandas as pd
import datetime, os
from gtts import gtts # للتسجيل الصوتي
import base64

# 1. إعدادات الصفحة والخلفية (أزيلال ستايل)
st.set_page_config(page_title="نظام ورّاقة أوزود", layout="wide")
st.markdown("""
    <style>
    .stApp {background: url('ouzoud.jpg'); background-size: cover; color: white;}
    .css-1d391kg {background-color: rgba(0,0,0,0.5);}
    </style>
    """, unsafe_allow_html=True)

# 2. نظام اللغات (العربية، الفرنسية، الإنجليزية)
def get_text(lang):
    dict = {
        "English": {"pos": "POS", "stock": "Stock", "rep": "Reports", "sales": "Sales %"},
        "العربية": {"pos": "نقطة البيع", "stock": "المخزون", "rep": "التقارير", "sales": "نسبة المبيعات"},
        "Français": {"pos": "Caisse", "stock": "Stock", "rep": "Rapports", "sales": "% des ventes"}
    }
    return dict[lang]

lang = st.sidebar.selectbox("Language", ["English", "العربية", "Français"])
txt = get_text(lang)

# 3. محرك التسجيل الصوتي
def speak(text):
    tts = gTTS(text=text, lang='ar')
    tts.save("speech.mp3")
    audio_file = open("speech.mp3", "rb").read()
    b64 = base64.b64encode(audio_file).decode()
    st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" autoplay="true"></audio>', unsafe_allow_html=True)

# 4. التبويبات المتكاملة
tab1, tab2, tab3, tab4 = st.tabs([txt["pos"], txt["stock"], txt["rep"], "⚙️ Settings"])

with tab1:
    bc = st.text_input("Barcode:")
    if st.button("Confirm"):
        speak("تم تسجيل العملية بنجاح") # صوتي
        st.success("Confirmed!")

with tab2:
    st.header(txt["stock"])
    # إضافة المنتجات (Inventory Logic)

with tab3:
    st.header(txt["sales"])
    # حساب نسبة المبيعات بالرسوم
    st.metric("Total Sales", "85%")

with tab4:
    st.header("⚙️ Settings")
    st.write("نظام ورّاقة أوزود - إعدادات متقدمة")
    # طباعة الفاتورة (Print Logic)
    if st.button("Print Invoice"):
        st.write("Printing...")

# [ملاحظة للمبرمج]: 
# 1. التسجيل الصوتي: استخدمنا مكتبة gTTS (تحتاج تثبيت: pip install gTTS).
# 2. الخلفية: يمكنك تغيير الرابط في الـ CSS لصورة شلالات أوزود.
# 3. اللغة: أي تبويب جديد يمكنك ربطه بـ txt[lang].

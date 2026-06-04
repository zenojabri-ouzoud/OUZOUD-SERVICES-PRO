import os
import subprocess
import sys

# =========================================================
# 0. نظام التثبيت الذكي والمستقل للمكتبات ف السيرفر
# =========================================================
def install_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        __import__(import_name)
    except ImportError:
        # أمر التثبيت التلقائي ف خلفية السيرفر
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# تشغيل وتثبيت السلعة كاملة أوتوماتيكياً
install_and_import("pandas")
install_and_import("fpdf")
install_and_import("gTTS", "gtts")
install_and_import("openpyxl")
install_and_import("plotly")

# دابا عاد نعيطو ليهم ف النظام
import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
from gtts import gTTS
import base64
import plotly.express as px

# ==========================================
# 1. إعدادات المنظر والخلفية (UI CSS)
# ==========================================
st.set_page_config(page_title="نظام أوزود المتكامل", layout="wide")

st.markdown("""
    <style>
    /* خلفية شلالات أوزود */
    .stApp {
        background: url('https://upload.wikimedia.org/wikipedia/commons/e/e0/Ouzoud_Falls_1.jpg'); 
        background-size: cover;
        background-attachment: fixed;
    }
    /* إطار شفاف بيض للمحتوى باش تبان الكلمات واضحة */
    .main {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. دوال النظام الأساسية (الصوت والمراقبة)
# ==========================================
def play_voice_alert(text):
    """دالة كتحول أي نص لكلام مسموع بالدارجة/العربية"""
    tts = gTTS(text=text, lang='ar')
    tts.save("alert.mp3")
    with open("alert.mp3", "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" autoplay="true"></audio>', unsafe_allow_html=True)

def check_stock_level(product_name, qty):
    """دالة لمراقبة كمية السلعة: إلا وصلات لـ 5 أو قل كتعلمك بالصوت"""
    if qty <= 5:
        alert_msg = f"تنبيه! المنتج {product_name} أوشك على النفاذ، تبقى منه {qty} فقط"
        st.error(alert_msg) 
        play_voice_alert(alert_msg) 

# ==========================================
# 3. واجهة النظام والتبويبات (Tabs)
# ==========================================
st.title("🖨️ نظام ورّاقة أوزود - النسخة الشاملة التفاعلية")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🛒 البيع بالليزر", 
    "📦 المخزون", 
    "💳 الكريدي", 
    "🖨️ الطباعة", 
    "📊 التحقيق المالي", 
    "⚙️ الإعدادات"
])

# --- التبويب 1: البيع بالليزر (QR/Barcode) ---
with tab1:
    st.header("نقطة البيع (POS)")
    st.info("قم بتمرير جهاز الليزر على الباركود أو أدخل الكود يدوياً")
    
    col1, col2 = st.columns(2)
    with col1:
        scan = st.text_input("امسح الكود (QR/Barcode):", key="barcode_scanner")
    with col2:
        qty_sell = st.number_input("الكمية المباعة", min_value=1, value=1)
        
    if st.button("إتمام البيع"):
        if scan:
            st.success(f"تم تسجيل بيع المنتج: {scan} (الكمية: {qty_sell})")
            play_voice_alert("تم البيع بنجاح")
        else:
            st.warning("المرجو مسح الكود أولاً")

# --- التبويب 2: المخزون (بدون ثمن الجملة) ---
with tab2:
    st.header("إدارة المخزون")
    p_name = st.text_input("اسم المنتج / السلعة")
    p_qty = st.number_input("الكمية المتوفرة", min_value=0)
    p_price = st.number_input("ثمن البيع للزبون (درهم)", min_value=0.0)
    
    if st.button("إضافة / تحديث المخزون"):
        if p_name:
            st.success(f"تم تحديث مخزون '{p_name}' بنجاح!")
            check_stock_level(p_name, p_qty) # كيدير التنبيه الصوتي يلا كانت السلعة قليلة
        else:
            st.error("المرجو إدخال اسم المنتج")

# --- التبويب 3: الكريدي ---
with tab3:
    st.header("سجل الديون (الكريدي)")
    c_name = st.text_input("اسم الزبون")
    c_amt = st.number_input("المبلغ المطلوب (درهم)", min_value=0.0)
    
    if st.button("حفظ الكريدي"):
        if c_name:
            st.info(f"تم تسجيل دين بقيمة {c_amt} درهم للزبون: {c_name}")
        else:
            st.warning("أدخل اسم الزبون أولاً")

# --- التبويب 4: الطباعة والفواتير ---
with tab4:
    st.header("مركز الطباعة والفواتير")
    st.write("استخراج الفاتورة بصيغة PDF قابلة للطباعة")
    invoice_client = st.text_input("اسم الزبون للفاتورة:")
    
    if st.button("إنشاء وطباعة فاتورة (PDF)"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(200, 10, txt="Facture - Papeterie Ouzoud", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Client: {invoice_client}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True, align='L')
        pdf.output("invoice_ouzoud.pdf")
        st.success("تم إنشاء الفاتورة بنجاح! يمكنك طباعة ملف (invoice_ouzoud.pdf)")

# --- التبويب 5: التحقيق المالي (المدخول، الرسوم وتصدير Excel) ---
with tab5:
    st.header("التقرير المالي اليومي")
    st.write(f"تاريخ اليوم: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    
    total_today = 850.50 
    st.metric(label="مداخيل اليوم (شحال دخلنا اليوم)", value=f"{total_today} درهم")
    
    st.subheader("📊 المبيعات التفاعلية")
    data = {
        "المنتج": ["ورق A4", "قلم أزرق", "دفتر 64", "أقلام ملونة"],
        "المدخول (درهم)": [300, 50, 400, 100.5]
    }
    df_chart = pd.DataFrame(data)
    
    # رسم بياني تفاعلي بـ Plotly
    fig = px.bar(df_chart, x="المنتج", y="المدخول (درهم)", title="أرباح المنتجات اليوم بالتفصيل", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("تحويل البيانات إلى Excel"):
        df_chart.to_excel("rapport_finance.xlsx", index=False)
        st.success("تم التصدير بنجاح! تم حفظ الملف باسم (rapport_finance.xlsx)")

# --- التبويب 6: الإعدادات ---
with tab6:
    st.header("⚙️ إعدادات النظام")
    lang = st.selectbox("لغة النظام (Language)", ["العربية", "Français", "English"])
    st.write("إصدار النظام: 1.2.0 Pro (Auto-Install Edition)")
    if st.button("اختبار الصوت"):
        play_voice_alert("نظام ورّاقة أوزود التفاعلي جاهز للعمل")

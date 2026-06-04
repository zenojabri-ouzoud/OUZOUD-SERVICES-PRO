import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- نظام الحماية ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 دخول نظام أوزود")
    password = st.text_input("أدخل كلمة المرور:", type="password")
    if st.button("دخول"):
        if password == "Ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("كلمة مرور خاطئة!")
    st.stop()

# --- إعدادات النظام ---
st.set_page_config(page_title="نظام أوزود الشامل", layout="wide")
st.title("🖨️ نظام ورّاقة أوزود - النسخة الموسعة")

# --- التبويبات ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛒 نقطة البيع", "📦 إدارة المخزون", "🖨️ مركز الطباعة", "💰 La Caisse", "⚙️ الإعدادات"])

# 1. البيع
with tab1:
    st.header("🛒 نقطة البيع")
    prod = st.text_input("اسم المنتج")
    price = st.number_input("الثمن (درهم)", min_value=0.0)
    qty = st.number_input("الكمية", min_value=1)
    if st.button("تسجيل البيع"):
        st.success(f"تم بيع {qty} من {prod} بسعر {price * qty} درهم")

# 2. المخزون (بما فيه نوع السلعة)
with tab2:
    st.header("📦 إدارة المخزون")
    name = st.text_input("اسم السلعة")
    type_prod = st.selectbox("نوع السلعة", ["أدوات مكتبية", "أوراق", "أحبار", "أخرى"])
    qr = st.text_input("كود QR")
    curr = st.number_input("الكمية الحالية", min_value=0)
    mini = st.number_input("الحد الأدنى للتنبيه", min_value=1, value=5)
    
    if st.button("حفظ السلعة"):
        st.success(f"تم حفظ {name} (النوع: {type_prod})")
    
    if curr <= mini:
        st.warning(f"⚠️ تنبيه: المنتج '{name}' قرب يسالي!")

# 3. مركز الطباعة (التفاصيل)
with tab3:
    st.header("🖨️ مركز الطباعة الذكي")
    doc_name = st.text_input("اسم الوثيقة")
    service = st.selectbox("الخدمة", ["فوطوكوبي", "طباعة", "سكان"])
    price_page = st.number_input("ثمن الصفحة الواحدة", min_value=0.1)
    pages = st.number_input("عدد الصفحات", min_value=1)
    
    if st.button("حساب وإرسال للطباعة"):
        total = price_page * pages
        st.info(f"المجموع للخدمة: {total} درهم | جاري الطباعة...")

# 4. La Caisse (المداخيل)
with tab4:
    st.header("💰 حساب La Caisse")
    total_sales = st.number_input("إجمالي مبيعات اليوم", min_value=0.0)
    expenses = st.number_input("مصاريف اليوم", min_value=0.0)
    if st.button("حساب الربح الصافي"):
        net = total_sales - expenses
        st.write(f"### الربح الصافي: {net} درهم")

# 5. الإعدادات
with tab5:
    st.header("⚙️ الإعدادات")
    if st.button("خروج"):
        st.session_state.authenticated = False
        st.rerun()

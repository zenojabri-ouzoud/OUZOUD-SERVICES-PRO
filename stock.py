import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- 1. إعدادات النظام ---
st.set_page_config(page_title="نظام أوزود الشامل", layout="wide")

# --- 2. نظام الحماية (Login) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 نظام ورّاقة أوزود - الدخول")
    password = st.text_input("أدخل كود المرور:", type="password")
    if st.button("دخول"):
        if password == "1234": # تقدر تبدل الكود هنا
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("كود خاطئ!")
    st.stop()

# --- 3. الدوال البرمجية ---
def check_stock(name, current_qty, min_qty):
    if current_qty <= min_qty:
        st.warning(f"⚠️ تنبيه! المنتج '{name}' أوشك على النفاذ (باقي فيه {current_qty} فقط)")

# --- 4. الواجهة الرئيسية ---
st.title("🖨️ نظام ورّاقة أوزود الاحترافي")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛒 البيع", "📦 المخزون", "🖨️ مركز الطباعة", "🧾 الفواتير", "⚙️ الإعدادات"])

# تبويب البيع
with tab1:
    st.header("🛒 نقطة البيع (POS)")
    p_name = st.text_input("اسم المنتج للبيع")
    qty_sell = st.number_input("الكمية", min_value=1)
    if st.button("إتمام عملية البيع"):
        st.success(f"تم تسجيل بيع: {qty_sell} قطعة من {p_name}")

# تبويب المخزون
with tab2:
    st.header("📦 إدارة المخزون")
    name = st.text_input("اسم السلعة")
    qr = st.text_input("كود QR / الباركود")
    curr = st.number_input("الكمية الحالية", min_value=0)
    mini = st.number_input("الحد الأدنى للتنبيه", min_value=1, value=5)
    price = st.number_input("السعر", min_value=0.0)
    
    if st.button("حفظ السلعة في المخزون"):
        st.success(f"تم حفظ {name} (باركود: {qr}) في قاعدة البيانات.")
    
    check_stock(name, curr, mini)

# تبويب الطباعة
with tab3:
    st.header("🖨️ مركز الطباعة الذكي")
    service = st.selectbox("نوع الخدمة", ["فوطوكوبي", "طباعة ملفات", "تغليف", "سكان", "تصوير وثائق"])
    docs = st.number_input("عدد الأوراق أو النسخ", min_value=1)
    if st.button("إرسال للطباعة"):
        st.info(f"جاري معالجة: {service} لـ {docs} نسخة...")

# تبويب الفواتير
with tab4:
    st.header("🧾 فواتير الزبناء")
    client_name = st.text_input("اسم الزبون")
    if st.button("إنشاء وطباعة الفاتورة"):
        st.success(f"تم إنشاء فاتورة خاصة بـ {client_name} بنجاح!")

# تبويب الإعدادات
with tab5:
    st.header("⚙️ الإعدادات")
    lang = st.selectbox("اختر اللغة", ["العربية", "Français", "English"])
    if st.button("خروج من النظام"):
        st.session_state.authenticated = False
        st.rerun()

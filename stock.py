import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- الإعدادات العامة ---
st.set_page_config(page_title="OUZOUD-PRO-2026", layout="wide")

# --- نظام الحماية ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 OUZOUD-SERVICES SYSTEM")
    password = st.text_input("كلمة المرور:", type="password")
    if st.button("دخول"):
        if password == "Ouzoud2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ كلمة المرور خاطئة!")
    st.stop()

# --- تهيئة البيانات ---
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])

if 'total_in' not in st.session_state: st.session_state.total_in = 0.0
if 'total_out' not in st.session_state: st.session_state.total_out = 0.0
if 'credit_list' not in st.session_state: 
    st.session_state.credit_list = pd.DataFrame(columns=["الاسم", "المبلغ (DH)", "التاريخ"])

# --- البلوكات ---

def pos_block():
    st.header("🛒 نقطة البيع")
    mode = st.radio("طريقة الإدخال:", ["سكانر (Auto)", "يدوي (Manual)"])
    product_data = None
    if mode == "سكانر (Auto)":
        qr = st.text_input("سكان QR:")
        if qr:
            item = st.session_state.inventory[st.session_state.inventory['QR'] == qr]
            if not item.empty: product_data = item
    else:
        if not st.session_state.inventory.empty:
            prod_name = st.selectbox("اختر المنتج:", st.session_state.inventory['المنتج'].tolist())
            product_data = st.session_state.inventory[st.session_state.inventory['المنتج'] == prod_name]
    
    if product_data is not None and not product_data.empty:
        col1, col2, col3 = st.columns(3)
        with col1: prod_name = st.text_input("المنتج:", value=product_data.iloc[0]['المنتج'])
        with col2: price = st.number_input("الثمن (DH):", value=float(product_data.iloc[0]['الثمن']))
        with col3: qty = st.number_input("الكمية:", min_value=1, value=1)
        st.write(f"### المجموع: {qty * price} DH")
        if st.button("تأكيد البيع"):
            idx = product_data.index[0]
            st.session_state.inventory.at[idx, 'الكمية'] -= qty
            st.success("✅ تم البيع!")

def stock_block():
    st.header("📦 إدارة المخزون")
    st.dataframe(st.session_state.inventory)
    with st.form("add_stock"):
        n = st.text_input("المنتج")
        q = st.number_input("الكمية")
        s = st.text_input("التخصص")
        p = st.number_input("الثمن")
        qr = st.text_input("QR")
        if st.form_submit_button("إضافة"):
            new = pd.DataFrame([[n, qr, q, p, s]], columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new], ignore_index=True)
            st.rerun()

def finance_block():
    st.header("💰 التدبير المالي")
    tab1, tab2 = st.tabs(["📊 الكيس", "💳 الديون"])
    with tab1:
        in_v = st.number_input("مبلغ الدخل:", 0.0)
        if st.button("إضافة للمداخيل"): st.session_state.total_in += in_v
        out_v = st.number_input("مبلغ المصاريف:", 0.0)
        if st.button("إضافة للمصاريف"): st.session_state.total_out += out_v
        st.write(f"### الأرباح الصافية: {st.session_state.total_in - st.session_state.total_out} DH")
    with tab2:
        st.dataframe(st.session_state.credit_list)
        # كود الديون هنا...

def settings_block():
    st.header("⚙️ الإعدادات")
    st.selectbox("اللغة:", ["العربية", "Français", "English"])
    if st.button("خروج"):
        st.session_state.auth = False
        st.rerun()

# --- القائمة الجانبية ---
menu = st.sidebar.radio("الخدمات:", ["🛒 نقطة البيع", "📦 المخزون", "💰 التدبير المالي", "⚙️ الإعدادات"])

if menu == "🛒 نقطة البيع": pos_block()
elif menu == "📦 المخزون": stock_block()
elif menu == "💰 التدبير المالي": finance_block()
elif menu == "⚙️ الإعدادات": settings_block()

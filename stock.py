import streamlit as st
import pandas as pd

# 1. الإعدادات الأساسية
PASSWORD = "ouzoud2026"
LANGUAGES = {
    "العربية": {"Title": "نظام أوزود للتسيير", "POS": "نقطة البيع", "Stock": "المخزون", "Print": "الطباعة", "Credit": "الكريديات", "Cash": "لاكيس"},
    "Français": {"Title": "Système de Gestion Ouzoud", "POS": "Point de Vente", "Stock": "Stock", "Print": "Impression", "Credit": "Crédits", "Cash": "Caisse"},
    "English": {"Title": "Ouzoud Management System", "POS": "POS", "Stock": "Inventory", "Print": "Printing", "Credit": "Credits", "Cash": "Cash Register"}
}

if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "lang" not in st.session_state: st.session_state.lang = "العربية"
if "inventory" not in st.session_state: st.session_state.inventory = pd.DataFrame(columns=["الاسم", "الثمن", "الكمية", "الباركود"])
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["الزبون", "المبلغ"])

st.title(LANGUAGES[st.session_state.lang]["Title"])
st.sidebar.selectbox("Language", list(LANGUAGES.keys()), key="lang")

# 2. الحماية
if not st.session_state.authenticated:
    if st.text_input("كلمة المرور:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
else:
    menu = st.sidebar.selectbox("القائمة", [LANGUAGES[st.session_state.lang][k] for k in ["POS", "Stock", "Print", "Credit", "Cash"]])
    
    # 3. المنطق (الوحش)
    if menu == LANGUAGES[st.session_state.lang]["POS"]:
        st.header("🛒 " + menu)
        method = st.radio("طريقة البيع:", ["عادي (بالاسم)", "سكانر (باركود)"])
        name = st.selectbox("اختر المنتج:", st.session_state.inventory['الاسم'].tolist()) if method == "عادي (بالاسم)" else st.text_input("سكان الباركود:")
        qty = st.number_input("الكمية:", min_value=1)
        if st.button("إتمام البيع"):
            st.success("✅ تم البيع")
            st.markdown("---")
            st.write(f"🧾 **الفاتورة:** {name} | الكمية: {qty}")
            
    elif menu == LANGUAGES[st.session_state.lang]["Stock"]:
        st.header("📦 " + menu)
        with st.form("add"):
            n, p, q, b = st.text_input("الاسم"), st.number_input("الثمن"), st.number_input("الكمية"), st.text_input("الباركود")
            if st.form_submit_button("إضافة للمخزون"):
                st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[n, p, q, b]], columns=["الاسم", "الثمن", "الكمية", "الباركود"])])
                st.rerun()
        st.table(st.session_state.inventory)
        
    elif menu == LANGUAGES[st.session_state.lang]["Print"]:
        st.header("🖨️ " + menu)
        pages = st.number_input("عدد الأوراق:", min_value=1)
        st.subheader(f"💰 التمن النهائي: {pages * 0.5} درهم")
        if st.button("طبع"): st.info("جاري الطباعة...")
            
    elif menu == LANGUAGES[st.session_state.lang]["Credit"]:
        st.header("💳 " + menu)
        cust, amt = st.text_input("اسم الزبون:"), st.number_input("المبلغ:")
        if st.button("تسجيل"):
            st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[cust, amt]], columns=["الزبون", "المبلغ"])])
        st.table(st.session_state.credits)

    elif menu == LANGUAGES[st.session_state.lang]["Cash"]:
        st.header("💰 " + menu)
        st.metric("مجموع الديون (الكريديات):", f"{st.session_state.credits['المبلغ'].sum()} درهم")

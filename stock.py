import streamlit as st
import pandas as pd

# 1. القاموس (Dictionary) للغات
LANGUAGES = {
    "العربية": {
        "Title": "نظام أوزود للتسيير", "POS": "نقطة البيع", "Stock": "إدارة المخزون", 
        "Print": "خدمات الطباعة", "Credit": "الكريديات", "Cash": "لاكيس",
        "Select": "اختر المنتج:", "Qty": "الكمية:", "BtnSell": "إتمام البيع", 
        "PricePage": "الثمن للورقة (درهم):", "Pages": "عدد الأوراق:", "Total": "التمن النهائي:", "Add": "إضافة"
    },
    "Français": {
        "Title": "Système de Gestion Ouzoud", "POS": "Point de Vente", "Stock": "Gestion de Stock", 
        "Print": "Impression", "Credit": "Crédits", "Cash": "Caisse",
        "Select": "Sélectionner le produit:", "Qty": "Quantité:", "BtnSell": "Confirmer la vente", 
        "PricePage": "Prix par page (DH):", "Pages": "Nombre de pages:", "Total": "Total final:", "Add": "Ajouter"
    },
    "English": {
        "Title": "Ouzoud Management System", "POS": "POS System", "Stock": "Inventory", 
        "Print": "Printing Services", "Credit": "Credits", "Cash": "Cash Register",
        "Select": "Select product:", "Qty": "Quantity:", "BtnSell": "Confirm Sale", 
        "PricePage": "Price per page (DH):", "Pages": "Number of pages:", "Total": "Total:", "Add": "Add"
    }
}

# 2. التهيئة
if "lang" not in st.session_state: st.session_state.lang = "العربية"
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = pd.DataFrame(columns=["الاسم", "الثمن", "الكمية"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0

# 3. الواجهة
st.sidebar.selectbox("Language / Langue / اللغة", list(LANGUAGES.keys()), key="lang")
curr = LANGUAGES[st.session_state.lang]
st.title(curr["Title"])

if not st.session_state.authenticated:
    if st.text_input("Password:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
else:
    menu = st.sidebar.selectbox("Menu", [curr["POS"], curr["Stock"], curr["Print"], curr["Credit"], curr["Cash"]])
    
    if menu == curr["POS"]:
        st.header(menu)
        if not st.session_state.inventory.empty:
            name = st.selectbox(curr["Select"], st.session_state.inventory['الاسم'].tolist())
            qty = st.number_input(curr["Qty"], min_value=1)
            if st.button(curr["BtnSell"]): st.success("✅ Done!")
            
    elif menu == curr["Stock"]:
        st.header(menu)
        with st.form("add"):
            n, p, q = st.text_input("Name"), st.number_input("Price"), st.number_input("Qty")
            if st.form_submit_button(curr["Add"]):
                st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[n, p, q]], columns=["الاسم", "الثمن", "الكمية"])])
                st.rerun()
        st.table(st.session_state.inventory)

    elif menu == curr["Print"]:
        st.header(menu)
        pp = st.number_input(curr["PricePage"], value=0.50)
        pages = st.number_input(curr["Pages"], min_value=1)
        st.subheader(f"{curr['Total']} {pages * pp} DH")
        
    elif menu == curr["Cash"]:
        st.header(menu)
        st.metric("Total", f"{st.session_state.sales_total} DH")

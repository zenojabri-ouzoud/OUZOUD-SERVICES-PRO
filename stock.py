import streamlit as st
import pandas as pd
import shutil
import os

# الدالة اللي كتحفظ
def save_to_excel(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    with pd.ExcelWriter(file_name, mode='a' if os.path.exists(file_name) else 'w', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# 1. تهيئة النظام
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False 
if "inventory" not in st.session_state: 
    st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["Client", "Montant"])
if "last_receipt" not in st.session_state: st.session_state.last_receipt = ""

st.title("Système de Gestion Ouzoud Pro")

# 2. الحماية هي الأولى
if not st.session_state.authenticated:
    if st.text_input("Mot de passe:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.warning("Veuillez entrer le mot de passe.")
        st.stop()

# 3. المنيو (بعد تجاوز الحماية)
menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Crédits", "Caisse"])

if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    # ... (الكود ديالك) ...
    # زر الحفظ الخاص بالبيع
    if st.button("💾 Enregistrer les Ventes dans Excel"):
        sale_df = pd.DataFrame({'Total_Sales': [st.session_state.sales_total]})
        save_to_excel(sale_df, "Ventes")
        st.success("تم الحفظ!")

elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    # ... (الكود ديالك) ...
    # زر الحفظ الخاص بالستوك
    if st.button("💾 Enregistrer le Stock dans Excel"):
        save_to_excel(st.session_state.inventory, "Stock")
        st.success("تم حفظ الستوك!")
    st.table(st.session_state.inventory)

elif menu == "Impression":
    st.header("🖨️ Service Impression")
    # ... (الكود ديالك) ...

elif menu == "Crédits":
    st.header("💳 Gestion des Crédits")
    c_n, c_a = st.text_input("Client"), st.number_input("Montant")
    if st.button("Ajouter Crédit"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[c_n, c_a]], columns=["Client", "Montant"])])
    
    # زر الحفظ الخاص بالكريديات
    if st.button("💾 Enregistrer les Crédits dans Excel"):
        save_to_excel(st.session_state.credits, "Crédits")
        st.success("تم حفظ الكريديات!")
    st.table(st.session_state.credits)

elif menu == "Caisse":
    st.header("💰 Caisse & Dashboard")
    # ... (الكود ديالك) ...
    

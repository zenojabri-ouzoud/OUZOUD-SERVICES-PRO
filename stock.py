import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- الإعدادات العامة ---
st.set_page_config(layout="wide")

# --- دالة الحفظ الذكية في Excel ---
def save_to_excel(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    try:
        if os.path.exists(file_name):
            with pd.ExcelWriter(file_name, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            with pd.ExcelWriter(file_name, mode='w', engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        st.success(f"Données enregistrées dans {sheet_name} avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement: {e}")

# --- تهيئة الذاكرة ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
if "cart" not in st.session_state: st.session_state.cart = []
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0

# --- الحماية (Connexion) ---
if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026": # تقدر تبدلو هنا
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Factures", "Gestion Stock", "Impression", "Caisse", "Credits"])

# --- 1. Point de Vente ---
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Type de vente:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier"])
    
    if mode == "Panier":
        col1, col2 = st.columns([1, 1])
        with col1:
            code = st.text_input("Code-barres:")
            qty = st.number_input("Quantité:", min_value=1)
            if st.button("✅ Ajouter au Panier"):
                st.session_state.cart.append({"Code": code, "Quantité": qty, "Total": 10.0 * qty})
                st.rerun()
        with col2:
            if st.session_state.cart:
                st.table(pd.DataFrame(st.session_state.cart))
                if st.button("🖨️ Valider et Enregistrer (Facture)"):
                    save_to_excel(pd.DataFrame(st.session_state.cart), "Factures_History")
                    st.session_state.cart = []
                    st.rerun()

# --- 2. Factures ---
elif menu == "Factures":
    st.header("📄 Historique des Factures")
    if st.button("💾 Sauvegarder Factures dans Excel"): save_to_excel(pd.DataFrame(), "Factures")

# --- 3. Gestion Stock ---
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Valider et Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder Stock dans Excel"): save_to_excel(st.session_state.inventory, "Stock")

# --- 4. Impression (مصلحة ومقادة) ---
elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p = st.number_input("Prix par page (DH):")
    n = st.number_input("Nombre de pages:", 1)
    if st.button("✅ Valider Impression"):
        st.success(f"Total à payer: {p * n} DH")
    if st.button("💾 Sauvegarder Impression dans Excel"):
        save_to_excel(pd.DataFrame([{"Prix": p, "N": n, "Total": p * n}]), "Impression")

# --- 5. Caisse ---
elif menu == "Caisse":
    st.header("💰 Caisse")
    if st.button("💾 Sauvegarder Caisse"): save_to_excel(pd.DataFrame([{"Date": datetime.now()}]), "Caisse")

# --- 6. Credits ---
elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client, montant = st.text_input("Nom du Client"), st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[client, montant]], columns=["Client", "Montant"])], ignore_index=True)
        st.rerun()
    if st.button("💾 Sauvegarder Crédits"): save_to_excel(st.session_state.credits, "Credits")

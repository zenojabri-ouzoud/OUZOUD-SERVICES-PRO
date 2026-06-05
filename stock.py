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

# --- دالة إنشاء فاتورة PDF ---
def generate_pdf(cart_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Facture Ouzoud 2026", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(10)
    for item in cart_data:
        pdf.cell(200, 10, txt=f"{item['Code']} | Qté: {item['Quantité']} | Total: {item['Total']} DH", ln=True)
    file_path = "facture.pdf"
    pdf.output(file_path)
    return file_path

# --- دالة تحميل البيانات ---
def load_data(sheet_name):
    if os.path.exists('ouzoud_data.xlsx'):
        try: return pd.read_excel('ouzoud_data.xlsx', sheet_name=sheet_name)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- تهيئة الذاكرة ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = load_data("Stock")
if "cart" not in st.session_state: st.session_state.cart = []
if "credits" not in st.session_state: st.session_state.credits = load_data("Credits")
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0

# --- الحماية ---
if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Factures", "Gestion Stock", "Impression", "Caisse", "Credits"])

# --- 1. Point de Vente ---
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Panier Rapide")
        code = st.text_input("Scanner le Code-barres:")
        qty = st.number_input("Quantité:", min_value=1, step=1)
        if st.button("✅ Ajouter au Panier"):
            st.session_state.cart.append({"Code": code, "Quantité": qty, "Prix": 10.0, "Total": 10.0 * qty})
            st.rerun()
    with col2:
        st.subheader("🛒 Votre Panier")
        if st.session_state.cart:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.table(cart_df)
            if st.button("🖨️ Valider et Enregistrer (Facture)"):
                st.session_state.sales_total += cart_df['Total'].sum()
                save_to_excel(cart_df, "Factures_History")
                st.session_state.cart = []
                st.success("Facture enregistrée !")
                st.rerun()

# --- 2. Factures ---
elif menu == "Factures":
    st.header("📄 Historique des Factures")
    if st.session_state.cart:
        if st.button("🖨️ Imprimer la dernière Facture en PDF"):
            pdf_path = generate_pdf(st.session_state.cart)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button("📥 Télécharger le PDF", pdf_file, "facture.pdf", "application/pdf")
    if st.button("💾 Sauvegarder Factures dans Excel"): save_to_excel(pd.DataFrame(), "Factures")

# --- 3. Gestion Stock ---
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder Stock dans Excel"): save_to_excel(st.session_state.inventory, "Stock")

# --- 4. Impression ---
elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p, n = st.number_input("Prix/Page"), st.number_input("Nombre", 1)
    if st.button("Enregistrer Impression"):
        st.session_state.sales_total += (p * n)
        st.success("Impression enregistrée")
    if st.button("💾 Sauvegarder Impression"): save_to_excel(pd.DataFrame([{"Prix": p, "N": n}]), "Impression")

# --- 5. Caisse ---
elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total", f"{st.session_state.sales_total} DH")
    if st.button("💾 Sauvegarder Caisse"): save_to_excel(pd.DataFrame([{"Total": st.session_state.sales_total}]), "Caisse")

# --- 6. Credits ---
elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client, montant = st.text_input("Nom du Client"), st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[client, montant]], columns=["Client", "Montant"])], ignore_index=True)
        st.rerun()
    st.table(st.session_state.credits)
    if st.button("💾 Sauvegarder Crédits"): save_to_excel(st.session_state.credits, "Credits")

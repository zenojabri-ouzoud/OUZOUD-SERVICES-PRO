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
if "last_cart" not in st.session_state: st.session_state.last_cart = None
if "system_notes" not in st.session_state: st.session_state.system_notes = "" # الخانة الجديدة

# --- الحماية ---
if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Caisse", "Credits"])

# --- 1. Point de Vente ---
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Type de vente:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier"])
    
    if mode == "Vente Normale":
        prod = st.text_input("Produit:")
        qty = st.number_input("Quantité:", min_value=1)
        if st.button("Valider Vente Normale"): st.success("Validé")
        
    elif mode == "Scan QR":
        scan = st.text_input("Scanner le Code-barres:")
        if st.button("Valider Scan QR"): st.success("Validé")
        
    elif mode == "Vente Libre":
        qty = st.number_input("Quantité:", min_value=1)
        prix = st.number_input("Prix:")
        code_opt = st.text_input("Code-barres (Optionnel):")
        if st.button("Valider Vente Libre"): st.success("Validé")
        
    elif mode == "Panier":
        col1, col2 = st.columns([1, 1])
        with col1:
            code = st.text_input("Scanner le Code-barres:")
            qty = st.number_input("Quantité:", min_value=1, step=1)
            if st.button("✅ Ajouter au Panier"):
                st.session_state.cart.append({"Code": code, "Quantité": qty, "Prix": 10.0, "Total": 10.0 * qty})
                st.rerun()
        with col2:
            if st.session_state.cart:
                st.table(pd.DataFrame(st.session_state.cart))
                if st.button("🖨️ Valider et Enregistrer (Facture)"):
                    st.session_state.last_cart = st.session_state.cart
                    # --- التعديل هنا: السيستم كيكتب فـ system_notes ---
                    items_str = "\n".join([f"{i['Code']} | {i['Quantité']} | {i['Total']} DH" for i in st.session_state.cart])
                    st.session_state.system_notes = f"Facture du {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n{items_str}\nTotal: {pd.DataFrame(st.session_state.cart)['Total'].sum()} DH"
                    
                    st.session_state.sales_total += pd.DataFrame(st.session_state.cart)['Total'].sum()
                    save_to_excel(pd.DataFrame(st.session_state.cart), "Factures_History")
                    st.session_state.cart = []
                    st.rerun()
    
    # --- العناصر التي تظهر دائماً في جميع حالات البيع ---
    st.divider()
    # الخانة كتقرا دابا من system_notes
    st.text_area("Espace système (Détails):", value=st.session_state.system_notes, height=150)
    if st.button("🖨️ Imprimer en PDF"):
        if st.session_state.last_cart:
            pdf_path = generate_pdf(st.session_state.last_cart)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button("📥 Télécharger le PDF", pdf_file, "facture.pdf", "application/pdf")
        else:
            st.warning("Aucune vente validée récemment pour imprimer !")

# --- 2. Gestion Stock ---
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder Stock dans Excel"): save_to_excel(st.session_state.inventory, "Stock")

# --- 3. Impression ---
elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p, n = st.number_input("Prix/Page"), st.number_input("Nombre", 1)
    if st.button("Enregistrer Impression"):
        st.session_state.sales_total += (p * n)
        st.success("Impression enregistrée")
    if st.button("💾 Sauvegarder Impression dans Excel"): save_to_excel(pd.DataFrame([{"Prix": p, "N": n}]), "Impression")

# --- 4. Caisse ---
elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total", f"{st.session_state.sales_total} DH")
    if st.button("💾 Sauvegarder Caisse dans Excel"): save_to_excel(pd.DataFrame([{"Total": st.session_state.sales_total}]), "Caisse")

# --- 5. Credits ---
elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client, montant = st.text_input("Nom du Client"), st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[client, montant]], columns=["Client", "Montant"])], ignore_index=True)
        st.rerun()
    st.table(st.session_state.credits)
    if st.button("💾 Sauvegarder Crédits dans Excel"): save_to_excel(st.session_state.credits, "Credits")

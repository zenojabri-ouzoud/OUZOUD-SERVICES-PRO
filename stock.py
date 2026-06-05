import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

def save_to_excel(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    mode = 'a' if os.path.exists(file_name) else 'w'
    with pd.ExcelWriter(file_name, mode=mode, if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Ouzoud Services - Facture", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=text)
    return pdf.output(dest='S').encode('latin-1')

if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
if "invoices_db" not in st.session_state: st.session_state.invoices_db = pd.DataFrame(columns=["Date", "Détails", "Total"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["Client", "Montant"])

st.title("Système de Gestion Ouzoud Pro")

if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Factures", "Impression", "Crédits", "Caisse"])

if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Mode:", ["Vente Normale", "Scan QR", "Vente Libre"])
    
    if mode == "Vente Normale":
        prod = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist()) if not st.session_state.inventory.empty else st.warning("Stock vide")
        qty = st.number_input("Quantité:", min_value=1)
        if st.button("Valider"):
            price = st.session_state.inventory[st.session_state.inventory['Nom'] == prod].iloc[0]['Prix']
            total = price * qty
            st.session_state.sales_total += total
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            details = f"Ouzoud Services\nDate: {date}\nProduit: {prod}\nQté: {qty}\nTotal: {total} DH"
            st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[date, details, total]], columns=["Date", "Détails", "Total"])])
            st.success("Vente enregistrée !")

    elif mode == "Scan QR":
        scan = st.text_input("Scanner le code:")
        if scan:
            row = st.session_state.inventory[st.session_state.inventory['Code-barres'] == scan]
            if not row.empty:
                if st.button("Valider le Scan"):
                    st.session_state.sales_total += row.iloc[0]['Prix']
                    details = f"Ouzoud Services\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nProduit: {row.iloc[0]['Nom']}\nTotal: {row.iloc[0]['Prix']} DH"
                    st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[datetime.now().strftime('%Y-%m-%d %H:%M'), details, row.iloc[0]['Prix']]], columns=["Date", "Détails", "Total"])])
                    st.success("Scanné !")

    elif mode == "Vente Libre":
        desc = st.text_input("Description:")
        prix_l = st.number_input("Prix:")
        if st.button("Valider"):
            st.session_state.sales_total += prix_l
            details = f"Ouzoud Services\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nProduit: {desc}\nTotal: {prix_l} DH"
            st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[datetime.now().strftime('%Y-%m-%d %H:%M'), details, prix_l]], columns=["Date", "Détails", "Total"])])
            st.success("Vente Libre validée !")

elif menu == "Factures":
    st.header("🧾 Gestion des Factures")
    if not st.session_state.invoices_db.empty:
        selected_date = st.selectbox("Choisir une facture par date:", st.session_state.invoices_db['Date'].tolist())
        facture = st.session_state.invoices_db[st.session_state.invoices_db['Date'] == selected_date].iloc[0]
        
        st.text_area("Détails de la facture:", value=facture['Détails'], height=200)
        
        st.download_button(
            label="🖨️ Imprimer en PDF",
            data=generate_pdf(facture['Détails']),
            file_name=f"Facture_{selected_date.replace(':', '-')}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Aucune facture disponible.")
    
    if st.button("💾 Sauvegarder Factures Excel"):
        save_to_excel(st.session_state.invoices_db, "Factures")
        st.success("Sauvegardé !")

elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])])
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder Stock Excel"):
        save_to_excel(st.session_state.inventory, "Stock")
        st.success("Sauvegardé !")

elif menu == "Impression":
    st.header("🖨️ Impression")
    pp = st.number_input("Prix par page")
    pages = st.number_input("Nombre de pages")
    if st.button("Enregistrer"):
        st.session_state.sales_total += (pages * pp)
        st.success("Enregistré")

elif menu == "Crédits":
    st.header("💳 Crédits")
    cn, ca = st.text_input("Client"), st.number_input("Montant")
    if st.button("Ajouter"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[cn, ca]], columns=["Client", "Montant"])])
    st.table(st.session_state.credits)
    if st.button("💾 Sauvegarder Crédits Excel"):
        save_to_excel(st.session_state.credits, "Crédits")
        st.success("Sauvegardé !")

elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total des Ventes", f"{st.session_state.sales_total} DH")
    if st.button("Réinitialiser"):
        st.session_state.sales_total = 0.0
        st.rerun()

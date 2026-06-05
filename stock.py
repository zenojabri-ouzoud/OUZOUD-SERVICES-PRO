import streamlit as st
import pandas as pd
import shutil
import os
from fpdf import FPDF
from datetime import datetime

def save_to_excel(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    if os.path.exists(file_name):
        mode = 'a'
    else:
        mode = 'w'
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

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])

if "invoices_db" not in st.session_state:
    st.session_state.invoices_db = pd.DataFrame(columns=["Date", "Détails", "Total"])

if "sales_total" not in st.session_state:
    st.session_state.sales_total = 0.0

if "credits" not in st.session_state:
    st.session_state.credits = pd.DataFrame(columns=["Client", "Montant"])

if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = ""

st.title("Système de Gestion Ouzoud Pro")

if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    st.stop()

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Crédits", "Caisse"])

if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Mode:", ["Vente Normale", "Scan QR/Code-barres", "Vente Libre"])
    
    if mode == "Vente Normale":
        if not st.session_state.inventory.empty:
            prod = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
            qty = st.number_input("Quantité:", min_value=1)
            if st.button("Valider"):
                idx = st.session_state.inventory[st.session_state.inventory['Nom'] == prod].index[0]
                price = st.session_state.inventory.at[idx, 'Prix']
                total = price * qty
                st.session_state.sales_total += total
                date = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.last_receipt = f"Ouzoud Services\nDate: {date}\nProduit: {prod}\nQté: {qty}\nTotal: {total} DH"
                new_inv = pd.DataFrame([[date, st.session_state.last_receipt, total]], columns=["Date", "Détails", "Total"])
                st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, new_inv])
                st.success("Vente effectuée !")
    
    elif mode == "Scan QR/Code-barres":
        scan = st.text_input("Scanner le code ici:")
        if scan:
            prod_row = st.session_state.inventory[st.session_state.inventory['Code-barres'] == scan]
            if not prod_row.empty:
                st.write(f"Produit: {prod_row.iloc[0]['Nom']} | Prix: {prod_row.iloc[0]['Prix']} DH")
                if st.button("Valider le Scan"):
                    total = prod_row.iloc[0]['Prix']
                    st.session_state.sales_total += total
                    date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.last_receipt = f"Ouzoud Services\nDate: {date}\nProduit: {prod_row.iloc[0]['Nom']}\nTotal: {total} DH"
                    new_inv = pd.DataFrame([[date, st.session_state.last_receipt, total]], columns=["Date", "Détails", "Total"])
                    st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, new_inv])
                    st.success("Vente scannée !")
            else:
                st.error("Code non trouvé")
    
    else:
        desc = st.text_input("Description:")
        prix_l = st.number_input("Prix:")
        if st.button("Valider"):
            st.session_state.sales_total += prix_l
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.last_receipt = f"Ouzoud Services\nDate: {date}\nProduit: {desc}\nTotal: {prix_l} DH"
            new_inv = pd.DataFrame([[date, st.session_state.last_receipt, prix_l]], columns=["Date", "Détails", "Total"])
            st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, new_inv])
            st.success("Vente Libre !")

    if st.session_state.last_receipt:
        st.subheader("🧾 Facture:")
        st.text_area("Détails:", value=st.session_state.last_receipt, height=150)
        st.download_button("🖨️ Imprimer en PDF", generate_pdf(st.session_state.last_receipt), "facture.pdf", "application/pdf")
        if st.button("💾 Enregistrer Factures Excel"):
            save_to_excel(st.session_state.invoices_db, "Factures")
            st.success("Factures sauvegardées !")

elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            new_row = pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder Stock Excel"):
        save_to_excel(st.session_state.inventory, "Stock")
        st.success("Stock sauvegardé !")

elif menu == "Impression":
    st.header("🖨️ Impression")
    pp = st.number_input("Prix par page")
    pages = st.number_input("Nombre de pages")
    if st.button("Enregistrer"):
        st.session_state.sales_total += (pages * pp)
        st.success("Enregistré")
    if st.button("💾 Sauvegarder Impressions Excel"):
        save_to_excel(pd.DataFrame({'Total': [st.session_state.sales_total]}), "Impression")
        st.success("Données enregistrées !")

elif menu == "Crédits":
    st.header("💳 Crédits")
    cn, ca = st.text_input("Client"), st.number_input("Montant")
    if st.button("Ajouter"):
        new_c = pd.DataFrame([[cn, ca]], columns=["Client", "Montant"])
        st.session_state.credits = pd.concat([st.session_state.credits, new_c], ignore_index=True)
    st.table(st.session_state.credits)
    if st.button("💾 Sauvegarder Crédits Excel"):
        save_to_excel(st.session_state.credits, "Crédits")
        st.success("Crédits sauvegardés !")

elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total des Ventes", f"{st.session_state.sales_total} DH")
    if st.button("Réinitialiser"):
        st.session_state.sales_total = 0.0
        st.rerun()
    if st.button("💾 Sauvegarder Caisse Excel"):
        save_to_excel(pd.DataFrame({'Total': [st.session_state.sales_total]}), "Caisse")
        st.success("Données sauvegardées !")

st.write("---")
st.text("Ouzoud Pro - System Operational")

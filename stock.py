import streamlit as st
import pandas as pd
import shutil
import os
from fpdf import FPDF
from datetime import datetime

# الدالة ديال الحفظ في ملف Excel
def save_to_excel(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    with pd.ExcelWriter(file_name, mode='a' if os.path.exists(file_name) else 'w', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# دالة توليد PDF بترويسة Ouzoud Services
def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Ouzoud Services", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=text)
    return pdf.output(dest='S').encode('latin-1')

# 1. تهيئة النظام
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False 
if "inventory" not in st.session_state: 
    st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
if "invoices_db" not in st.session_state: 
    st.session_state.invoices_db = pd.DataFrame(columns=["Date", "Détails", "Total"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["Client", "Montant"])
if "last_receipt" not in st.session_state: st.session_state.last_receipt = ""

st.title("Système de Gestion Ouzoud Pro")

# 2. الحماية
if not st.session_state.authenticated:
    if st.text_input("Mot de passe:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.warning("Veuillez entrer le mot de passe pour accéder au système.")
        st.stop()

# 3. المنيو الرئيسي
menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Crédits", "Caisse"])

# 4. الأقسام
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Mode de vente:", ["Vente Normale", "Scan QR/Code-barres", "Vente Libre (Divers)"])
    
    date_heure = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if mode == "Vente Normale":
        if not st.session_state.inventory.empty:
            name = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
            qty = st.number_input("Quantité:", min_value=1)
            if st.button("Valider"):
                idx = st.session_state.inventory[st.session_state.inventory['Nom'] == name].index[0]
                price = st.session_state.inventory.at[idx, 'Prix']
                code = st.session_state.inventory.at[idx, 'Code-barres']
                code_text = f"\nCode: {code}" if pd.notnull(code) and code != "" else ""
                total = price * qty
                st.session_state.sales_total += total
                st.session_state.inventory.at[idx, 'Quantité'] -= qty
                st.session_state.last_receipt = f"--- Ouzoud Services ---\nDate: {date_heure}{code_text}\nProduit: {name}\nQuantité: {qty}\nTotal: {total} DH"
                st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[date_heure, st.session_state.last_receipt, total]], columns=["Date", "Détails", "Total"])])
                st.success("Vente effectuée !")
    
    elif mode == "Scan QR/Code-barres":
        scan = st.text_input("Scanner le code ici:")
        if scan:
            prod = st.session_state.inventory[st.session_state.inventory['Code-barres'] == scan]
            if not prod.empty:
                st.write(f"Produit: {prod.iloc[0]['Nom']} | Prix: {prod.iloc[0]['Prix']} DH")
                if st.button("Valider Scan"):
                    total = prod.iloc[0]['Prix']
                    st.session_state.sales_total += total
                    code_text = f"\nCode: {scan}" if scan else ""
                    st.session_state.last_receipt = f"--- Ouzoud Services ---\nDate: {date_heure}{code_text}\nProduit: {prod.iloc[0]['Nom']}\nTotal: {total} DH"
                    st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[date_heure, st.session_state.last_receipt, total]], columns=["Date", "Détails", "Total"])])
                    st.success("Vente scannée !")
    
    else:
        desc = st.text_input("Description du produit:")
        prix_l = st.number_input("Prix de vente:", min_value=0.0)
        if st.button("Valider Vente Libre"):
            st.session_state.sales_total += prix_l
            st.session_state.last_receipt = f"--- Ouzoud Services ---\nDate: {date_heure}\nProduit: {desc}\nTotal: {prix_l} DH"
            st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[date_heure, st.session_state.last_receipt, prix_l]], columns=["Date", "Détails", "Total"])])
            st.success("Vente Libre enregistrée !")
    
    if st.session_state.last_receipt:
        st.text_area("Facture:", value=st.session_state.last_receipt, height=150)
        st.download_button("🖨️ Imprimer Facture PDF", generate_pdf(st.session_state.last_receipt), file_name="facture.pdf", mime="application/pdf")
        if st.button("💾 Enregistrer Ventes dans Excel"):
            save_to_excel(st.session_state.invoices_db, "Factures")
            st.success("تم الحفظ في Excel!")

elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.expander("➕ Ajouter un produit"):
        with st.form("add"):
            n, p, q, b = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
            if st.form_submit_button("Ajouter"):
                new_item = pd.DataFrame([[n, p, q, b]], columns=["Nom", "Prix", "Quantité", "Code-barres"])
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
                st.rerun()
    
    st.subheader("🛠 Modifier / Supprimer")
    if not st.session_state.inventory.empty:
        sel = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
        idx = st.session_state.inventory[st.session_state.inventory['Nom'] == sel].index[0]
        new_p = st.number_input("Prix:", value=float(st.session_state.inventory.at[idx, 'Prix']))
        new_q = st.number_input("Qté:", value=int(st.session_state.inventory.at[idx, 'Quantité']))
        if st.button("Sauvegarder"):
            st.session_state.inventory.at[idx, 'Prix'], st.session_state.inventory.at[idx, 'Quantité'] = new_p, new_q
            st.rerun()
        if st.button("🗑 Supprimer", type="primary"):
            st.session_state.inventory = st.session_state.inventory.drop(idx)
            st.rerun()
    
    st.table(st.session_state.inventory)
    if st.button("💾 Enregistrer le Stock dans Excel"):
        save_to_excel(st.session_state.inventory, "Stock")
        st.success("تم حفظ الستوك في Excel!")

elif menu == "Impression":
    st.header("🖨️ Service Impression")
    pp = st.number_input("Prix par page:", value=0.50)
    pages = st.number_input("Nombre de pages:", min_value=1)
    if st.button("Enregistrer"):
        st.session_state.sales_total += (pages * pp)
        st.success("Opération enregistrée")
    if st.button("💾 Enregistrer Impression dans Excel"):
        save_to_excel(pd.DataFrame({'Total_Impression': [st.session_state.sales_total]}), "Impression")
        st.success("تم حفظ بيانات الطباعة!")

elif menu == "Crédits":
    st.header("💳 Gestion des Crédits")
    c_n, c_a = st.text_input("Client"), st.number_input("Montant")
    if st.button("Ajouter Crédit"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[c_n, c_a]], columns=["Client", "Montant"])])
    
    st.table(st.session_state.credits)
    if st.button("💾 Enregistrer les Crédits dans Excel"):
        save_to_excel(st.session_state.credits, "Crédits")
        st.success("تم حفظ الكريديات في Excel!")

elif menu == "Caisse":
    st.header("💰 Caisse & Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Produits:", len(st.session_state.inventory))
    c2.metric("Total Crédits:", f"{st.session_state.credits['Montant'].sum()} DH")
    c3.metric("Revenus:", f"{st.session_state.sales_total} DH")
    
    st.markdown("---")
    st.subheader("📋 Liste des Factures")
    st.table(st.session_state.invoices_db)
    
    if st.button("Réinitialiser la Caisse"):
        st.session_state.sales_total = 0.0
        st.session_state.last_receipt = ""
        st.rerun()
    if st.button("💾 Enregistrer Caisse dans Excel"):
        save_to_excel(pd.DataFrame({'Total_Revenus': [st.session_state.sales_total]}), "Caisse")
        st.success("تم حفظ بيانات الكايس!")

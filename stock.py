import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# دالة الحفظ
def save_to_excel(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    try:
        if os.path.exists(file_name):
            with pd.ExcelWriter(file_name, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            with pd.ExcelWriter(file_name, mode='w', engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        st.success(f"تم الحفظ في {sheet_name} بنجاح!")
    except Exception as e:
        st.error(f"خطأ أثناء الحفظ: {e}")

# دالة تحميل الستوك (جديدة)
def load_stock():
    if os.path.exists('ouzoud_data.xlsx'):
        try:
            return pd.read_excel('ouzoud_data.xlsx', sheet_name='Stock')
        except:
            return pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
    return pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])

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
# هنا كنشارجيو الستوك أوتوماتيكياً يلا كان ديجا مسجل فالإكسيل
if "inventory" not in st.session_state: st.session_state.inventory = load_stock()
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

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Factures", "Gestion Stock", "Impression", "Crédits", "Caisse"])

if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Mode:", ["Vente Normale", "Scan QR", "Vente Libre"])
    
    if mode == "Vente Normale":
        if not st.session_state.inventory.empty:
            prod = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
            qty = st.number_input("Quantité:", min_value=1)
            if st.button("Valider"):
                idx = st.session_state.inventory[st.session_state.inventory['Nom'] == prod].index[0]
                price = st.session_state.inventory.at[idx, 'Prix']
                total = price * qty
                st.session_state.sales_total += total
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                details = f"Ouzoud Services\nDate: {date}\nProduit: {prod}\nQté: {qty}\nTotal: {total} DH"
                st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[date, details, total]], columns=["Date", "Détails", "Total"])], ignore_index=True)
                st.success("Vente enregistrée !")

    elif mode == "Scan QR":
        scan = st.text_input("Scanner le code:")
        if scan:
            row = st.session_state.inventory[st.session_state.inventory['Code-barres'] == scan]
            if not row.empty:
                if st.button("Valider le Scan"):
                    total = row.iloc[0]['Prix']
                    st.session_state.sales_total += total
                    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    details = f"Ouzoud Services\nDate: {date}\nProduit: {row.iloc[0]['Nom']}\nTotal: {total} DH"
                    st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[date, details, total]], columns=["Date", "Détails", "Total"])], ignore_index=True)
                    st.success("Scanné !")
    
    else:
        desc = st.text_input("Description:")
        prix_l = st.number_input("Prix:")
        if st.button("Valider"):
            st.session_state.sales_total += prix_l
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            details = f"Ouzoud Services\nDate: {date}\nProduit: {desc}\nTotal: {prix_l} DH"
            st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[date, details, prix_l]], columns=["Date", "Détails", "Total"])], ignore_index=True)
            st.success("Vente Libre enregistrée !")

elif menu == "Factures":
    st.header("🧾 Historique des Factures")
    if not st.session_state.invoices_db.empty:
        selected_date = st.selectbox("Choisir une facture par heure:", st.session_state.invoices_db['Date'].tolist())
        facture = st.session_state.invoices_db[st.session_state.invoices_db['Date'] == selected_date].iloc[0]
        st.text_area("Détails de la facture:", value=facture['Détails'], height=200)
        st.download_button("🖨️ Imprimer en PDF", generate_pdf(facture['Détails']), f"Facture_{selected_date.replace(':', '-')}.pdf", "application/pdf")
        if st.button("💾 Sauvegarder toutes les factures Excel"):
            save_to_excel(st.session_state.invoices_db, "Factures")
    else:
        st.info("Aucune facture pour le moment.")

elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder Stock Excel"):
        save_to_excel(st.session_state.inventory, "Stock")

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
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[cn, ca]], columns=["Client", "Montant"])], ignore_index=True)
    st.table(st.session_state.credits)
    if st.button("💾 Sauvegarder Crédits Excel"):
        save_to_excel(st.session_state.credits, "Crédits")

elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total des Ventes", f"{st.session_state.sales_total} DH")
    if st.button("Réinitialiser"):
        st.session_state.sales_total = 0.0
        st.session_state.invoices_db = pd.DataFrame(columns=["Date", "Détails", "Total"])
        st.rerun()

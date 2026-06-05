import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime, timedelta

# --- دالة الحفظ الذكية ---
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

# --- دالة تحميل البيانات ---
def load_data(sheet_name):
    if os.path.exists('ouzoud_data.xlsx'):
        try:
            return pd.read_excel('ouzoud_data.xlsx', sheet_name=sheet_name)
        except:
            return pd.DataFrame(columns=['Nom', 'Prix', 'Quantité', 'Code-barres'])
    return pd.DataFrame(columns=['Nom', 'Prix', 'Quantité', 'Code-barres'])

# --- دالة PDF ---
def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Ouzoud Services - Facture", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=text)
    return pdf.output(dest='S').encode('latin-1')

# --- تهيئة الذاكرة ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = load_data("Stock")
if "invoices_db" not in st.session_state: st.session_state.invoices_db = load_data("Factures")
if "cart" not in st.session_state: st.session_state.cart = []
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0

st.title("Système de Gestion Ouzoud Pro")

# --- الحماية ---
if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Factures", "Gestion Stock", "Impression", "Caisse"])
date_str = (datetime.now() + timedelta(hours=1, minutes=3)).strftime("%Y-%m-%d %H:%M:%S")

if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("اختيار طريقة البيع:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier (السلة)"])

    if mode == "Vente Normale" and not st.session_state.inventory.empty:
        prod = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
        qty = st.number_input("Quantité:", min_value=1)
        if st.button("✅ Valider"):
            price = st.session_state.inventory[st.session_state.inventory['Nom'] == prod].iloc[0]['Prix']
            st.session_state.cart.append({"Nom": prod, "Prix": price, "Qté": qty, "Total": price * qty})
            st.success(f"تمت إضافة {prod} للسلة")

    elif mode == "Scan QR":
        scan = st.text_input("Scanner le code-barres:")
        if scan:
            row = st.session_state.inventory[st.session_state.inventory['Code-barres'] == str(scan)]
            if not row.empty:
                st.write(f"Produit: {row.iloc[0]['Nom']} | Prix: {row.iloc[0]['Prix']} DH")
                if st.button("✅ Valider"):
                    st.session_state.cart.append({"Nom": row.iloc[0]['Nom'], "Prix": row.iloc[0]['Prix'], "Qté": 1, "Total": row.iloc[0]['Prix']})
                    st.success("تمت إضافة المنتج للسلة")

    elif mode == "Vente Libre":
        desc = st.text_input("Description:")
        prix_l = st.number_input("Prix:", min_value=0.0)
        if st.button("✅ Valider"):
            st.session_state.cart.append({"Nom": desc, "Prix": prix_l, "Qté": 1, "Total": prix_l})
            st.success("تمت إضافة المنتج الحر للسلة")

    elif mode == "Panier (السلة)":
        st.subheader("سلة التسوق:")
        if st.session_state.cart:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.table(cart_df)
            st.write(f"**المجموع:** {cart_df['Total'].sum()} DH")
            if st.button("🖨️ Valider et Imprimer (Facture)"):
                total_facture = cart_df['Total'].sum()
                st.session_state.sales_total += total_facture
                details = f"Ouzoud Services\nDate: {date_str}\n\n" + cart_df.to_string(index=False) + f"\n\nTotal: {total_facture} DH"
                st.session_state.invoices_db = pd.concat([st.session_state.invoices_db, pd.DataFrame([[date_str, details, total_facture]], columns=["Date", "Détails", "Total"])], ignore_index=True)
                st.session_state.cart = []
                st.success("تم إصدار الفاتورة !")
                st.rerun()

elif menu == "Factures":
    st.header("🧾 Historique des Factures")
    if not st.session_state.invoices_db.empty:
        selected_date = st.selectbox("Choisir une facture:", st.session_state.invoices_db['Date'].tolist())
        facture = st.session_state.invoices_db[st.session_state.invoices_db['Date'] == selected_date].iloc[0]
        st.text_area("Détails:", value=facture['Détails'], height=250)
        st.download_button("🖨️ Imprimer en PDF", generate_pdf(facture['Détails']), "facture.pdf")
        if st.button("💾 Sauvegarder"): save_to_excel(st.session_state.invoices_db, "Factures")

elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder"): save_to_excel(st.session_state.inventory, "Stock")

elif menu == "Impression":
    st.header("🖨️ Impression")
    pp = st.number_input("Prix par page")
    pages = st.number_input("Nombre de pages")
    if st.button("✅ Valider"):
        st.session_state.sales_total += (pages * pp)
        st.success("Enregistré")

elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total des Ventes", f"{st.session_state.sales_total} DH")
    if st.button("Réinitialiser"):
        st.session_state.sales_total = 0.0
        st.session_state.invoices_db = pd.DataFrame(columns=["Date", "Détails", "Total"])
        st.rerun()

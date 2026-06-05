import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime, timedelta

# --- الإعدادات العامة ---
st.set_page_config(layout="wide")

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

# --- تهيئة الذاكرة ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = load_data("Stock")
if "invoices_db" not in st.session_state: st.session_state.invoices_db = load_data("Factures")
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

# --- واجهة Point de Vente ---
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("إدخال المنتجات")
        mode = st.radio("اختيار طريقة الإدخال:", ["Vente Normale", "Scan QR", "Vente Libre"])
        
        if mode == "Vente Normale":
            prod = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
            qty = st.number_input("Quantité:", min_value=1)
            if st.button("✅ Valider"):
                price = st.session_state.inventory[st.session_state.inventory['Nom'] == prod].iloc[0]['Prix']
                st.session_state.cart.append({"Nom": prod, "Prix": price, "Qté": qty, "Total": price * qty})
        
        elif mode == "Scan QR":
            scan = st.text_input("Scanner le code-barres:")
            if scan:
                row = st.session_state.inventory[st.session_state.inventory['Code-barres'] == str(scan)]
                if not row.empty:
                    st.write(f"Produit: {row.iloc[0]['Nom']} | Prix: {row.iloc[0]['Prix']} DH")
                    if st.button("✅ Valider"):
                        st.session_state.cart.append({"Nom": row.iloc[0]['Nom'], "Prix": row.iloc[0]['Prix'], "Qté": 1, "Total": row.iloc[0]['Prix']})
        
        elif mode == "Vente Libre":
            desc = st.text_input("Description:")
            prix_l = st.number_input("Prix:", min_value=0.0)
            if st.button("✅ Valider"):
                st.session_state.cart.append({"Nom": desc, "Prix": prix_l, "Qté": 1, "Total": prix_l})

    with col2:
        st.subheader("🛒 السلة (الشكل القديم)")
        # هاد الجزء هو العرض اللي كنتي مولف عليه
        if st.session_state.cart:
            for i, item in enumerate(st.session_state.cart):
                st.write(f"{i+1}. {item['Nom']} - {item['Prix']} DH x {item['Qté']} = {item['Total']} DH")
            
            cart_df = pd.DataFrame(st.session_state.cart)
            st.write(f"**المجموع الكلي:** {cart_df['Total'].sum()} DH")
            
            if st.button("🖨️ Valider et Imprimer (Facture)"):
                st.session_state.sales_total += cart_df['Total'].sum()
                st.session_state.cart = []
                st.success("تم إصدار الفاتورة !")
                st.rerun()

# --- موديول الطباعة ---
elif menu == "Impression":
    st.header("🖨️ Impression")
    pp = st.number_input("Prix par page (DH):", min_value=0.0)
    pages = st.number_input("Nombre de pages:", min_value=1)
    if st.button("✅ Enregistrer Impression"):
        st.session_state.sales_total += (pp * pages)
        st.success(f"تم تسجيل {pp * pages} DH في الخزينة")

# --- إدارة الكريديات ---
elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client = st.text_input("Nom du Client")
    montant = st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[client, montant]], columns=["Client", "Montant"])], ignore_index=True)
        st.success("Crédit enregistré")
    st.table(st.session_state.credits)
    if st.button("💾 Sauvegarder"): save_to_excel(st.session_state.credits, "Credits")

# --- باقي الكود ---
elif menu == "Factures":
    st.header("📄 Factures")
    st.write("Section dédiée à l'historique des factures.")

elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder"): save_to_excel(st.session_state.inventory, "Stock")

elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total (Ventes + Impressions)", f"{st.session_state.sales_total} DH")

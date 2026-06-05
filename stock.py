import streamlit as st
import pandas as pd
import os
from datetime import datetime
from openpyxl import load_workbook

# --- إعدادات الصفحة ---
st.set_page_config(layout="wide")

# --- دالة الحفظ العامة لكل المنيوهات ---
def save_data(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    try:
        if os.path.exists(file_name):
            with pd.ExcelWriter(file_name, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            with pd.ExcelWriter(file_name, mode='w', engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        st.success(f"تم حفظ بيانات {sheet_name} في ملف Excel بنجاح!")
    except Exception as e:
        st.error(f"خطأ أثناء الحفظ: {e}")

def load_data(sheet_name):
    if os.path.exists('ouzoud_data.xlsx'):
        try: return pd.read_excel('ouzoud_data.xlsx', sheet_name=sheet_name)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- تهيئة البيانات ---
if "cart" not in st.session_state: st.session_state.cart = []
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "inventory" not in st.session_state: st.session_state.inventory = load_data("Stock")
if "credits" not in st.session_state: st.session_state.credits = load_data("Credits")

# --- المنيو الرئيسي ---
menu = st.sidebar.selectbox("Menu Principal", ["1. Vente", "2. Stock", "3. Factures", "4. Credits", "5. Caisse", "6. Impression"])

# --- 1. Vente (4 طرق إدخال) ---
if menu == "1. Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Choisissez le mode:", ["Vente Normale", "Vente QR", "Vente Libre", "Panier"])
    
    if mode == "Vente Normale":
        prod = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
        qty = st.number_input("Quantité:", min_value=1)
        if st.button("Ajouter à la liste"):
            price = st.session_state.inventory[st.session_state.inventory['Nom'] == prod].iloc[0]['Prix']
            st.session_state.cart.append({"Nom": prod, "Prix": price, "Qté": qty, "Total": price * qty})
            st.rerun()

    elif mode == "Vente QR":
        code = st.text_input("Scanner le code-barres:")
        if code:
            row = st.session_state.inventory[st.session_state.inventory['Code-barres'] == str(code)]
            if not row.empty:
                if st.button("Ajouter"):
                    st.session_state.cart.append({"Nom": row.iloc[0]['Nom'], "Prix": row.iloc[0]['Prix'], "Qté": 1, "Total": row.iloc[0]['Prix']})
                    st.rerun()

    elif mode == "Vente Libre":
        name = st.text_input("Nom du produit:")
        price = st.number_input("Prix:")
        if st.button("Ajouter"):
            st.session_state.cart.append({"Nom": name, "Prix": price, "Qté": 1, "Total": price})
            st.rerun()

    st.write("---")
    st.subheader("🛒 Panier")
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.table(cart_df)
        st.write(f"### Total: {cart_df['Total'].sum()} DH")
        if st.button("Valider et Enregistrer dans Excel"):
            st.session_state.sales_total += cart_df['Total'].sum()
            save_data(cart_df, "Ventes_History")
            st.session_state.cart = []
            st.rerun()

# --- 2. Stock ---
elif menu == "2. Stock":
    st.header("📦 Gestion du Stock")
    with st.form("stock_form"):
        name = st.text_input("Nom")
        price = st.number_input("Prix")
        qty = st.number_input("Qté")
        bar = st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            new_row = pd.DataFrame([[name, price, qty, bar]], columns=['Nom', 'Prix', 'Quantité', 'Code-barres'])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Enregistrer le Stock dans Excel"): save_data(st.session_state.inventory, "Stock")

# --- 3. Factures (توقيت المغرب) ---
elif menu == "3. Factures":
    st.header("📄 Factures")
    time_ma = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.write(f"Date et Heure locale (Maroc): **{time_ma}**")
    if st.button("💾 Exporter Factures vers Excel"): save_data(pd.DataFrame(), "Factures")

# --- 4. Credits ---
elif menu == "4. Credits":
    st.header("💳 Gestion des Crédits")
    client = st.text_input("Nom du client")
    montant = st.number_input("Montant")
    if st.button("Ajouter Crédit"):
        new_c = pd.DataFrame([[client, montant]], columns=['Client', 'Montant'])
        st.session_state.credits = pd.concat([st.session_state.credits, new_c], ignore_index=True)
        st.rerun()
    st.table(st.session_state.credits)
    if st.button("💾 Enregistrer Crédits dans Excel"): save_data(st.session_state.credits, "Credits")

# --- 5. Caisse ---
elif menu == "5. Caisse":
    st.header("💰 Caisse")
    st.metric("Total des revenus", f"{st.session_state.sales_total} DH")
    if st.button("💾 Enregistrer Caisse dans Excel"): save_data(pd.DataFrame([{"Total": st.session_state.sales_total}]), "Caisse")

# --- 6. Impression ---
elif menu == "6. Impression":
    st.header("🖨️ Service d'Impression")
    p = st.number_input("Prix par page (DH):")
    n = st.number_input("Nombre de pages:", min_value=1)
    if st.button("Enregistrer l'impression"):
        st.session_state.sales_total += (p * n)
        st.success(f"Enregistré : {p * n} DH")
    if st.button("💾 Enregistrer Impression dans Excel"): save_data(pd.DataFrame([{"Prix": p, "Nombre": n}]), "Impression")

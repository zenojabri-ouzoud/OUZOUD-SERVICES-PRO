import streamlit as st
import pandas as pd
import os
from datetime import datetime
from openpyxl import load_workbook

# --- إعدادات الصفحة ---
st.set_page_config(layout="wide")

# --- دوال الحفظ والتحميل لكل المنيوهات ---
def save_data(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(file_name, mode='w', engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    st.success(f"تم حفظ البيانات في ورقة {sheet_name}")

def load_data(sheet_name):
    if os.path.exists('ouzoud_data.xlsx'):
        try: return pd.read_excel('ouzoud_data.xlsx', sheet_name=sheet_name)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- تهيئة الذاكرة (Session State) ---
if "cart" not in st.session_state: st.session_state.cart = []
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "inventory" not in st.session_state: st.session_state.inventory = load_data("Stock")
if "credits" not in st.session_state: st.session_state.credits = load_data("Credits")

# --- المنيو الرئيسي (6 خيارات) ---
menu = st.sidebar.selectbox("Menu Principal", ["1. Vente", "2. Stock", "3. Factures", "4. Credits", "5. Caisse", "6. Impression"])

# --- 1. Vente (مع 4 طرق إدخال) ---
if menu == "1. Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Choisissez le mode de vente:", ["Vente Normale", "Vente QR", "Vente Libre", "Panier"])
    
    if mode == "Vente Normale":
        prod = st.selectbox("Sélectionnez le produit:", st.session_state.inventory['Nom'].tolist())
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
                st.write(f"Produit trouvé: {row.iloc[0]['Nom']} | Prix: {row.iloc[0]['Prix']}")
                if st.button("Ajouter"):
                    st.session_state.cart.append({"Nom": row.iloc[0]['Nom'], "Prix": row.iloc[0]['Prix'], "Qté": 1, "Total": row.iloc[0]['Prix']})
                    st.rerun()

    elif mode == "Vente Libre":
        name = st.text_input("Nom du produit:")
        price = st.number_input("Prix du produit:")
        if st.button("Ajouter vente libre"):
            st.session_state.cart.append({"Nom": name, "Prix": price, "Qté": 1, "Total": price})
            st.rerun()

    # قسم السلة (Panier) المدمج
    st.write("---")
    st.subheader("🛒 Panier")
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.table(cart_df)
        st.write(f"### Total à payer: {cart_df['Total'].sum()} DH")
        if st.button("Valider et vider le panier"):
            st.session_state.sales_total += cart_df['Total'].sum()
            st.session_state.cart = []
            st.success("Vente validée avec succès !")
            st.rerun()
    else:
        st.info("Le panier est vide.")

# --- 2. Stock ---
elif menu == "2. Stock":
    st.header("📦 Gestion du Stock")
    with st.form("stock_form"):
        name = st.text_input("Nom du produit")
        price = st.number_input("Prix")
        qty = st.number_input("Quantité")
        bar = st.text_input("Code-barres")
        if st.form_submit_button("Sauvegarder dans Stock"):
            new_row = pd.DataFrame([[name, price, qty, bar]], columns=['Nom', 'Prix', 'Quantité', 'Code-barres'])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            save_data(st.session_state.inventory, "Stock")
            st.rerun()
    st.table(st.session_state.inventory)

# --- 3. Factures (مع توقيت المغرب) ---
elif menu == "3. Factures":
    st.header("📄 Factures")
    # توقيت المغرب الدقيق
    time_ma = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.write(f"Date et Heure locale (Maroc): **{time_ma}**")
    
    if st.button("Imprimer Facture (PDF/Excel)"):
        # هنا يمكنك إضافة كود PDF
        save_data(pd.DataFrame(), "Factures")
        st.success("Facture générée avec succès")

# --- 4. Credits ---
elif menu == "4. Credits":
    st.header("💳 Gestion des Crédits")
    client = st.text_input("Nom du client")
    montant = st.number_input("Montant du crédit")
    if st.button("Enregistrer Crédit"):
        new_c = pd.DataFrame([[client, montant]], columns=['Client', 'Montant'])
        st.session_state.credits = pd.concat([st.session_state.credits, new_c], ignore_index=True)
        save_data(st.session_state.credits, "Credits")
    st.table(st.session_state.credits)

# --- 5. Caisse ---
elif menu == "5. Caisse":
    st.header("💰 Caisse")
    st.metric("Total des revenus", f"{st.session_state.sales_total} DH")

# --- 6. Impression ---
elif menu == "6. Impression":
    st.header("🖨️ Service d'Impression")
    pp = st.number_input("Prix par page (DH):")
    n = st.number_input("Nombre de pages:", min_value=1)
    if st.button("Enregistrer l'impression"):
        total_imp = pp * n
        st.session_state.sales_total += total_imp
        st.success(f"Impression enregistrée : {total_imp} DH ajoutés à la caisse.")

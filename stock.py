import streamlit as st
import pandas as pd
import shutil
import os

# --- 1. دالة الحماية والنسخ (Backup) ---
def backup_data():
    if os.path.exists('stock.xlsx'):
        shutil.copy('stock.xlsx', 'stock_backup.xlsx')

def save_to_excel(data, sheet_name):
    """دالة عامة للحفظ في Excel"""
    file_name = 'ouzoud_data.xlsx'
    backup_data()
    try:
        if os.path.exists(file_name):
            with pd.ExcelWriter(file_name, mode='a', if_sheet_exists='overlay') as writer:
                data.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            data.to_excel(file_name, sheet_name=sheet_name, index=False)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde: {e}")

# --- 2. تهيئة النظام ---
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False 
if "inventory" not in st.session_state: 
    st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["Client", "Montant"])
if "last_receipt" not in st.session_state: st.session_state.last_receipt = ""

st.title("Système de Gestion Ouzoud Pro")

# --- 3. الحماية ---
if not st.session_state.authenticated:
    if st.text_input("Mot de passe:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
else:
    menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Crédits", "Caisse"])

    # --- 4. العمليات ---
    if menu == "Point de Vente":
        st.header("🛒 Point de Vente")
        mode = st.radio("Mode de vente:", ["Vente Normale", "Scan QR/Code-barres", "Vente Libre"])
        
        # مثال للبيع العادي (تم دمج الحفظ هنا)
        if mode == "Vente Normale" and not st.session_state.inventory.empty:
            name = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
            qty = st.number_input("Quantité:", min_value=1)
            if st.button("Valider et Enregistrer dans Excel"):
                idx = st.session_state.inventory[st.session_state.inventory['Nom'] == name].index[0]
                price = st.session_state.inventory.at[idx, 'Prix']
                total = price * qty
                st.session_state.sales_total += total
                st.session_state.inventory.at[idx, 'Quantité'] -= qty
                
                # حفظ عملية البيع
                sale_df = pd.DataFrame([[name, qty, total]], columns=["Produit", "Quantité", "Total"])
                save_to_excel(sale_df, "Ventes")
                st.success("Vente effectuée et enregistrée !")

    elif menu == "Gestion Stock":
        st.header("📦 Gestion Stock")
        # نفس منطق الإضافة... (يمكنك استدعاء save_to_excel هنا)
        st.table(st.session_state.inventory)
        if st.button("Exporter le Stock vers Excel"):
            save_to_excel(st.session_state.inventory, "Stock")
            st.success("Stock exporté !")

    elif menu == "Crédits":
        st.header("💳 Gestion des Crédits")
        c_n, c_a = st.text_input("Client"), st.number_input("Montant")
        if st.button("Ajouter Crédit"):
            new_credit = pd.DataFrame([[c_n, c_a]], columns=["Client", "Montant"])
            st.session_state.credits = pd.concat([st.session_state.credits, new_credit])
            save_to_excel(new_credit, "Crédits")
            st.success("Crédit enregistré !")
        st.table(st.session_state.credits)

    elif menu == "Caisse":
        st.header("💰 Caisse & Dashboard")
        # (باقي الكود ديال الكاسة...)

import streamlit as st
import pandas as pd

# Configuration et Sécurité
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["Client", "Montant"])

st.title("Système de Gestion Ouzoud")

# Authentification
if not st.session_state.authenticated:
    if st.text_input("Mot de passe:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
else:
    menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Crédits", "Caisse"])
    
    # Point de Vente
    if menu == "Point de Vente":
        st.header("🛒 Point de Vente")
        if not st.session_state.inventory.empty:
            name = st.selectbox("Choisir le produit:", st.session_state.inventory['Nom'].tolist())
            qty = st.number_input("Quantité:", min_value=1)
            if st.button("Confirmer la vente"):
                price = st.session_state.inventory.loc[st.session_state.inventory['Nom'] == name, 'Prix'].iloc[0]
                total = price * qty
                st.session_state.sales_total += total
                idx = st.session_state.inventory[st.session_state.inventory['Nom'] == name].index[0]
                st.session_state.inventory.at[idx, 'Quantité'] -= qty
                st.success(f"✅ Vente effectuée! Total: {total} DH")
        else:
            st.warning("⚠️ Stock vide, ajoutez des produits.")

    # Gestion Stock
    elif menu == "Gestion Stock":
        st.header("📦 Gestion Stock")
        with st.form("add_item"):
            n, p, q, b = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Quantité"), st.text_input("Code-barres")
            if st.form_submit_button("Ajouter au stock"):
                new_item = pd.DataFrame([[n, p, q, b]], columns=["Nom", "Prix", "Quantité", "Code-barres"])
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
                st.rerun()
        st.table(st.session_state.inventory)

    # Impression
    elif menu == "Impression":
        st.header("🖨️ Service Impression")
        pp = st.number_input("Prix par page (DH):", value=0.50)
        pages = st.number_input("Nombre de pages:", min_value=1)
        total = pages * pp
        st.subheader(f"💰 Total final: {total} DH")
        if st.button("Enregistrer la vente"):
            st.session_state.sales_total += total
            st.success("✅ Opération enregistrée.")

    # Crédits
    elif menu == "Crédits":
        st.header("💳 Gestion des Crédits")
        c_name, c_amt = st.text_input("Nom du client"), st.number_input("Montant")
        if st.button("Enregistrer le crédit"):
            st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[c_name, c_amt]], columns=["Client", "Montant"])])
        st.table(st.session_state.credits)

    # Caisse
    elif menu == "Caisse":
        st.header("💰 Caisse")
        st.metric("Total des revenus:", f"{st.session_state.sales_total} DH")
        if st.button("Réinitialiser la caisse"):
            st.session_state.sales_total = 0.0
            st.rerun()

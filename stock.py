import streamlit as st
import pandas as pd
import shutil
import os


# 1. تهيئة النظام
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False 
if "inventory" not in st.session_state: 
    st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
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
    menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Crédits", "Caisse"])
    # --- Fonction centrale de sauvegarde (à mettre une seule fois en haut de ton script) ---

    # 3. نقطة البيع (3 طرق للبيع)  
if menu == "Point de Vente"
        st.header("🛒 Point de Vente")
        mode = st.radio("Mode de vente:", ["Vente Normale", "Scan QR/Code-barres", "Vente Libre (Divers)"])
        
        # النوع 1: البيع العادي
        if mode == "Vente Normale":
            if not st.session_state.inventory.empty:
                name = st.selectbox("Produit:", st.session_state.inventory['Nom'].tolist())
                qty = st.number_input("Quantité:", min_value=1)
                if st.button("Valider"):
                    idx = st.session_state.inventory[st.session_state.inventory['Nom'] == name].index[0]
                    price = st.session_state.inventory.at[idx, 'Prix']
                    total = price * qty
                    st.session_state.sales_total += total
                    st.session_state.inventory.at[idx, 'Quantité'] -= qty
                    st.session_state.last_receipt = f"--- FACTURE OUZOUD ---\nProduit: {name}\nQuantité: {qty}\nTotal: {total} DH"
                    st.success("Vente effectuée !")
        
        # النوع 2: السكانر
        elif mode == "Scan QR/Code-barres":
            scan = st.text_input("Scanner le code ici:")
            if scan:
                prod = st.session_state.inventory[st.session_state.inventory['Code-barres'] == scan]
                if not prod.empty:
                    st.write(f"Produit: {prod.iloc[0]['Nom']} | Prix: {prod.iloc[0]['Prix']} DH")
                    if st.button("Valider Scan"):
                        st.session_state.sales_total += prod.iloc[0]['Prix']
                        st.session_state.last_receipt = f"--- FACTURE OUZOUD ---\nProduit: {prod.iloc[0]['Nom']}\nTotal: {prod.iloc[0]['Prix']} DH"
                        st.success("Vente scannée !")
        
        # النوع 3: التجارة العادية (Vente Libre)
        else:
            desc = st.text_input("Description du produit:")
            prix_l = st.number_input("Prix de vente:", min_value=0.0)
            if st.button("Valider Vente Libre"):
                st.session_state.sales_total += prix_l
                st.session_state.last_receipt = f"--- FACTURE OUZOUD ---\nProduit: {desc}\nTotal: {prix_l} DH"
                st.success("Vente Libre enregistrée !")

        if st.session_state.last_receipt:
            st.download_button("📥 Télécharger la Facture", st.session_state.last_receipt, file_name="facture.txt")

    # 4. إدارة المخزون
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

    # 5. الطباعة والكريديات واللاكيس
    elif menu == "Impression":
        st.header("🖨️ Service Impression")
        pp = st.number_input("Prix par page:", value=0.50)
        pages = st.number_input("Nombre de pages:", min_value=1)
        if st.button("Enregistrer"):
            st.session_state.sales_total += (pages * pp)
            st.success("Opération enregistrée")

    elif menu == "Crédits":
        st.header("💳 Gestion des Crédits")
        c_n, c_a = st.text_input("Client"), st.number_input("Montant")
        if st.button("Ajouter Crédit"):
            st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[c_n, c_a]], columns=["Client", "Montant"])])
        st.table(st.session_state.credits)

    elif menu == "Caisse":
        st.header("💰 Caisse & Dashboard")
        st.subheader("🎯 Tableau de bord")
        c1, c2, c3 = st.columns(3)
        c1.metric("Produits:", len(st.session_state.inventory))
        c2.metric("Total Crédits:", f"{st.session_state.credits['Montant'].sum()} DH")
        c3.metric("Revenus:", f"{st.session_state.sales_total} DH")
        
        st.markdown("---")
        st.subheader("🧾 Dernière Facture")
        st.text_area("Détails:", value=st.session_state.last_receipt, height=150)
        
        if st.button("Réinitialiser la Caisse"):
            st.session_state.sales_total = 0.0
            st.session_state.last_receipt = ""
            st.rerun()

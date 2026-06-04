import streamlit as st
import pandas as pd

# Initialisation des données
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = pd.DataFrame(columns=["Nom", "Prix", "Quantité", "Code-barres"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["Client", "Montant"])

st.title("Système de Gestion Ouzoud")

# Authentification
if not st.session_state.authenticated:
    if st.text_input("Mot de passe:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
else:
    menu = st.sidebar.selectbox("Menu", ["Point de Vente", "Stock", "Impression", "Crédits", "Caisse"])

    # 1. POINT DE VENTE (Double mode : Normal & Scan)
    if menu == "Point de Vente":
        st.header("🛒 Point de Vente")
        mode = st.radio("Mode:", ["Vente Normale", "Scan QR/Code-barres"])
        
        if mode == "Vente Normale":
            name = st.selectbox("Choisir:", st.session_state.inventory['Nom'].tolist())
            qty = st.number_input("Quantité:", min_value=1)
            if st.button("Confirmer"):
                idx = st.session_state.inventory[st.session_state.inventory['Nom'] == name].index[0]
                price = st.session_state.inventory.at[idx, 'Prix']
                st.session_state.sales_total += price * qty
                st.session_state.inventory.at[idx, 'Quantité'] -= qty
                st.success(f"Vendu: {name}")
        else:
            scan = st.text_input("Scanner ici:")
            if scan:
                prod = st.session_state.inventory[st.session_state.inventory['Code-barres'] == scan]
                if not prod.empty:
                    st.write(f"Produit: {prod.iloc[0]['Nom']} | Prix: {prod.iloc[0]['Prix']} DH")
                    if st.button("Valider Scan"):
                        st.session_state.sales_total += prod.iloc[0]['Prix']
                        st.success("Vente réussie!")

    # 2. STOCK
    elif menu == "Stock":
        st.header("📦 Gestion Stock")
        with st.form("stock_form"):
            n, p, q, b = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
            if st.form_submit_button("Ajouter"):
                st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[n, p, q, b]], columns=["Nom", "Prix", "Quantité", "Code-barres"])])
                st.rerun()
        st.table(st.session_state.inventory)

    # 3. IMPRESSION
    elif menu == "Impression":
        st.header("🖨️ Service Impression")
        pp = st.number_input("Prix par page:", value=0.50)
        pages = st.number_input("Nb pages:", min_value=1)
        if st.button("Enregistrer"):
            st.session_state.sales_total += (pages * pp)
            st.success("Opération enregistrée")

    # 4. CRÉDITS
    elif menu == "Crédits":
        st.header("💳 Gestion des Crédits")
        c_n, c_a = st.text_input("Client"), st.number_input("Montant")
        if st.button("Ajouter Crédit"):
            st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[c_n, c_a]], columns=["Client", "Montant"])])
        st.table(st.session_state.credits)

    # 5. CAISSE
    elif menu == "Caisse":
               # 8. لوحة الهدف (Dashboard) - ضيفها فآخر ملفك
    st.markdown("---")
    st.subheader("🎯 لوحة تحكم الأهداف (Dashboard)")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("السلع المتبقية:", len(st.session_state.inventory))
    col_b.metric("مجموع الديون:", f"{st.session_state.credits['المبلغ'].sum()} DH")
    col_c.metric("الأرباح الإجمالية:", f"{st.session_state.sales_total} DH")
    
    st.info("💡 نصيحة: حاول تحافظ على "السلع المتبقية" فوق 10 منتجات لتفادي نفاذ المخزون!")
    # سجل الفواتير
        st.subheader("🧾 سجل الفواتير الأخيرة")
        if st.session_state.last_receipt:
            st.text_area("تفاصيل آخر فاتورة:", value=st.session_state.last_receipt, height=150)
        else:
            st.info("لا توجد فواتير مسجلة حالياً.")
            
        if st.button("تصفير لاكيس"):
            st.session_state.sales_total = 0.0
            st.session_state.last_receipt = ""
            st.rerun()
        if st.button("Réinitialiser"):
            st.session_state.sales_total = 0.0
            st.rerun()

        st.header("💰 Caisse & Analyse")
        st.metric("Revenus Totaux:", f"{st.session_state.sales_total} DH")
 

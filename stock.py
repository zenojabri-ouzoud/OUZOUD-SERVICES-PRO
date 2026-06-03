import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# ==========================================
# 1. الإعدادات المتقدمة للهندسة البرمجية للموقع
# ==========================================
st.set_page_config(
    page_title="نظام Enterprise لإدارة المكتبات",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# أسماء ملفات البيانات (CSV Engine)
STOCK_FILE = "library_stock_v2.csv"
SALES_FILE = "library_sales_v2.csv"
CONFIG_FILE = "library_config.csv"

# ==========================================
# 2. نظام إدارة وقراءة الملفات الحرج (Data Core)
# ==========================================
def initialize_system():
    stock_cols = ["الرقم الترتيبي", "نوع المنتج", "الاسم / الوصف", "الكمية المتوفرة", "ثمن الشراء (DH)", "ثمن البيع (DH)", "الحد الأدنى للتنبيه"]
    sales_cols = ["معرف العملية", "التاريخ والوقت", "نوع الخدمة/المنتج", "التفاصيل", "الكمية", "ثمن البيع الكلي (DH)", "الربح الصافي (DH)"]
    
    if not os.path.exists(STOCK_FILE):
        pd.DataFrame(columns=stock_cols).to_csv(STOCK_FILE, index=False)
    if not os.path.exists(SALES_FILE):
        pd.DataFrame(columns=sales_cols).to_csv(SALES_FILE, index=False)
        
    # تهيئة ملف الإعدادات الافتراضي (Les Paramètres)
    if not os.path.exists(CONFIG_FILE):
        config_df = pd.DataFrame([{
            "اسم_المكتبة": "مكتبة السلام الذكية",
            "الأصناف": "روايات وكتب,أدوات مدرسية,أدوات مكتبية,أخرى",
            "نسبة_ربح_الطباعة": 70.0
        }])
        config_df.to_csv(CONFIG_FILE, index=False)

initialize_system()

@st.cache_data(ttl=1)
def load_secure_data(file_path):
    return pd.read_csv(file_path)

def save_secure_data(df, file_path):
    df.to_csv(file_path, index=False)
    st.cache_data.clear()

# تحميل البيانات الحية والإعدادات
stock_df = load_secure_data(STOCK_FILE)
sales_df = load_secure_data(SALES_FILE)
config_df = load_secure_data(CONFIG_FILE)

# جلب قيم الإعدادات الحالية
app_name = config_df.at[0, "اسم_المكتبة"]
categories_list = config_df.at[0, "الأصناف"].split(",")
print_profit_margin = float(config_df.at[0, "نسبة_ربح_الطباعة"]) / 100.0

# ==========================================
# 3. الواجهة الجانبية ونظام الصلاحيات (Sidebar Layout)
# ==========================================
st.sidebar.markdown(f"<h2 style='text-align: center; color: #1E3A8A;'>{app_name}</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size: 12px; color: gray;'>ERP Enterprise v3.0</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu_option = st.sidebar.selectbox(
    "🌐 وحدة التحكم المركزية:",
    [
        "📊 اللوحة الديناميكية والإحصائيات",
        "🛒 نقطة البيع السريعة (POS)",
        "🖨️ مركز الطباعة والنسخ الرقمي",
        "📦 الهندسة الخلفية للمخزون (التحكم الكامل)",
        "🧾 التدقيق المالي وسجل العمليات",
        "⚙️ الإعدادات (Les Paramètres)"
    ]
)

# إشعار المخزون المنخفض
if not stock_df.empty:
    low_stock_items = stock_df[stock_df["الكمية المتوفرة"] <= stock_df["الحد الأدنى للتنبيه"]]
    if not low_stock_items.empty:
        st.sidebar.warning(f"⚠️ تنبيه حرج: لديك {len(low_stock_items)} منتجات تقترب من النفاد!")

st.title(f"📚 {app_name}")
st.markdown("---")

# ==========================================
# 4. التطبيق البرمجي لكل قسم (Business Logic)
# ==========================================

# --- القسم الأول: اللوحة الديناميكية والإحصائيات ---
if menu_option == "📊 اللوحة الديناميكية والإحصائيات":
    st.subheader("📊 لوحة الأداء العام والتحليلات المتقدمة للمكتبة")
    
    total_sales_value = sales_df["ثمن البيع الكلي (DH)"].sum() if not sales_df.empty else 0.0
    total_net_profit = sales_df["الربح الصافي (DH)"].sum() if not sales_df.empty else 0.0
    total_items_in_stock = stock_df["الكمية المتوفرة"].sum() if not stock_df.empty else 0
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="💰 إجمالي المبيعات (الرواج)", value=f"{total_sales_value:,.2f} DH", delta="نشط")
    kpi2.metric(label="📈 صافي الأرباح الحقيقية", value=f"{total_net_profit:,.2f} DH", delta=f"{((total_net_profit/total_sales_value)*100 if total_sales_value > 0 else 0):.1f}% هامش ربح")
    kpi3.metric(label="📦 قطع السلع المتوفرة حالياً", value=f"{total_items_in_stock:,} قطعة")
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📈 مبيعات الأصناف")
        if not sales_df.empty:
            fig_pie = px.pie(sales_df, values="ثمن البيع الكلي (DH)", names="نوع الخدمة/المنتج", hole=0.4, title="توزيع المداخيل حسب الصنف")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("لا توجد بيانات كافية لرسم المخطط المالي.")
    with col_chart2:
        st.subheader("⚠️ وضعية المخزون الحرجة")
        if not stock_df.empty:
            fig_bar = px.bar(stock_df, x="الاسم / الوصف", y="الكمية المتوفرة", color="الكمية المتوفرة", title="مستويات السلع في الرفوف")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("المخزن فارغ.")

# --- القسم الثاني: نقطة البيع السريعة (POS) ---
elif menu_option == "🛒 نقطة البيع السريعة (POS)":
    st.subheader("🛒 نظام مبيعات الكتب والأدوات المدرسية المباشر")
    if stock_df.empty:
        st.error("❌ المخزون فارغ تماماً!")
    else:
        category_filter = st.selectbox("🎯 تصفية حسب الصنف لتسهيل البحث:", ["الكل"] + list(set(stock_df["نوع المنتج"].tolist())))
        available_products = stock_df if category_filter == "الكل" else stock_df[stock_df["نوع المنتج"] == category_filter]
        product_list = available_products["الاسم / الوصف"].tolist()
        
        if not product_list:
            st.warning("لا توجد منتجات متوفرة.")
        else:
            selected_product = st.selectbox("📖 اختر المنتج أو الرواية المراد بيعها:", product_list)
            prod_row = stock_df[stock_df["الاسم / الوصف"] == selected_product].iloc[0]
            current_stock = int(prod_row["الكمية المتوفرة"])
            selling_price = float(prod_row["ثمن البيع (DH)"])
            buying_price = float(prod_row["ثمن الشراء (DH)"])
            
            st.markdown(f"""
            <div style='background-color:#F0FDF4; padding:15px; border-radius:10px; border-left:5px solid #16A34A;'>
                <h4>📊 تفاصيل السلعة:</h4>
                <p>💸 ثمن البيع: <b>{selling_price} DH</b> | 📦 متوفر: <b>{current_stock} قطعة</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            sales_qty = st.number_input("📥 حدد الكمية المطلوبة للزبون:", min_value=1, max_value=current_stock if current_stock > 0 else 1, value=1)
            if current_stock == 0:
                st.error("⛔ عذراً! هذا المنتج خارج المخزن.")
            else:
                total_checkout = sales_qty * selling_price
                net_profit_calc = (selling_price - buying_price) * sales_qty
                st.markdown(f"### 🧾 المجموع الإجمالي للحساب: <span style='color:#16A34A;'>{total_checkout:.2f} DH</span>", unsafe_allow_html=True)
                
                if st.button("🛒 تأكيد عملية البيع", use_container_width=True):
                    stock_df.loc[stock_df["الاسم / الوصف"] == selected_product, "الكمية المتوفرة"] -= sales_qty
                    save_secure_data(stock_df, STOCK_FILE)
                    tx_id = f"TX-{datetime.now().strftime('%d%H%M%S')}"
                    new_tx = pd.DataFrame([{
                        "معرف العملية": tx_id, "التاريخ والوقت": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "نوع الخدمة/المنتج": prod_row["نوع المنتج"], "التفاصيل": f"{selected_product}",
                        "الكمية": sales_qty, "ثمن البيع الكلي (DH)": total_checkout, "الربح الصافي (DH)": net_profit_calc
                    }])
                    sales_df = pd.concat([sales_df, new_tx], ignore_index=True)
                    save_secure_data(sales_df, SALES_FILE)
                    st.success(f"🎉 تم تسجيل البيع بنجاح! رقم العملية: {tx_id}")
                    st.rerun()

# --- القسم الثالث: مركز الطباعة والنسخ الرقمي ---
elif menu_option == "🖨️ مركز الطباعة والنسخ الرقمي":
    st.subheader("🖨️ مبيعات خدمات النسخ السريع، الطباعة والإنترنت")
    service_selected = st.selectbox("⚙️ اختر الخدمة المنجزة:", [
        "فوتوكوبي عادي (Photocopie A4)", "طباعة وثائق وبحوث (Impression)",
        "طباعة ملونة بجودة احترافية", "تجليد المستندات (Reliure / Plastification)",
        "عمليات التسجيل الإلكتروني والإنترنت"
    ])
    c1, c2 = st.columns(2)
    with c1: unit_cost = st.number_input("💵 سعر الخدمة / الورقة الواحدة (DH):", min_value=0.1, value=1.0, step=0.5)
    with c2: total_units = st.number_input("📄 إجمالي عدد الأوراق أو العمليات:", min_value=1, value=1, step=1)
    
    service_total_price = unit_cost * total_units
    service_net_profit = service_total_price * print_profit_margin 
    
    st.markdown(f"### 💵 المجموع الكلي للخدمة: <span style='color:#2563EB;'>{service_total_price:.2f} DH</span>", unsafe_allow_html=True)
    if st.button("💾 ترحيل المعاملة إلى السجل المالي", use_container_width=True):
        tx_id_serv = f"SRV-{datetime.now().strftime('%d%H%M%S')}"
        new_service_row = pd.DataFrame([{
            "معرف العملية": tx_id_serv, "التاريخ والوقت": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "نوع الخدمة/المنتج": "خدمات وطباعة", "التفاصيل": f"{service_selected} ({total_units} وحدة)",
            "الكمية": total_units, "ثمن البيع الكلي (DH)": service_total_price, "الربح الصافي (DH)": service_net_profit
        }])
        sales_df = pd.concat([sales_df, new_service_row], ignore_index=True)
        save_secure_data(sales_df, SALES_FILE)
        st.success("✅ تم حفظ الخدمة وتحديث الحسابات!")
        st.rerun()

# --- القسم الرابع: الهندسة الخلفية للمخزون (التحكم الكامل) ---
elif menu_option == "📦 الهندسة الخلفية للمخزون (التحكم الكامل)":
    st.subheader("📦 اللوحة البرمجية المتقدمة للتحكم الشامل في السلع")
    t1, t2, t3 = st.tabs(["➕ إدخال وهيكلة منتج جديد", "✏️ التعديل الجذري والتحيين الفوري", "🗑️ التطهير والحذف من النظام"])
    
    with t1:
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            new_prod_type = st.selectbox("📁 صنف المنتج الجديد بالمكتبة:", categories_list)
            new_name = st.text_input("📝 الاسم الدقيق للسلعة:")
            new_alert_limit = st.number_input("🔔 حد التنبيه للمخزون المنخفض:", min_value=0, value=3)
        with col_in2:
            new_qty_init = st.number_input("📦 إجمالي الكمية الموردة:", min_value=0, value=10)
            new_buy_price = st.number_input("💰 ثمن الشراء من الجملة (DH):", min_value=0.0, value=10.0, step=0.5)
            new_sell_price = st.number_input("💸 ثمن البيع المقترح (DH):", min_value=0.0, value=15.0, step=0.5)
            
        if st.button("🚀 دمج السلعة الجديدة", use_container_width=True):
            if new_name.strip() == "": st.error("⚠️ لا يمكن ترك الحقل فارغاً.")
            elif new_name.strip() in stock_df["الاسم / الوصف"].tolist(): st.error("⚠️ هذا المنتج مسجل مسبقاً!")
            else:
                next_index_num = len(stock_df) + 1
                new_row_data = pd.DataFrame([{
                    "الرقم الترتيبي": next_index_num, "نوع المنتج": new_prod_type, "الاسم / الوصف": new_name.strip(),
                    "الكمية المتوفرة": new_qty_init, "ثمن الشراء (DH)": new_buy_price, "ثمن البيع (DH)": new_sell_price, "الحد الأدنى للتنبيه": new_alert_limit
                }])
                stock_df = pd.concat([stock_df, new_row_data], ignore_index=True)
                save_secure_data(stock_df, STOCK_FILE)
                st.success(f"✅ تم إضافة '{new_name}' بنجاح!")
                st.rerun()
                
    with t2:
        if stock_df.empty: st.info("قائمة السلع فارغة.")
        else:
            select_modify = st.selectbox("✏️ اختر السلعة المراد تعديلها:", stock_df["الاسم / الوصف"].tolist())
            idx_mod = stock_df[stock_df["الاسم / الوصف"] == select_modify].index[0]
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                mod_name = st.text_input("تعديل الاسم:", value=stock_df.at[idx_mod, "الاسم / الوصف"])
                # التأكد من بقاء الصنف القديم في القائمة حتى لو تغيرت الإعدادات
                current_item_type = stock_df.at[idx_mod, "نوع المنتج"]
                temp_cat_list = categories_list.copy()
                if current_item_type not in temp_cat_list: temp_cat_list.append(current_item_type)
                mod_type = st.selectbox("تعديل الصنف:", temp_cat_list, index=temp_cat_list.index(current_item_type))
            with cm2:
                mod_qty = st.number_input("تعديل قطع المخزون الحالي:", min_value=0, value=int(stock_df.at[idx_mod, "الكمية المتوفرة"]))
                mod_alert = st.number_input("تعديل رقم حد التنبيه:", min_value=0, value=int(stock_df.at[idx_mod, "الحد الأدنى للتنبيه"]))
            with cm3:
                mod_buy = st.number_input("تحديث ثمن الشراء:", min_value=0.0, value=float(stock_df.at[idx_mod, "ثمن الشراء (DH)"]))
                mod_sell = st.number_input("تحديث ثمن البيع للعموم:", min_value=0.0, value=float(stock_df.at[idx_mod, "ثمن البيع (DH)"]))
                
            if st.button("💾 حفظ التعديلات الجذريّة", use_container_width=True):
                stock_df.at[idx_mod, "الاسم / الوصف"] = mod_name.strip()
                stock_df.at[idx_mod, "نوع المنتج"] = mod_type
                stock_df.at[idx_mod, "الكمية المتوفرة"] = mod_qty
                stock_df.at[idx_mod, "الحد الأدنى للتنبيه"] = mod_alert
                stock_df.at[idx_mod, "ثمن الشراء (DH)"] = mod_buy
                stock_df.at[idx_mod, "ثمن البيع (DH)"] = mod_sell
                save_secure_data(stock_df, STOCK_FILE)
                st.success("🔄 تم تحديث قاعدة بيانات المنتج!")
                st.rerun()
                
    with t3:
        if stock_df.empty: st.info("لا توجد مواد لحذفها.")
        else:
            select_del = st.selectbox("🗑️ اختر المنتج المراد حذفه نهائياً:", stock_df["الاسم / الوصف"].tolist())
            if st.button("🗑️ تأكيد التدمير النهائي للمنتج", type="primary", use_container_width=True):
                stock_df = stock_df[stock_df["الاسم / الوصف"] != select_del]
                stock_df["الرقم الترتيبي"] = range(1, len(stock_df) + 1)
                save_secure_data(stock_df, STOCK_FILE)
                st.success("💥 تم حذف المادة بنجاح.")
                st.rerun()
    st.markdown("---")
    st.dataframe(stock_df, use_container_width=True)

# --- القسم الخامس: التدقيق المالي وسجل العمليات ---
elif menu_option == "🧾 التدقيق المالي وسجل العمليات":
    st.subheader("🧾 مصفوفة تدقيق العمليات الماليّة والأرباح الصافية")
    if sales_df.empty: st.info("السجل المالي فارغ.")
    else:
        rev_sum = sales_df["ثمن البيع الكلي (DH)"].sum()
        profit_sum = sales_df["الربح الصافي (DH)"].sum()
        c_fin1, c_fin2 = st.columns(2)
        c_fin1.info(f"📊 إجمالي التدفق المالي الوارد: **{rev_sum:.2f} DH**")
        c_fin2.success(f"💸 إجمالي الأرباح الصافية: **{profit_sum:.2f} DH**")
        st.markdown("---")
        st.dataframe(sales_df.sort_values(by="التاريخ والوقت", ascending=False), use_container_width=True)
        if st.button("🚨 تصفية البيانات وإغلاق الصندوق اليومي", type="primary", use_container_width=True):
            if os.path.exists(SALES_FILE): os.remove(SALES_FILE)
            st.success("✅ تم قفل اليوم المالي!")
            st.rerun()

# ==================== 5. قسم الإعدادات الجديد (Les Paramètres) ====================
elif menu_option == "⚙️ الإعدادات (Les Paramètres)":
    st.header("⚙️ لوحة التحكم في إعدادات النظام وعملياته")
    st.write("تحكم في واجهة برمجتك والأصناف التي تشتغل بها دون لمس الكود.")
    
    with st.form("settings_form"):
        st.subheader("🏢 الهوية البصرية للبرنامج")
        new_app_name = st.text_input("اسم المكتبة (يظهر في الأعلى وفي القائمة الجانبية):", value=app_name)
        
        st.markdown("---")
        st.subheader("📁 هندسة أصناف المنتجات")
        st.write("اكتب الأصناف المفصولة بفاصلة `,` (مثال: روايات وكتب,أدوات مدرسية,أدوات مكتبية)")
        current_cats_str = ",".join(categories_list)
        new_cats_str = st.text_area("أصناف السلع النشطة بالمكتبة:", value=current_cats_str)
        
        st.markdown("---")
        st.subheader("🖨️ حسابات قسم الخدمات والطباعة")
        new_profit_margin = st.slider("هامش الربح الصافي المقدر لخدمات الفوتوكوبي والطباعة (%):", min_value=10, max_value=100, value=int(print_profit_margin * 100))
        
        # زر الحفظ داخل الـ form
        save_settings = st.form_submit_data = st.form_submit_button("💾 حفظ الإعدادات الجديدة وتحديث النظام")
        
        if save_settings:
            if new_app_name.strip() != "" and new_cats_str.strip() != "":
                config_df.at[0, "اسم_المكتبة"] = new_app_name.strip()
                config_df.at[0, "الأصناف"] = new_cats_str.strip()
                config_df.at[0, "نسبة_ربح_الطباعة"] = float(new_profit_margin)
                
                save_secure_data(config_df, CONFIG_FILE)
                st.success("⚙️ تم حفظ وتثبيت الإعدادات الجديدة بنجاح تام! جاري إعادة تشغيل الواجهة...")
                st.rerun()
            else:
                st.error("⚠️ خطأ: يرجى عدم ترك الحقول فارغة.")
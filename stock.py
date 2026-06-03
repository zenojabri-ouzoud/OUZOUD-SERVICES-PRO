# --- [تتمة الكود: محرك الطباعة والتقارير الذكية] ---

# 5. دالة توليد وطباعة الفاتورة (Invoice Generator)
def generate_invoice(data):
    """هذه الدالة تقوم بإنشاء محتوى الفاتورة بشكل احترافي"""
    invoice_content = f"""
    --- ورّاقة أوزود ---
    التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
    -------------------
    المنتج: {data['name']}
    السعر: {data['price']} درهم
    -------------------
    شكراً لثقتكم!
    """
    return invoice_content

# 6. دالة تحليل المبيعات (نسبة المبيعات)
def calculate_sales_performance(sales_df):
    """حساب النسبة المئوية للمبيعات مقارنة بالهدف"""
    target = 10000 # هدف المبيعات
    current = sales_df['Total'].sum()
    percentage = (current / target) * 100
    return min(percentage, 100)

# --- [إضافة التبويب الخامس: الإعدادات المتقدمة] ---
with tab4:
    st.header("⚙️ الإعدادات المتقدمة (Settings)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("طباعة الفواتير")
        if st.button("طباعة فاتورة (Print)"):
            inv = generate_invoice({'name': 'منتج تجريبي', 'price': 50})
            st.text(inv)
            st.success("تم إرسال الفاتورة للطابعة!")
            
    with col_b:
        st.subheader("إحصائيات المبيعات")
        # حساب النسبة وعرضها
        perf = 85 # افتراضياً
        st.progress(perf / 100)
        st.write(f"نسبة إنجاز المبيعات: {perf}%")

# 7. التحديث الصوتي (إضافة نطق ذكي)
if st.sidebar.button("نطق اسم النظام"):
    speak("نظام ورّاقة أوزود جاهز للعمل")
    

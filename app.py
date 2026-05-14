import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(
    page_title="Opener Performance Insights",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    .main {background-color: #0e1117;}
    .stMetric {
        background-color: #161b22; 
        border-radius: 10px; 
        padding: 20px; 
        border: 1px solid #30363d;
    }
    [data-testid="stMetricValue"] {color: #58a6ff;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Data Loading & Preparation
@st.cache_data
def load_and_process_data():
    df = pd.read_csv('MLA_Campaign.csv')
    
    # تعريف التصنيفات
    approved_cats = ['Approved']
    postdated_cats = ['Postdated']
    pending_cats = ['Pending Bank Approval']
    
    neutral_cats = ['Follow up', 'Retreansfer to client']
    negative_cats = ['Not interested', 'Not Eligible', 'Cancelled']
    
    # تجميع البيانات لكل موظف
    perf = df.groupby('Opener Name').agg(
        total_leads=('Opener Name', 'count'),
        approved=('Closing Status', lambda x: x.isin(approved_cats).sum()),
        postdated=('Closing Status', lambda x: x.isin(postdated_cats).sum()),
        pending_bank_approval=('Closing Status', lambda x: x.isin(pending_cats).sum())
    ).reset_index()
    
    # حساب إجمالي الـ Success (مجموع التلاتة) لحساب النسبة المئوية
    total_wins = perf['approved'] + perf['postdated'] + perf['pending_bank_approval']
    perf['Success Ratio (%)'] = (total_wins / perf['total_leads'] * 100).round(2)
    
    perf = perf.sort_values(by='total_leads', ascending=False)
    
    status_details = pd.crosstab(df['Opener Name'], df['Closing Status']).reset_index()
    full_data = pd.merge(perf, status_details, on='Opener Name')
    
    return df, perf, full_data, approved_cats, neutral_cats, negative_cats

df, opener_perf, final_details, app_cats, neu_cats, neg_cats = load_and_process_data()

# --- Date Filter Logic (Top of Page) ---
# 1. تحويل العمود لتاريخ ومعالجة الأخطاء (coerce تحول القيم الخاطئة لـ NaT)
df['Creation Date'] = pd.to_datetime(df['Creation Date'], errors='coerce')

# 2. حذف أي صفوف التاريخ فيها فارغ لضمان عمل الفلتر بشكل صحيح
df = df.dropna(subset=['Creation Date'])

# 3. تحويله إلى صيغة date فقط (بدون ساعات)
df['Creation Date'] = df['Creation Date'].dt.date

# وضع الفلتر في السايدبار
st.sidebar.header("🔍 Global Filters")

# التأكد من وجود بيانات بعد التنظيف
if not df.empty:
    min_date = df['Creation Date'].min()
    max_date = df['Creation Date'].max()

    selected_dates = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    st.error("Error: No valid dates found in 'Creation Date' column.")
    st.stop() # إيقاف التطبيق لتجنب أخطاء أخرى
# تطبيق الفلترة (الكل يعتمد على filtered_df الآن)
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered_df = df[(df['Creation Date'] >= start_date) & (df['Creation Date'] <= end_date)]
else:
    filtered_df = df

# إعادة حساب الـ Performance بناءً على الفترة المختارة فقط
opener_perf = filtered_df.groupby('Opener Name').agg(
    total_leads=('Opener Name', 'count'),
    approved=('Closing Status', lambda x: x.isin(['Approved']).sum()),
    postdated=('Closing Status', lambda x: x.isin(['Postdated']).sum()),
    pending_bank_approval=('Closing Status', lambda x: x.isin(['Pending Bank Approval']).sum())
).reset_index()

# حساب النسب المئوية للفترة المختارة
total_wins = opener_perf['approved'] + opener_perf['postdated'] + opener_perf['pending_bank_approval']
opener_perf['Success Ratio (%)'] = (total_wins / opener_perf['total_leads'] * 100).round(2)
opener_perf = opener_perf.sort_values(by='total_leads', ascending=False)

# تحديث بيانات الـ Deep Dive أيضاً
status_details = pd.crosstab(filtered_df['Opener Name'], filtered_df['Closing Status']).reset_index()
final_details = pd.merge(opener_perf, status_details, on='Opener Name')


# تعريف إعدادات الأعمدة
column_cfg = {
    "Success Ratio (%)": st.column_config.ProgressColumn(
        "Success Ratio",
        help="Ratio of Wins over Total Leads",
        format="%.2f%%", 
        min_value=0,
        max_value=100
    ),
    "total_leads": "Total Leads",
    "approved": "Approved ✅",
    "postdated": "Postdated 📅",
    "pending_bank_approval": "Pending Bank ⏳"
}

# --- Header Section ---
t1, t2 = st.columns([3, 1])
with t1:
    st.title("📊 Opener Analysis Dashboard")
    st.caption("Strategic performance metrics and status distribution for MLA Campaign")
with t2:
    st.write("") 
    st.info(f"📅 Last Sync: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

# --- Global Metrics Row 1 ---
m1, m2, m3, m4, m5 = st.columns(5)

l_count = opener_perf['total_leads'].sum()
a_count = opener_perf['approved'].sum()
p_count = opener_perf['postdated'].sum()
pb_count = opener_perf['pending_bank_approval'].sum()

total_s = a_count + p_count + pb_count
g_ratio = (total_s / l_count * 100) if l_count > 0 else 0

m1.metric("Campaign Leads", f"{l_count:,}")
m2.metric("Approved ✅", f"{a_count:,}")
m3.metric("Postdated 📅", f"{p_count:,}")
m4.metric("Pending Bank ⏳", f"{pb_count:,}")
m5.metric("Global Success Rate", f"{g_ratio:.2f}%")

# --- Global Metrics Row 2 ---
st.markdown("#### 📑 Global Status Distribution")
d1, d2, d3, d4, d5 = st.columns(5)

d1.metric("Follow Up", filtered_df[filtered_df['Closing Status'] == 'Follow up'].shape[0])
d2.metric("Not Interested", filtered_df[filtered_df['Closing Status'] == 'Not interested'].shape[0])
d3.metric("Not Eligible", filtered_df[filtered_df['Closing Status'] == 'Not Eligible'].shape[0])
d4.metric("Retransfer", filtered_df[filtered_df['Closing Status'] == 'Retreansfer to client'].shape[0])
d5.metric("Cancelled", filtered_df[filtered_df['Closing Status'] == 'Cancelled'].shape[0])

st.divider()

# --- Section 1: Overview & Rankings ---

col_table, col_chart = st.columns([1.5, 1], gap="large")     
with col_table:
    st.subheader("🏆 Performance Rankings")
    st.dataframe(
        opener_perf, 
        column_config=column_cfg,
        hide_index=True, 
        use_container_width=True
    )    

with col_chart:
    st.subheader("📈 Top 10 Volume Leaders")
    
    # تحديث الـ y لتشمل التصنيفات الجديدة بدلاً من total_approved
    fig_top = px.bar(
        opener_perf.head(10), 
        x='Opener Name', 
        y=['total_leads', 'approved', 'postdated', 'pending_bank_approval'], # الأسماء الجديدة هنا
        barmode='group',
        labels={"value": "Count", "variable": "Status"},
        color_discrete_sequence=['#58a6ff', '#238636', '#ffbd45', '#ff4b4b'], # ألوان متناسقة لكل حالة
        template="plotly_dark"
    )
    
    fig_top.update_layout(
        margin=dict(t=10, b=0, l=0, r=0), 
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_top, use_container_width=True)

# --- Section 2: Individual Deep Dive ---
st.markdown("---")
st.subheader("🎯 Individual Agent Analysis")

selected_opener = st.selectbox(
    "Search or select an Opener Name:", 
    options=opener_perf['Opener Name'].unique()
)

if selected_opener:
    row = final_details[final_details['Opener Name'] == selected_opener].iloc[0]
    
    # حساب إجمالي النجاح للموظف المختار
    ind_success = row['approved'] 
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Individual Leads", int(row['total_leads']))
    c2.metric("Total Approved", int(ind_success)) # الإجمالي الجديد
    c3.metric("Success Rate", f"{(row['Success Ratio (%)']):.2f}%")

    l_col, r_col = st.columns([1, 1.2], gap="large")
    with l_col:
        st.write(f"**Closing Inventory: {selected_opener}**")
        raw_counts = df[df['Opener Name'] == selected_opener]['Closing Status'].value_counts().reset_index()
        raw_counts.columns = ['Status', 'Count']
        st.dataframe(raw_counts, use_container_width=True, hide_index=True)

    with r_col:
        st.write(f"**Status Distribution Analysis**")
        fig_bar = px.bar(
            raw_counts, x='Status', y='Count', text='Count', color='Status',
            color_discrete_sequence=px.colors.qualitative.G10, template="plotly_dark"
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(showlegend=False, height=400, margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

# Outcomes Summary - تحديث الأسماء لتعمل بدون أخطاء
    res1, res2, res3 = st.columns(3)
    with res1:
        # هنا غيرنا 'total_approved' إلى 'approved'
        st.success(f"**POSITIVE (Approved)**  \n**{int(row['approved'])}** Leads")
        
    with res2:
        # حساب الحالات المحايدة (Neutral)
        neu = sum(row.get(c, 0) for c in neu_cats)
        st.warning(f"**NEUTRAL**  \n**{int(neu)}** Leads")
        
    with res3:
        # حساب الحالات السلبية (Negative)
        neg = sum(row.get(c, 0) for c in neg_cats)
        st.error(f"**NEGATIVE**  \n**{int(neg)}** Leads")
        

# --- Section 3: Full Data Access ---
st.divider()
with st.expander("📂 View Master Status Matrix (All Data)"):
    show_columns = [
        "Opener Name", 
        "total_leads", 
        "approved", 
        "postdated", 
        "pending_bank_approval", 
        "Success Ratio (%)",
        "Cancelled",
        "Follow up",
        "Not Eligible",
        "Not interested",
        "Retreansfer to client"
    ]
    
    st.dataframe(
        final_details,
        column_order=show_columns, # هذا السطر هو الحل لمنع التكرار
        column_config=column_cfg,
        use_container_width=True,
        hide_index=True
    )


# --- State Performance Calculation ---
state_perf = filtered_df.groupby('State').agg(
    total_leads=('State', 'count'),
    approved=('Closing Status', lambda x: x.isin(['Approved']).sum()),
    postdated=('Closing Status', lambda x: x.isin(['Postdated']).sum()),
    pending_bank_approval=('Closing Status', lambda x: x.isin(['Pending Bank Approval']).sum()),
    follow_up=('Closing Status', lambda x: (x == 'Follow up').sum()),
    not_interested=('Closing Status', lambda x: (x == 'Not interested').sum()),
    not_eligible=('Closing Status', lambda x: (x == 'Not Eligible').sum()),
    cancelled=('Closing Status', lambda x: (x == 'Cancelled').sum())
).reset_index()

# حساب نسبة النجاح (Approved + Postdated + Pending)
state_wins = state_perf['approved'] + state_perf['postdated'] + state_perf['pending_bank_approval']
state_perf['Success Ratio (%)'] = (state_wins / state_perf['total_leads'] * 100).round(2)
state_perf = state_perf.sort_values(by='total_leads', ascending=False)

st.markdown("---")
st.subheader("🗺️ Geographic Performance & Status Analysis")

# عرض الجدول مع جميع الحالات
st.dataframe(
    state_perf,
    column_config={
        "State": "State Name",
        "total_leads": "Total Leads",
        "approved": "Approved ✅",
        "postdated": "Postdated 📅",
        "pending_bank_approval": "Pending Bank ⏳",
        "follow_up": "Follow Up 📞",
        "not_interested": "Not Interested ❌",
        "not_eligible": "Not Eligible ⚠️",
        "cancelled": "Cancelled 🚫",
        "Success Ratio (%)": st.column_config.ProgressColumn(
            "Success Ratio",
            format="%.2f%%", 
            min_value=0,
            max_value=100
        )
    },
    hide_index=True,
    use_container_width=True
)

st.write("**Negative & Neutral Status Distribution by State**")
fig_neg_state = px.bar(
    state_perf.head(10),
    x='State',
    y=['follow_up', 'not_interested', 'not_eligible', 'cancelled'],
    title="Reasons for Non-Conversion by State",
    barmode='group',
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(fig_neg_state, use_container_width=True)

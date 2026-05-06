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
    approved_cats = ['Approved'] # تم التعديل لتكون Approved فقط
    postdated_cats = ['Postdated']
    pending_cats = ['Pending Bank Approval']
    
    neutral_cats = ['Follow up', 'Retreansfer to client']
    negative_cats = ['Not interested', 'Not Eligible', 'Cancelled']
    
    # تجميع البيانات لكل موظف بالتفصيل الجديد
    perf = df.groupby('Opener Name').agg(
        total_leads=('Opener Name', 'count'),
        approved=('Closing Status', lambda x: x.isin(approved_cats).sum()),
        postdated=('Closing Status', lambda x: x.isin(postdated_cats).sum()),
        pending_bank_approval=('Closing Status', lambda x: x.isin(pending_cats).sum())
    ).reset_index()
    
    # حساب إجمالي الـ Success (مجموع التلاتة) لحساب النسبة المئوية
    total_approved = perf['approved']
    total_postdated = perf['postdated'] 
    total_pending_bank_approval = perf['pending_bank_approval']
    perf['Success Ratio (%)'] = (total_approved / perf['total_leads']*100).round(2)
    
    perf = perf.sort_values(by='total_leads', ascending=False)
    
    status_details = pd.crosstab(df['Opener Name'], df['Closing Status']).reset_index()
    full_data = pd.merge(perf, status_details, on='Opener Name')
    
    return df, perf, full_data, approved_cats, neutral_cats, negative_cats

df, opener_perf, final_details, app_cats, neu_cats, neg_cats = load_and_process_data()

# تعريف إعدادات الأعمدة الموحدة لاستخدامها في أكثر من مكان
column_cfg = {
    "Success Ratio (%)": st.column_config.ProgressColumn(
        "Success Ratio",
        help="Ratio of Wins over Total Leads",
        # التعديل هنا: %.2f تعني إظهار رقمين عشريين، والـ %% تضرب في 100 وتضع العلامة
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



# --- Global Metrics Row 1: Key Performance Indicators ---
m1, m2, m3, m4 = st.columns(4)

# 1. الحسابات (تأكد من مطابقة الأسماء تماماً)
total_leads = opener_perf['total_leads'].sum()
total_approved_val = opener_perf['approved'].sum()
total_postdated_val = opener_perf['postdated'].sum() 
total_pending_val = opener_perf['pending_bank_approval'].sum()

# 2. إجمالي النجاح (Approved + Postdated + Pending)
total_success = total_approved_val + total_postdated_val + total_pending_val

# 3. حساب النسبة العالمية (بناءً على إجمالي النجاح)
global_ratio = (total_success / total_leads) if total_leads > 0 else 0

# 4. عرض المقاييس
m1.metric("Campaign Leads", f"{total_leads:,}")
m2.metric("Total Success", f"{total_success:,}") 
m3.metric("Global Success Rate", f"{(global_ratio * 100):.2f}%")
m4.metric("Active Agents", len(opener_perf))

# --- Global Metrics Row 2 ---
st.markdown("#### 📑 Global Status Distribution")
d1, d2, d3, d4, d5 = st.columns(5)

follow_up_total = df[df['Closing Status'] == 'Follow up'].shape[0]
not_interested_total = df[df['Closing Status'] == 'Not interested'].shape[0]
not_eligible_total = df[df['Closing Status'] == 'Not Eligible'].shape[0]
retransfer_total = df[df['Closing Status'] == 'Retreansfer to client'].shape[0]
cancelled_total = df[df['Closing Status'] == 'Cancelled'].shape[0]

d1.metric("Follow Up", follow_up_total)
d2.metric("Not Interested", not_interested_total)
d3.metric("Not Eligible", not_eligible_total)
d4.metric("Retransfer", retransfer_total)
d5.metric("Cancelled", cancelled_total)

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
    ind_success = row['approved'] + row['postdated'] + row['pending_bank_approval']
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Individual Leads", int(row['total_leads']))
    c2.metric("Total Wins", int(ind_success)) # الإجمالي الجديد
    c3.metric("Success Rate", f"{(row['Success Ratio (%)'] * 100):.2f}%")

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
    st.dataframe(
        final_details,
        column_config=column_cfg, # استخدام نفس الإعدادات الصحيحة
        use_container_width=True,
        hide_index=True
    )

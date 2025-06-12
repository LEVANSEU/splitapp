import streamlit as st
import pandas as pd
import io
from openpyxl import Workbook
import re

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        body, .main, .block-container {
            background-color: white !important;
            color: #222 !important;
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stTextLabelWrapper, label {
            color: #222 !important;
        }
        .stFileUploader, .stTextInput, .stSelectbox, .stRadio, .stButton, .stDataFrame,
        .stTextInput input, .stSelectbox div[data-baseweb="select"],
        .stSelectbox div[data-baseweb="select"] *,
        .stRadio div[role="radiogroup"] label,
        .stRadio div[role="radiogroup"] label * {
            background-color: #f5f5f5 !important;
            color: #222 !important;
            border-radius: 10px;
            font-size: 14px !important;
        }
        .stFileUploader {
            max-width: 600px !important;
            margin: 0 auto !important;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white !important;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 14px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .summary-header {
            display: flex;
            font-weight: bold;
            margin-top: 1em;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #999;
            text-align: center;
            background-color: #f0f0f0;
            border-radius: 8px;
            color: #222 !important;
        }
        .summary-header div {
            flex: 1;
            padding: 0.5rem;
        }
        .number-cell {
            text-align: right !important;
            font-variant-numeric: tabular-nums;
            padding-right: 1rem;
            font-weight: bold;
            color: #222;
        }
    </style>
""", unsafe_allow_html=True)

st.title("კომპანიების ანალიზი - ჩარიცხვები")

report_file = st.file_uploader("ატვირთე ანგარიშფაქტურების ფაილი (report.xlsx)", type=["xlsx"])
statement_files = st.file_uploader("ატვირთე საბანკო ამონაწერის ფაილები (statement.xlsx)", type=["xlsx"], accept_multiple_files=True)

if report_file and statement_files:
    purchases_df = pd.read_excel(report_file, sheet_name='Grid')

    bank_dfs = []
    for statement_file in statement_files:
        df = pd.read_excel(statement_file)
        df['P'] = df.iloc[:, 15].astype(str).str.strip()
        df['Name'] = df.iloc[:, 14].astype(str).str.strip()
        df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
        bank_dfs.append(df)

    bank_df = pd.concat(bank_dfs, ignore_index=True) if bank_dfs else pd.DataFrame()

    purchases_df['დასახელება'] = purchases_df['გამყიდველი'].astype(str).apply(lambda x: re.sub(r'^\(\d+\)\s*', '', x).strip())
    purchases_df['საიდენტიფიკაციო კოდი'] = purchases_df['გამყიდველი'].apply(lambda x: ''.join(re.findall(r'\d', str(x)))[:11])

    bank_company_ids = bank_df['P'].unique()
    invoice_company_ids = purchases_df['საიდენტიფიკაციო კოდი'].unique()
    missing_company_ids = [cid for cid in bank_company_ids if cid not in invoice_company_ids]

    if 'selected_missing_company' in st.session_state:
        selected_id = st.session_state['selected_missing_company']
        st.subheader(f"💸 ჩარიცხვების ცხრილი - {selected_id}")
        matching_transactions = bank_df[bank_df['P'] == str(selected_id)]
        if not matching_transactions.empty:
            st.dataframe(matching_transactions, use_container_width=True)
        else:
            st.warning("ჩანაწერი არ მოიძებნა ამ კომპანიისთვის.")
        if st.button("⬅️ დაბრუნება კომპანიის სიაზე"):
            del st.session_state['selected_missing_company']
            st.experimental_rerun()
        st.stop()

    st.subheader("კომპანიები ანგარიშფაქტურის სიაში არ არიან")
    missing_data = []
    for company_id in missing_company_ids:
        matching_rows = bank_df[bank_df['P'] == str(company_id)]
        company_name = matching_rows['Name'].iloc[0] if not matching_rows.empty else "-"
        total_amount = matching_rows['Amount'].sum()
        invoice_amount = 0.00
        difference = total_amount - invoice_amount
        missing_data.append([company_name, company_id, total_amount, invoice_amount, difference])

    st.markdown("""
    <div class='summary-header'>
        <div style='flex: 2;'>დასახელება</div>
        <div style='flex: 2;'>საიდენტიფიკაციო კოდი</div>
        <div style='flex: 1.5;'>ჩარიცხული თანხა</div>
        <div style='flex: 1.5;'>ანგარიშფაქტურის თანხა</div>
        <div style='flex: 1.5;'>სხვაობა</div>
    </div>
    """, unsafe_allow_html=True)

    for item in missing_data:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1.5, 1.5])
        with col1:
            st.write(item[0])
        with col2:
            if st.button(str(item[1]), key=f"missing_{item[1]}"):
                st.session_state['selected_missing_company'] = item[1]
        with col3:
            st.write(f"{item[2]:,.2f}")
        with col4:
            st.write(f"{item[3]:,.2f}")
        with col5:
            st.write(f"{item[4]:,.2f}")

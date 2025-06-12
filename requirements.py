
import streamlit as st
import pandas as pd
import io
from openpyxl import Workbook
import re

st.set_page_config(layout="wide")

# Read query params to detect page and selected company
params = st.experimental_get_query_params()
selected_company_id = params.get("company_id", [None])[0]

# Title
st.title("კომპანიების ანალიზი - ჩარიცხვები")

# File uploaders
report_file = st.file_uploader("ატვირთე ანგარიშფაქტურების ფაილი (report.xlsx)", type=["xlsx"])
statement_files = st.file_uploader("ატვირთე საბანკო ამონაწერის ფაილები (statement.xlsx)", type=["xlsx"], accept_multiple_files=True)

# If we are on detail page and files uploaded
if selected_company_id and report_file and statement_files:
    st.header(f"ჩარიცხვების ცხრილი - {selected_company_id}")

    bank_dfs = []
    for statement_file in statement_files:
        df = pd.read_excel(statement_file)
        df['P'] = df.iloc[:, 15].astype(str).str.strip()
        df['Name'] = df.iloc[:, 14].astype(str).str.strip()
        df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
        bank_dfs.append(df)

    bank_df = pd.concat(bank_dfs, ignore_index=True) if bank_dfs else pd.DataFrame()

    filtered_df = bank_df[bank_df["P"] == selected_company_id]

    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("ჩანაწერი ვერ მოიძებნა ამ კომპანიისთვის.")

    if st.button("⬅️ დაბრუნება სრულ სიაზე"):
        st.experimental_set_query_params()  # Clear query params
        st.experimental_rerun()

# If no company is selected, show the main page
elif report_file and statement_files:
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

    if missing_company_ids:
        st.subheader("კომპანიები ანგარიშფაქტურის სიაში არ არიან")

        for company_id in missing_company_ids:
            matching_rows = bank_df[bank_df['P'] == str(company_id)]
            company_name = matching_rows['Name'].iloc[0] if not matching_rows.empty else "-"
            total_amount = bank_df[bank_df['P'] == str(company_id)]['Amount'].sum()

            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.markdown(company_name)
            with col2:
                st.markdown(company_id)
            with col3:
                if st.button("დეტალურად ნახვა", key=f"detail_{company_id}"):
                    st.experimental_set_query_params(company_id=company_id)
                    st.experimental_rerun()
    else:
        st.success("ყველა ჩარიცხვის კოდი მოიძებნა ანგარიშფაქტურებში.")

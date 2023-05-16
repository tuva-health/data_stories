import streamlit as st
import pandas as pd

st.markdown("# Main page 🎈")
st.sidebar.markdown("# Main page 🎈")

data_sheet = 'Dates'
data_url = f"https://docs.google.com/spreadsheets/d/1gUMKZT1qd15PquTHmtK2I5AMqpVCx2W6OlcXWq2eMq8/gviz/tq?tqx=out:csv&sheet={data_sheet}"
data = pd.read_csv(data_url, nrows=52,
                   dtype={'laim Dates Table 1: Distribution of Dates YEAR_MONTH': 'str'})
data = data.rename({'Claim Dates Table 1: Distribution of Dates YEAR_MONTH': 'YEAR_MONTH'}, axis=1)
use_cols = [x for x in data.columns if 'Unnamed' not in x]
data = data.loc[:, use_cols]
data['YEAR_MONTH'] = pd.to_datetime(data['YEAR_MONTH'], format='%Y%m').dt.date

st.markdown("### Sample table component from real data")
st.write(data)
st.divider()

y_axis = st.selectbox('Select Y Parameter for Chart', [x for x in data.columns if x != 'YEAR_MONTH'])

if y_axis:
    st.line_chart(data, x='YEAR_MONTH', y=y_axis)
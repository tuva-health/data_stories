import streamlit as st
import pandas as pd

st.markdown("# Main page 🎈")
st.sidebar.markdown("# Main page 🎈")

data_sheet = 'Dates'
data_url = f"https://docs.google.com/spreadsheets/d/1gUMKZT1qd15PquTHmtK2I5AMqpVCx2W6OlcXWq2eMq8/gviz/tq?tqx=out:csv&sheet={data_sheet}"
data = pd.read_csv(data_url)

st.markdown("### Sample table component from real data")
st.write(data)
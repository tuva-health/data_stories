import streamlit as st
import pandas as pd
import snowflake.connector as sn
from dotenv import load_dotenv
import os

load_dotenv()

st.markdown("# High Level Summary")
st.sidebar.markdown("# High Level Summary")

con = sn.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse=os.getenv('SNOWFLAKE_WH'),
    role=os.getenv('SNOWFLAKE_ROLE')
)
cs = con.cursor()
cs.execute("""SELECT * FROM TUVA_PROJECT_DEMO.PMPM.PMPM_TRENDS;""")

data = cs.fetch_pandas_all()

st.markdown("### Sample table component from real data")
st.write(data)
st.divider()

y_axis = st.selectbox('Select Y Parameter for Chart', [x for x in data.columns if x != 'YEAR_MONTH'])

if y_axis:
    st.line_chart(data, x='YEAR_MONTH', y=y_axis)
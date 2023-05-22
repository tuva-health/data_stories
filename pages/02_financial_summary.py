import streamlit as st
import pandas as pd
import altair as alt
import plost
import util
import components as comp

conn = util.connection(database="dev_lipsa")

@st.cache_data
def cost_summary():
    query = """
        select *
        from dbt_lipsa.cost_summary
        order by 1, 2, 3
    """
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def year_months():
    query = """
        select distinct
           year(claim_end_date)::text || '-' ||
             lpad(month(claim_end_date)::text, 2, '0')
             as year_month
           , sum(paid_amount)
        from core.medical_claim
        group by 1
        having sum(paid_amount) > 10
        order by 1
    """
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def summary_stats():
    query = """
        with medical as (
           select distinct
               year(claim_end_date)::text year
               , sum(paid_amount) as medical_paid_amount
           from core.medical_claim
           group by 1
        )
        , pharmacy as (
           select
               year(dispensing_date)::text year
               , sum(paid_amount) as pharmacy_paid_amount
           from core.pharmacy_claim
           group by 1
        ), elig as (
           select
               substr(year_month, 0, 4) as year
               , sum(member_month_count) as member_month_count
           from pmpm._int_member_month_count
           group by 1
        )
        select *
        from medical
        join pharmacy using(year)
        join elig using(year)
    """
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def pmpm_by_claim_type():
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , claim_type
               , sum(paid_amount) as paid_amount_sum
            from core.medical_claim
            group by 1, 2
            having sum(paid_amount) > 0
            order by 1, 2 desc
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join pmpm._int_member_month_count using(year_month)
    """
    data = util.safe_to_pandas(conn, query)
    return data



@st.cache_data
def pmpm_by_service_category_1():
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , service_category_1
               , sum(paid_amount) as paid_amount_sum
            from core.medical_claim
            group by 1, 2
            having sum(paid_amount) > 0
            order by 1, 2 desc
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join pmpm._int_member_month_count using(year_month)
    """
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def pmpm_by_service_category_1_2():
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , service_category_1
               , service_category_2
               , sum(paid_amount) as paid_amount_sum
            from core.medical_claim
            group by 1, 2, 3
            having sum(paid_amount) > 0
            order by 1, 2, 3 desc
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join pmpm._int_member_month_count using(year_month)
    """
    data = util.safe_to_pandas(conn, query)
    return data


year_month_values = year_months()
year_values = sorted(list(set([x[:4] for x in year_month_values['year_month']])))

## --------------------------------- ##
## Header
## --------------------------------- ##
st.markdown("# Financial Overview")
summary_stats_data = summary_stats()
summary_stats_data = summary_stats_data.loc[summary_stats_data["year"] == year_values[-1]]

comp.financial_bans(summary_stats_data)

st.divider()
st.markdown("""
Use the following time slider to cut the following charts by the year range of your interest.
""")

start_year, end_year = st.select_slider(
    label="Select a range of years",
    options=year_values,
    value=(year_values[0], year_values[-1]),
    label_visibility='collapsed'
)
selected_range = year_values[year_values.index(start_year): year_values.index(end_year)+1]


## --------------------------------- ##
## ---                           --- ##
## --------------------------------- ##
pmpm_claim_type_data = pmpm_by_claim_type()
pmpm_claim_type_data = pmpm_claim_type_data.loc[
    pmpm_claim_type_data["year_month"].str[:4].isin(selected_range)
]
pmpm_claim_type_data = pmpm_claim_type_data\
    .groupby("claim_type", as_index=False)\
    [["paid_amount_sum", "member_month_count"]].sum()\
    .assign(paid_amount_pmpm = lambda x: x["paid_amount_sum"] / x["member_month_count"])

st.table(pmpm_claim_type_data)

# plost.bar_chart(
#     data=pmpm_claim_type_data
#     bar='',
#     value=,
#     stack='normalize',
#     direction='horizontal',
#     legend='top',
#     height=200
# )



## --------------------------------- ##
## Service Category 1
## --------------------------------- ##
st.markdown("## Service Category")
st.markdown("""
Analyzing medical claims by service category allows healthcare insurers to identify patterns, trends, and cost drivers in the service type being performed for the patient.

Here we see that, **outpatient and inpatient spend** have the highest amount of variation over time. Overall spend
seems to **spike in 2018**, driven by a large increase in outpatient spend 1 month and inpatient
spend the next.
""")
service_1_data = pmpm_by_service_category_1()
service_1_data = service_1_data.loc[
    service_1_data["year_month"].str[:4].isin(selected_range)
]

service_1_chart = alt.Chart(service_1_data).mark_bar().encode(
    x="year_month",
    y=alt.Y("paid_amount_pmpm"),
    color="service_category_1:N",
    tooltip=["service_category_1", "paid_amount_pmpm"]
).configure_legend(
  orient='bottom'
)

st.altair_chart(service_1_chart, use_container_width=True)

## --------------------------------- ##
## Service Category 2
## --------------------------------- ##
service_cat_options = service_1_data["service_category_1"].drop_duplicates().tolist()
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    Use the following dropdown to get more detail on the service category that interested you.
    """)
with col2:
    selected_service_cat = st.selectbox(
        label="Select a Service Category",
        options=service_cat_options,
        label_visibility='collapsed',
    )

service_2_data = pmpm_by_service_category_1_2()
service_2_data = service_2_data.loc[
    service_2_data["year_month"].str[:4].isin(selected_range)
    & service_2_data["service_category_1"].isin([selected_service_cat])
].drop("service_category_1", axis=1).reset_index(drop=True)
service_2_data = service_2_data\
    .groupby("service_category_2", as_index=False)\
    [["paid_amount_sum", "member_month_count"]].sum()\
    .assign(paid_amount_pmpm = lambda x: x["paid_amount_sum"] / x["member_month_count"])


service_2_chart = alt.Chart(service_2_data).mark_bar().encode(
    x="paid_amount_pmpm",
    y=alt.Y("service_category_2", sort="-x"),
    tooltip=["service_category_2", "paid_amount_pmpm"]
)

st.altair_chart(service_2_chart, use_container_width=True)


## --------------------------------- ##
## Cost Variables
## --------------------------------- ##
st.markdown("## Cost Variable Quality Summary")
cost_summary_data = cost_summary()
st.dataframe(cost_summary_data, use_container_width=True)

import streamlit as st
import pandas as pd
import altair as alt
import plost
import util

conn = util.connection(database="dev_lipsa")

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


@st.cache_data
def pmpm_by_chronic_condition():
    query = """
        with conditions as (
            select distinct
                year(condition_date)::text || '-' || lpad(month(condition_date)::text, 2, '0') as year_month
                , claim_id
                , patient_id
                , code
                , condition
                , condition_family
            from core.condition
            inner join chronic_conditions._value_set_tuva_chronic_conditions_hierarchy vs on condition.code = vs.icd_10_cm_code
            where code_type = 'icd-10-cm'
        )
        , medical_spend as (
            select
                year(claim_start_date)::text || '-' || lpad(month(claim_start_date)::text, 2, '0') as year_month
                , claim_id
                , patient_id
                , sum(paid_amount) as medical_paid_amount
            from core.medical_claim
            group by 1, 2, 3
        ), merged as (
            select
                year_month
                , condition_family
                , sum(medical_paid_amount) as medical_paid_amount_sum
            from conditions
            join medical_spend using(patient_id, claim_id, year_month)
            group by 1, 2
        )
        select
            *
        from merged
        join pmpm._int_member_month_count using(year_month)
        order by 2, 1
    """
    data = util.safe_to_pandas(conn, query)
    return data



year_month_values = year_months()
year_values = sorted(list(set([x[:4] for x in year_month_values['year_month']])))

## --------------------------------- ##
## Header
## --------------------------------- ##
st.markdown("# Financial Overview")
st.markdown(f"""
These financial summary charts offer a concise and comprehensive snapshot of your organization's financial performance, providing key metrics and insights at a glance.

The top three metrics you need to know about your data at all times are medical paid amount, pharmacy
paid amount and member months.
""")
st.markdown(f"## Spend Summary in {year_values[-1]}")
summary_stats_data = summary_stats()
summary_stats_data = summary_stats_data.loc[summary_stats_data["year"] == year_values[-1]]
col1, col2, col3 = st.columns(3)
col1.metric("Medical Spend", util.human_format(summary_stats_data["medical_paid_amount"].iloc[0]))
col2.metric("Pharmacy Spend", util.human_format(summary_stats_data["pharmacy_paid_amount"].iloc[0]))
col3.metric("Member Months", util.human_format(summary_stats_data["member_month_count"].iloc[0]))

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
st.markdown("""
Use the following dropdown to get more detail on the service category that interested you.
""")
service_cat_options = service_1_data["service_category_1"].drop_duplicates().tolist()
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
## Chronic Condition
## --------------------------------- ##
st.markdown("## Chronic Condition")
st.markdown("""
Certain conditions will be more expensive in your population. Here we see that the top driver of spend
is `Cardiovascular disease`. The second highest driver is `Metabolic Disease`.
""")
chronic_condition_data = pmpm_by_chronic_condition()
chronic_condition_data = chronic_condition_data.loc[
    chronic_condition_data["year_month"].str[:4].isin(selected_range)
]
chronic_condition_data = chronic_condition_data\
    .groupby("condition_family", as_index=False)\
    [["medical_paid_amount_sum", "member_month_count"]].sum()\
    .assign(medical_paid_amount_pmpm = lambda x: x["medical_paid_amount_sum"] / x["member_month_count"])\
    .round()

st.dataframe(
    chronic_condition_data[["condition_family", "medical_paid_amount_pmpm"]],
    use_container_width=True
)

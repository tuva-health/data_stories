import streamlit as st
import pandas as pd
import altair as alt
import plost
import util
import components

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


## --------------------------------- ##
## Chronic Condition
## --------------------------------- ##
st.markdown("## Chronic Condition")
st.markdown(
    """
Certain conditions will be more expensive in your population. Here we see that the top driver of spend
is `Cardiovascular disease`. The second highest driver is `Metabolic Disease`.
"""
)

year_month_values = year_months()
year_values = sorted(list(set([x[:4] for x in year_month_values["year_month"]])))
selected_range = components.year_slider(year_values)


chronic_condition_data = pmpm_by_chronic_condition()
chronic_condition_data = chronic_condition_data.loc[
    chronic_condition_data["year_month"].str[:4].isin(selected_range)
]
chronic_condition_data = (
    chronic_condition_data.groupby("condition_family", as_index=False)[
        ["medical_paid_amount_sum", "member_month_count"]
    ]
    .sum()
    .assign(
        medical_paid_amount_pmpm=lambda x: x["medical_paid_amount_sum"]
        / x["member_month_count"]
    )
    .round()
    .sort_values("medical_paid_amount_pmpm", ascending=False)
)

st.dataframe(
    chronic_condition_data[["condition_family", "medical_paid_amount_pmpm"]],
    use_container_width=True,
)

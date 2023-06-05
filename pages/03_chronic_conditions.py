import streamlit as st
import plost
import components
import data


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

year_month_values = data.year_months()
year_values = sorted(list(set([x[:4] for x in year_month_values["year_month"]])))
selected_range = components.year_slider(year_values)


chronic_condition_counts = data.condition_data()
chronic_condition_data = data.pmpm_by_chronic_condition()
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
st.divider()

st.markdown("### Top 5 Condition Diagnoses Over Claim Period")
st.markdown(
    """The chart below shows trends in new cases of the top five chronic conditions during the
claims period selected."""
)
msk = chronic_condition_counts["diagnosis_year"].isin(selected_range)
filtered_cond_data = chronic_condition_counts.loc[msk, :]
top5_conditions = (
    filtered_cond_data.groupby("condition")["condition_cases"].sum().nlargest(5)
)
msk = filtered_cond_data["condition"].isin(top5_conditions.index)
top5_filtered_cond = filtered_cond_data.loc[msk, :]

plost.line_chart(
    data=top5_filtered_cond,
    x="diagnosis_year_month",
    y="condition_cases",
    color="condition",
    pan_zoom=None,
    height=400,
)

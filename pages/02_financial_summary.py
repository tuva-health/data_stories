import streamlit as st
import altair as alt
import util
import components as comp
import data
import time
import pandas as pd


def group_for_pmpm(df, grouping_column):
    grouped_df = (
        df.groupby(grouping_column, as_index=False)[
            ["paid_amount_sum", "member_month_count"]
        ]
        .sum()
        .assign(
            paid_amount_pmpm=lambda x: x["paid_amount_sum"] / x["member_month_count"]
        )
    )
    return grouped_df


year_month_values = sorted(list(set(data.year_months()["year_month"])))

year_values = sorted(list(set([x[:4] for x in year_month_values])))
## --------------------------------- ##
## ---                           --- ##
## --------------------------------- ##
pmpm_claim_type_data = data.pmpm_by_claim_type()
pmpm_claim_type_data.sort_values(by="year_month", inplace=True)

## --------------------------------- ##
## Header
## --------------------------------- ##
st.markdown("# Financial Overview")
start_year, end_year = st.select_slider(
    label="Select a range of years",
    options=year_values,
    value=(year_values[0], year_values[-1]),
    label_visibility="collapsed",
)
selected_range = year_values[
    year_values.index(start_year) : year_values.index(end_year) + 1
]

if len(selected_range) == 1:
    year_string = selected_range[0]
else:
    year_string = "{} - {}".format(selected_range[0], selected_range[-1])

st.markdown(
    f"""
    These financial summary charts offer a concise and comprehensive snapshot of your organization's financial
    performance, providing key metrics and insights at a glance.

    The top three metrics you need to know about your data at all times are medical paid amount, pharmacy
    paid amount and PMPM."""
)
st.markdown(f"### Spend Summary in {year_string}")
summary_stats_data = data.summary_stats()
summary_stats_data = summary_stats_data.loc[
    summary_stats_data["year"].isin(selected_range)
]
pmpm_claim_type_data = pmpm_claim_type_data.loc[
    pmpm_claim_type_data["year"].isin(selected_range)
]

if "iteration" not in st.session_state:
    st.session_state["iteration"] = 0

col1, col2 = st.columns([1, 3])
with col1:
    comp.financial_bans(summary_stats_data, direction="vertical")
with col2:
    animate = False
    month_list = sorted(list(set(pmpm_claim_type_data["year_month"])))
    if animate:
        while st.session_state["iteration"] < len(month_list):
            comp.claim_type_line_chart(pmpm_claim_type_data, True)
            time.sleep(0.05)
            st.session_state["iteration"] += 1

            if st.session_state["iteration"] < len(month_list) and animate:
                st.experimental_rerun()
    else:
        comp.claim_type_line_chart(pmpm_claim_type_data, False)


## --------------------------------- ##
## Spend Change
## --------------------------------- ##

for ctype in ["medical", "pharmacy", "total"]:
    summary_stats_data[f"current_period_{ctype}_pmpm"] = (
        summary_stats_data[f"current_period_{ctype}_paid"]
        .astype(float)
        .div(
            summary_stats_data["current_period_member_months"].astype(float),
            fill_value=0,
        )
    )
    summary_stats_data[f"prior_period_{ctype}_pmpm"] = (
        summary_stats_data[f"prior_period_{ctype}_paid"]
        .astype(float)
        .div(
            summary_stats_data["prior_period_member_months"].astype(float), fill_value=0
        )
    )
    summary_stats_data[f"pct_change_{ctype}_pmpm"] = (
        summary_stats_data[f"current_period_{ctype}_pmpm"]
        - summary_stats_data[f"prior_period_{ctype}_pmpm"]
    ).div(summary_stats_data[f"prior_period_{ctype}_pmpm"], fill_value=0)


# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)
st.markdown(
    """
   Get a better sense of the change over time using this table.
"""
)
test = pd.concat(
    [
        summary_stats_data.assign(category=lambda x: ctype.title())[
            [
                "year",
                "category",
                f"prior_period_{ctype}_pmpm",
                f"current_period_{ctype}_pmpm",
                f"pct_change_{ctype}_pmpm",
            ]
        ].rename(
            columns={
                f"current_period_{ctype}_pmpm": "current_period_pmpm",
                f"prior_period_{ctype}_pmpm": "prior_period_pmpm",
                f"pct_change_{ctype}_pmpm": "pct_change_pmpm",
            }
        )
        for ctype in ["medical", "pharmacy", "total"]
    ]
)
test = test.loc[test.year != year_values[0]]
st.table(util.format_df(test))

comp.pop_grouped_bar(test)

## --------------------------------- ##
## Service Category 1
## --------------------------------- ##
st.markdown("## Service Category")
st.markdown(
    """
Analyzing medical claims by service category allows healthcare insurers to identify patterns, trends, and cost drivers in the service type being performed for the patient.

Here we see that, **outpatient and inpatient spend** have the highest amount of variation over time. Overall spend
seems to **spike in 2018**, driven by a large increase in outpatient spend 1 month and inpatient
spend the next.
"""
)
service_1_data = data.pmpm_by_service_category_1()
service_1_data = service_1_data.loc[
    service_1_data["year_month"].str[:4].isin(selected_range)
]

service_1_chart = (
    alt.Chart(service_1_data)
    .mark_bar()
    .encode(
        x="year_month",
        y=alt.Y("paid_amount_pmpm"),
        color="service_category_1:N",
        tooltip=["service_category_1", "paid_amount_pmpm"],
    )
    .configure_legend(orient="bottom")
)

st.altair_chart(service_1_chart, use_container_width=True)

# chart_vals = ["Ancillary", "Inpatient", "Office Visit", "Other", "Outpatient"]
# grouped_service = service_1_data.groupby(by="service_category_1", as_index=False)[
#     "paid_amount_sum"
# ].sum()
# total_member_months = (
#     service_1_data[["year_month", "member_month_count"]]
#     .drop_duplicates()["member_month_count"]
#     .sum()
# )
# grouped_service["paid_amount_pmpm"] = (
#     grouped_service["paid_amount_sum"] / total_member_months
# )
# grouped_service.set_index("service_category_1", inplace=True)
# grouped_service = grouped_service.transpose()
# grouped_service["Metric"] = "Average PMPM"
# plost.bar_chart(
#     data=grouped_service,
#     bar="Metric",
#     value=chart_vals,
#     stack="normalize",
#     direction="horizontal",
#     height=200,
# )

## --------------------------------- ##
## Drilldown from Service Category 1
## --------------------------------- ##
service_cat_options = service_1_data["service_category_1"].drop_duplicates().tolist()
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        """
    Use the following dropdown to get more detail on the service category that interested you.
    """
    )
with col2:
    selected_service_cat = st.selectbox(
        label="Select a Service Category",
        options=service_cat_options,
        label_visibility="collapsed",
    )
with col3:
    selected_year_month = st.selectbox(
        label="Select a Year Month",
        options=["All Time"] + year_month_values,
        label_visibility="collapsed",
    )

# Fetch and filter data based on selections above
service_2_data = data.pmpm_by_service_category_1_2()
service_2_data = (
    service_2_data.loc[
        service_2_data["year_month"].str[:4].isin(selected_range)
        & (
            (service_2_data["year_month"] == selected_year_month)
            | (selected_year_month == "All Time")
        )
        & service_2_data["service_category_1"].isin([selected_service_cat])
    ]
    .drop("service_category_1", axis=1)
    .reset_index(drop=True)
)

condition_data = data.pmpm_by_service_category_1_condition()
condition_data = (
    condition_data.loc[
        condition_data["year_month"].str[:4].isin(selected_range)
        & (
            (condition_data["year_month"] == selected_year_month)
            | (selected_year_month == "All Time")
        )
        & condition_data["service_category_1"].isin([selected_service_cat])
    ]
    .drop("service_category_1", axis=1)
    .reset_index(drop=True)
)

provider_data = data.pmpm_by_service_category_1_provider()
provider_data = (
    provider_data.loc[
        provider_data["year_month"].str[:4].isin(selected_range)
        & (
            (provider_data["year_month"] == selected_year_month)
            | (selected_year_month == "All Time")
        )
        & provider_data["service_category_1"].isin([selected_service_cat])
    ]
    .drop("service_category_1", axis=1)
    .reset_index(drop=True)
)

claim_type_data = data.pmpm_by_service_category_1_claim_type()
claim_type_data = (
    claim_type_data.loc[
        claim_type_data["year_month"].str[:4].isin(selected_range)
        & (
            (claim_type_data["year_month"] == selected_year_month)
            | (selected_year_month == "All Time")
        )
        & claim_type_data["service_category_1"].isin([selected_service_cat])
    ]
    .drop("service_category_1", axis=1)
    .reset_index(drop=True)
)

# Re-group to get PMPM
claim_type_data = group_for_pmpm(claim_type_data, "claim_type")
condition_data = group_for_pmpm(condition_data, "condition_family")
provider_data = group_for_pmpm(provider_data, "provider_name")
service_2_data = group_for_pmpm(service_2_data, "service_category_2")

top_col1, top_col2 = st.columns(2)
bot_col1, bot_col2 = st.columns(2)
with top_col1:
    title = "PMPM by Service Category 2"
    comp.generic_simple_v_bar(
        df=service_2_data, x="paid_amount_pmpm", y="service_category_2", title=title
    )
with top_col2:
    title = "Top 5 Conditions by PMPM"
    comp.generic_simple_v_bar(
        df=condition_data,
        x="paid_amount_pmpm",
        y="condition_family",
        title=title,
        top_n=5,
    )
with bot_col1:
    title = "Top 10 Providers by PMPM"
    comp.generic_simple_v_bar(
        df=provider_data, x="paid_amount_pmpm", y="provider_name", title=title, top_n=10
    )
with bot_col2:
    title = "PMPM by Claim Type"
    comp.generic_simple_v_bar(
        df=claim_type_data, x="paid_amount_pmpm", y="claim_type", title=title
    )


## --------------------------------- ##
## --- Pharmacy Spend            --- ##
## --------------------------------- ##
st.markdown("## Pharmacy Spend")
st.markdown(
    """
A look at pharmacy spend over time during the claims period selected.
"""
)
pharm_pmpm = data.pmpm_by_claim_type()
pharm_pmpm = pharm_pmpm.loc[pharm_pmpm["claim_type"] == "pharmacy", :]
pharm_pmpm = pharm_pmpm.loc[pharm_pmpm["year_month"].str[:4].isin(selected_range)]
st.line_chart(data=pharm_pmpm, x="year_month", y="paid_amount_sum")

## --------------------------------- ##
## Cost Variables
## --------------------------------- ##
st.markdown("## Quality Summary")
"""
This table details all the use cases for the Tuva Project and relevant claim rows that
failed our tests. It is recommended that you look into these test results to
improve the quality of your data and thus, trust in the analysis above.
"""
use_case_data = data.use_case()
st.dataframe(use_case_data, use_container_width=True)

st.markdown(
    """
You can also review specific test results in the following table that lists
all the checks that failed.
"""
)
test_result_data = data.test_results()
st.dataframe(test_result_data, use_container_width=True)

st.markdown(
    """
Then check out the distribution of cost for the spend variables.
"""
)
cost_summary_data = data.cost_summary()
st.dataframe(cost_summary_data, use_container_width=True)

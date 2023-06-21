import streamlit as st
from st_pages import show_pages_from_config, add_page_title
import altair as alt
import util
import components as comp
import data
from palette import ORDINAL, PALETTE
import time
import pandas as pd


## --------------------------------- ##
## --- Page Setup
## --------------------------------- ##
st.set_page_config(
    layout="wide",
    page_icon=comp.favicon(),
    page_title="Tuva Health - Financial Datastory",
    initial_sidebar_state="expanded",
)
comp.add_logo()
st.image(comp.tuva_logo())
add_page_title()
show_pages_from_config()

## --------------------------------- ##
## ---                           --- ##
## --------------------------------- ##
year_month_values = sorted(list(set(data.year_months()["year_month"])))

year_values = sorted(list(set([x[:4] for x in year_month_values])))
pmpm_claim_type_data = data.pmpm_by_claim_type()
pmpm_claim_type_data.sort_values(by="year_month", inplace=True)

## --------------------------------- ##
## Header
## --------------------------------- ##
st.markdown(
    f"""
    These financial summary charts provide a breakdown of the 2020 Medicare LDS data, which is a 5% national sample of all Medicare fee-for-service claims data.
    We used the Tuva Medicare LDS Connector to transform the LDS data into the Tuva claims data model. We then used the following Tuva data marts to prepare the data for analysis:
    The following Tuva data marts were used to transform the Medicare LDS data for this analysis:

    Member Months: A data mart that converts eligibility data into member months
    Service Category Grouper: A data mart that groups claims into one of 17 service categories
    PMPM: A data mart that calculates per-member-per-month costs

    """
)

if len(year_values) > 1:
    st.markdown(
        """Simply slide the time slider below to analyze financial trends over different
    periods, gaining valuable insights into the ever-changing healthcare landscape."""
    )
    start_year, end_year = st.select_slider(
        label="Select a range of years",
        options=year_values,
        value=(year_values[0], year_values[-1]),
        label_visibility="collapsed",
    )
    selected_range = year_values[
        year_values.index(start_year) : year_values.index(end_year) + 1
    ]
else:
    selected_range = year_values


if len(selected_range) == 1:
    year_string = selected_range[0]
else:
    year_string = "{} - {}".format(selected_range[0], selected_range[-1])
st.markdown(
    f"""
    ### Spend Summary in {year_string}

    Let's review your key financial performance indicators.
"""
)
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
            comp.claim_type_line_chart(pmpm_claim_type_data, "525px", True)
            time.sleep(0.05)
            st.session_state["iteration"] += 1

            if st.session_state["iteration"] < len(month_list) and animate:
                st.experimental_rerun()
    else:
        comp.claim_type_line_chart(pmpm_claim_type_data.round(), "525px", False)


## --------------------------------- ##
## Spend Change
## --------------------------------- ##
st.markdown(
    f"""
     ### Spend Change over Time

     View the following chart to understand changes in medical
     spend over several years.
"""
)
for ctype in ["medical"]:
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
test = pd.concat(
    [
        summary_stats_data.assign(category=lambda x: ctype.title())[
            [
                "display",
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
        for ctype in [
            "medical",
        ]
    ]
)

tab1, tab2 = st.tabs(["Chart", "Data"])
with tab1:
    comp.pop_grouped_bar(test)
with tab2:
    st.table(util.format_df(test.sort_values("category")))

## --------------------------------- ##
## Service Category 1
## --------------------------------- ##
st.markdown("### Service Category")
st.markdown(
    """
    Analyzing medical claims by service category allows healthcare insurers
    to identify patterns, trends, and cost drivers in the service type being
    performed for the patient.
"""
)
service_1_data = data.pmpm_by_service_category_1()
service_1_data = service_1_data.loc[
    service_1_data["year_month"].str[:4].isin(selected_range)
]
cat_to_color = dict(zip(sorted(service_1_data["service_category_1"].unique()), ORDINAL))

highlight = alt.selection_point(
    on="mouseover",
    clear="mouseout",
    fields=["service_category_1"],
    nearest=True,
)

service_1_chart = (
    alt.Chart(service_1_data.round())
    .mark_bar()
    .encode(
        x="year_month",
        y=alt.Y("paid_amount_pmpm"),
        color=alt.Color("service_category_1").scale(
            domain=list(cat_to_color.keys()), range=list(cat_to_color.values())
        ),
        opacity=alt.condition(highlight, alt.value(1.0), alt.value(0.3)),
        tooltip=["year_month", "service_category_1", "paid_amount_pmpm"],
    )
    .add_selection(highlight)
    .configure_legend(orient="bottom")
    .properties(height=500)
)

st.altair_chart(service_1_chart, use_container_width=True)


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
        (
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
        (
            (condition_data["year_month"] == selected_year_month)
            | (selected_year_month == "All Time")
        )
        & condition_data["service_category_1"].isin([selected_service_cat])
    ]
    .drop("service_category_1", axis=1)
    .reset_index(drop=True)
)

provider_data = data.pmpm_by_service_category_1_provider(
    selected_service_cat, selected_year_month
)

claim_type_data = data.pmpm_by_service_category_1_claim_type()
claim_type_data = (
    claim_type_data.loc[
        (
            (claim_type_data["year_month"] == selected_year_month)
            | (selected_year_month == "All Time")
        )
        & claim_type_data["service_category_1"].isin([selected_service_cat])
    ]
    .drop("service_category_1", axis=1)
    .reset_index(drop=True)
)

# Re-group to get PMPM
claim_type_data = util.group_for_pmpm(claim_type_data, "claim_type")
condition_data = util.group_for_pmpm(condition_data, "condition_family")
service_2_data = util.group_for_pmpm(service_2_data, "service_category_2")

top_col1, top_col2 = st.columns(2)
bot_col1, bot_col2 = st.columns(2)
with top_col1:
    title = "PMPM by Service Category 2"
    comp.generic_simple_v_bar(
        df=service_2_data.round(),
        x="paid_amount_pmpm",
        y="service_category_2",
        title=title,
        color=PALETTE["4-cerulean"],
        height="350px",
    )
with top_col2:
    title = "Top 5 Conditions by PMPM"
    comp.generic_simple_v_bar(
        df=condition_data.round(),
        x="paid_amount_pmpm",
        y="condition_family",
        title=title,
        top_n=5,
        color=PALETTE["melon"],
        height="350px",
    )
with bot_col1:
    title = "Top 10 Providers by PMPM"
    comp.generic_simple_v_bar(
        df=provider_data.round(5),
        x="paid_amount_pmpm",
        y="provider_name",
        title=title,
        top_n=10,
        color=PALETTE["french-grey"],
        height="350px",
    )
with bot_col2:
    title = "PMPM by Claim Type"
    comp.generic_simple_v_bar(
        df=claim_type_data.round(),
        x="paid_amount_pmpm",
        y="claim_type",
        title=title,
        color=PALETTE["2-light-sky-blue"],
        height="350px",
    )


## --------------------------------- ##
## Cost Variables
## --------------------------------- ##
st.markdown("### Quality Summary")
"""
Here we used the Tuva data profiling data mart to analyze the data quality of the LDS data.
This data mart looks for approximately 250 different types of data quality issues that can occur
in claims data.
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

# st.markdown(
#     """
# Then check out the distribution of cost for the spend variables.
# """
# )
# cost_summary_data = data.cost_summary()
# st.dataframe(cost_summary_data, use_container_width=True)

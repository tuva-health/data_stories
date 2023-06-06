import streamlit as st
from streamlit_echarts import st_echarts
import util
import toolz as to
from palette import PALETTE

from streamlit_extras.metric_cards import style_metric_cards

style_args = {
    "border_size_px": 0,
    "border_left_color": PALETTE["4-cerulean"]
}


def financial_bans(summary_stats_data, direction="horizontal"):
    # TODO: Add Year filter
    """Takes dataframe of financial summary data at the year level and displays BANs
    for med spend, pharm spend, member months and average pmpm. Can handle dataframe with
    multiple years or a single year. Dataframe should be pre-filtered to the time frame desired.
    """
    year_values = sorted(list(set(summary_stats_data["year"])))
    summary_stats_data = summary_stats_data.copy(deep=True)
    summary_stats_data = summary_stats_data.loc[
        summary_stats_data["year"].isin(year_values)
    ]

    med_spend = summary_stats_data["current_period_medical_paid"].sum()
    pharm_spend = summary_stats_data["current_period_pharmacy_paid"].sum()
    member_mon_count = summary_stats_data["current_period_member_months"].sum()
    avg_pmpm = med_spend / member_mon_count
    if direction == "vertical":
        st.metric("Medical Spend", util.human_format(med_spend))
        st.metric("Pharmacy Spend", util.human_format(pharm_spend))
        st.metric("Member Months", util.human_format(member_mon_count))
        st.metric("Average PMPM", util.human_format(avg_pmpm))
        style_metric_cards(**style_args)
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Medical Spend", util.human_format(med_spend))
        col2.metric("Pharmacy Spend", util.human_format(pharm_spend))
        col3.metric("Member Months", util.human_format(member_mon_count))
        col4.metric("Average PMPM", util.human_format(avg_pmpm))
        style_metric_cards(**style_args)


def year_slider(year_values):
    st.divider()
    st.markdown(
        """
    Use the following time slider to cut the following charts by the year range of your interest.
    """
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
    return selected_range


def claim_type_line_chart(df, animated=True):
    if animated:
        t = st.session_state["iteration"]
        month_list = sorted(list(set(df["year_month"])))
        anim_data = df.loc[df["year_month"] <= month_list[t], :]
        list_data = [anim_data.columns.to_list()] + anim_data.values.tolist()
    else:
        list_data = [df.columns.to_list()] + df.values.tolist()
    series = list(set(df["claim_type"]))
    datasetWithFilters = [
        {
            "id": f"dataset_{s}",
            "fromDatasetId": "dataset_raw",
            "transform": {
                "type": "filter",
                "config": {
                    "and": [
                        {"dimension": "claim_type", "=": s},
                    ]
                },
            },
        }
        for s in series
    ]
    seriesList = [
        {
            "type": "line",
            "datasetId": f"dataset_{s}",
            "showSymbol": False,
            "name": s,
            "labelLayout": {"moveOverlap": "shiftY"},
            "emphasis": {"focus": "series"},
            "encode": {
                "x": "year_month",
                "y": "paid_amount_pmpm",
                "label": ["claim_type", "paid_amount_pmpm"],
                "itemName": "year_month",
                "tooltip": ["paid_amount_pmpm"],
            },
        }
        for s in series
    ]
    option = {
        "color": ["#06405C", "#FFCC05", "#66B1E2"],
        "dataset": [{"id": "dataset_raw", "source": list_data}] + datasetWithFilters,
        "title": {"text": "Paid Amount PMPM by Claim Type"},
        "tooltip": {"order": "valueDesc", "trigger": "axis"},
        "xAxis": {"type": "category", "nameLocation": "middle"},
        "yAxis": {"name": "PMPM"},
        "grid": {"right": 140},
        "series": seriesList,
    }
    st_echarts(options=option, height="400px", key="chart")


def pop_grouped_bar(df):
    pivoted_df = df.pivot(
        index="category", columns="year", values="current_period_pmpm"
    ).reset_index()
    list_data = [pivoted_df.columns.to_list()] + pivoted_df.values.tolist()
    option = {
        "legend": {},
        "tooltip": {},
        "dataset": {"source": list_data},
        "xAxis": {"type": "category", "data": sorted(list(set(df["category"])))},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar"} for x in list(set(df["year"]))],
    }
    st_echarts(options=option)

import streamlit as st
import pandas as pd
import dask.dataframe as dd
import util

conn = util.connection(database="dev_lipsa")
s3_uri = "s3://tuva-public-resources/data-extracts/lds/"

global_converters = {"year": str}


@st.cache_data
def test_results():
    query = """
    select * from data_profiling.test_result
    """

    data = pd.read_csv(s3_uri + "test_results.csv")
    return data


@st.cache_data
def use_case():
    query = """
    select * from data_profiling.use_case
    """

    data = pd.read_csv(s3_uri + "use_case.csv")
    return data


@st.cache_data
def cost_summary():
    query = """
        select *
        from dbt_lipsa.cost_summary
        order by 1, 2, 3
    """

    data = pd.read_csv(s3_uri + "cost_summary.csv")
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

    data = pd.read_csv(s3_uri + "year_months.csv")
    return data


@st.cache_data
def summary_stats():
    query = """
    with medical as (
       select distinct
           year(claim_end_date)::text year
           , quarter(claim_end_date)::text quarter
           , sum(paid_amount) as medical_paid_amount
       from core.medical_claim
       group by 1, 2
    )
    , elig as (
       select
            substr(year_month, 0, 4) as year
           , quarter(to_date(concat(year_month, '01'), 'YYYYMMDD')) as quarter
           , sum(member_months) as member_month_count
       from pmpm.pmpm
       group by 1, 2
    )
    select
        concat(year, 'Q', quarter) as display
        , year
        , quarter
        , lag(quarter) over(order by quarter) as prior_quarter
        , medical_paid_amount as current_period_medical_paid
        , lag(medical_paid_amount) over(order by quarter) as prior_period_medical_paid
        , div0null(
             medical_paid_amount - lag(medical_paid_amount) over(order by quarter),
             lag(medical_paid_amount) over(order by quarter)
          ) as pct_change_medical_paid
        , member_month_count as current_period_member_months
        , lag(member_month_count) over(order by quarter) as prior_period_member_months
        , div0null(
             member_month_count - lag(member_month_count) over(order by quarter),
             lag(member_month_count) over(order by quarter)
        ) as pct_change_member_months
    from medical
    join elig using(year, quarter)
    """

    data = pd.read_csv(s3_uri + "summary_stats.csv", converters=global_converters)
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
        ), pharmacy_summary as (
           select
               year(dispensing_date)::text || '-' ||
                 lpad(month(dispensing_date)::text, 2, '0')
                 as year_month
               , 'pharmacy' as claim_type
               , sum(paid_amount) as paid_amount_sum
           from core.pharmacy_claim
           group by 1
        ), together as (
           select * from spend_summary union all
           select * from pharmacy_summary
        ), elig as (
            select
            CONCAT(LEFT(year_month, 4), '-', RIGHT(year_month, 2)) as year_month
           , member_months as member_month_count
            from pmpm.pmpm
        )
        select
           *
           , substr(year_month, 0, 4) as year
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from together
        join elig using(year_month)
    """

    data = pd.read_csv(s3_uri + "pmpm_by_claim_type.csv", converters=global_converters)
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
               , count(*) as row_count
            from core.medical_claim
            left join service_category.service_category_grouper using(claim_id, claim_line_number)
            group by 1, 2
            having sum(paid_amount) > 0
            order by 1, 2 desc
        ), elig as (
            select
            CONCAT(LEFT(year_month, 4), '-', RIGHT(year_month, 2)) as year_month
           , member_months as member_month_count
            from pmpm.pmpm
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join elig using(year_month)
    """

    data = pd.read_csv(s3_uri + "pmpm_by_service_category_1.csv")
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
               , count(*) as row_count
            from core.medical_claim
            left join service_category.service_category_grouper using(claim_id, claim_line_number)
            group by 1, 2, 3
            having sum(paid_amount) > 0
            order by 1, 2, 3 desc
        ), elig as (
            select
            CONCAT(LEFT(year_month, 4), '-', RIGHT(year_month, 2)) as year_month
           , member_months as member_month_count
            from pmpm.pmpm
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join elig using(year_month)
    """

    data = pd.read_csv(s3_uri + "pmpm_by_service_category_1_2.csv")
    return data


@st.cache_data
def pmpm_by_service_category_1_provider(service_cat, year_month):
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , service_category_1
               , p.provider_name
               , sum(paid_amount) as paid_amount_sum
               , count(*) as row_count
            from core.medical_claim c
            left join service_category.service_category_grouper using(claim_id, claim_line_number)
            left join core.provider p
            on c.rendering_npi = p.npi
            group by 1, 2, 3
            having sum(paid_amount) > 0
            order by 1, 2, 3 desc
        ), elig as (
            select
            CONCAT(LEFT(year_month, 4), '-', RIGHT(year_month, 2)) as year_month
           , member_months as member_month_count
            from pmpm.pmpm
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join elig using(year_month)
    """
    data_path = s3_uri + "pmpm_by_service_category_1_provider.csv"
    data = dd.read_csv(data_path, storage_options={"anon": True})
    data = (
        data.loc[
            ((data["year_month"] == year_month) | (year_month == "All Time"))
            & data["service_category_1"].isin([service_cat])
        ]
        .drop("service_category_1", axis=1)
        .reset_index(drop=True)
    )

    grouped = util.group_for_pmpm(data, "provider_name")
    return grouped.compute()


@st.cache_data
def pmpm_by_service_category_1_condition():
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , service_category_1
               , cc.condition_family
               , sum(paid_amount) as paid_amount_sum
               , count(*) as row_count
            from core.medical_claim mc
            left join service_category.service_category_grouper using(claim_id, claim_line_number)
            left join chronic_conditions.tuva_chronic_conditions_long cc
            on mc.patient_id = cc.patient_id
            and cc.last_diagnosis_date >= mc.claim_end_date
            and cc.first_diagnosis_date <= mc.claim_end_date
            group by 1, 2, 3
            having sum(paid_amount) > 0
            order by 1, 2, 3 desc
        ), elig as (
            select
            CONCAT(LEFT(year_month, 4), '-', RIGHT(year_month, 2)) as year_month
           , member_months as member_month_count
            from pmpm.pmpm
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join elig using(year_month)
    """

    data = pd.read_csv(s3_uri + "pmpm_by_service_category_1_condition.csv")
    return data


@st.cache_data
def pmpm_by_service_category_1_claim_type():
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , service_category_1
               , claim_type
               , sum(paid_amount) as paid_amount_sum
               , count(*) as row_count
            from core.medical_claim c
            left join service_category.service_category_grouper using(claim_id, claim_line_number)
            group by 1, 2, 3
            having sum(paid_amount) > 0
            order by 1, 2, 3 desc
        ), elig as (
            select
            CONCAT(LEFT(year_month, 4), '-', RIGHT(year_month, 2)) as year_month
           , member_months as member_month_count
            from pmpm.pmpm
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join elig using(year_month)
    """

    data = pd.read_csv(s3_uri + "pmpm_by_service_category_1_claim_type.csv")
    return data


@st.cache_data
def pmpm_data():
    query = """SELECT PT.*, PB.MEMBER_COUNT, PHARMACY_SPEND FROM PMPM.PMPM_TRENDS PT
              LEFT JOIN (SELECT CONCAT(LEFT(YEAR_MONTH, 4), '-', RIGHT(YEAR_MONTH, 2)) AS YEAR_MONTH,
                         COUNT(*) AS MEMBER_COUNT,
                         SUM(PHARMACY_PAID) AS PHARMACY_SPEND
                         FROM PMPM.PMPM_BUILDER
                         GROUP BY YEAR_MONTH) AS PB
              ON PT.YEAR_MONTH = PB.YEAR_MONTH;"""

    data = pd.read_csv(s3_uri + "pmpm_data.csv")
    # data["year_month"] = pd.to_datetime(data["year_month"], format="%Y-%m").dt.date
    data["year"] = data["year_month"].str[:4]
    data["pharmacy_spend"] = data["pharmacy_spend"].astype(float)

    return data


@st.cache_data
def gender_data():
    query = """SELECT GENDER, COUNT(*) AS COUNT FROM CORE.PATIENT GROUP BY 1;"""

    data = pd.read_csv(s3_uri + "gender_data.csv")
    return data


@st.cache_data
def race_data():
    query = """SELECT RACE, COUNT(*) AS COUNT FROM CORE.PATIENT GROUP BY 1;"""

    data = pd.read_csv(s3_uri + "race_data.csv")
    return data


@st.cache_data
def age_data():
    query = """SELECT CASE
                        WHEN div0(current_date() - BIRTH_DATE, 365) < 49 THEN '34-48'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 49 AND div0(current_date() - BIRTH_DATE, 365) < 65 THEN '49-64'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 65 AND div0(current_date() - BIRTH_DATE, 365) < 79 THEN '65-78'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 79 AND div0(current_date() - BIRTH_DATE, 365) < 99 THEN '79-98'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 99 THEN '99+' END
                AS AGE_GROUP,
                COUNT(*) AS COUNT
                FROM CORE.PATIENT
                GROUP BY 1
                ORDER BY 1;"""

    data = pd.read_csv(s3_uri + "age_data.csv")
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
        ), elig as (
            select
            CONCAT(LEFT(year_month, 4), '-', RIGHT(year_month, 2)) as year_month
           , member_months as member_month_count
            from pmpm.pmpm
        )
        select
            *
        from merged
        join elig using(year_month)
        order by 2, 1
    """

    data = pd.read_csv(s3_uri + "pmpm_by_chronic_condition.csv")
    return data


@st.cache_data
def condition_data():
    query = """SELECT
                CONCAT(date_part(year, FIRST_DIAGNOSIS_DATE), '-', lpad(date_part(month, FIRST_DIAGNOSIS_DATE), 2, 0)) AS DIAGNOSIS_YEAR_MONTH,
                CONDITION,
                COUNT(*) AS CONDITION_CASES,
                AVG(LAST_DIAGNOSIS_DATE + 1 - FIRST_DIAGNOSIS_DATE) AS DIAGNOSIS_DURATION
              FROM CHRONIC_CONDITIONS.TUVA_CHRONIC_CONDITIONS_LONG
              GROUP BY 1,2
              ORDER BY 3 DESC;"""

    data = pd.read_csv(s3_uri + "condition_data.csv")
    data["diagnosis_year"] = pd.to_datetime(
        data["diagnosis_year_month"]
    ).dt.year.astype(str)
    return data

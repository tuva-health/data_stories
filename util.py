import snowflake.connector as sn
import pandas as pd
import tomli

with open(".streamlit/secrets.toml", mode="rb") as fp:
    config = tomli.load(fp)


def connection(database=None):
    return sn.connect(
        user=config["SNOWFLAKE_USER"],
        password=config["SNOWFLAKE_PASSWORD"],
        account=config["SNOWFLAKE_ACCOUNT"],
        warehouse=config["SNOWFLAKE_WH"],
        role=config["SNOWFLAKE_ROLE"],
        database=database or "tuva_project_demo",
    )


def safe_to_pandas(conn, query):
    cur = conn.cursor()
    data = cur.execute(query).fetch_pandas_all()
    cur.close()
    lowercase = lambda x: str(x).lower()
    rename_dict = {k: lowercase(k) for k in data}
    data = data.rename(columns=rename_dict)
    for col in [x for x in data if ("amount" in x) or (x == "member_month_count")]:
        data[col] = pd.to_numeric(data[col])
    return data


def human_format(num):
    num = float("{:.3g}".format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "{}{}".format(
        "{:f}".format(num).rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude]
    )

def format_df(df):
    df = df.copy(deep=True)
    # format column values
    for c in df:
        if 'pct' in c:
            df[c] = df[c].apply(lambda x: f"{round(x, 4) * 100}%" if x else "").replace("nan%", "")
        elif 'pmpm' in c:
            df[c] = df[c].apply(lambda x: f"${human_format(x)}" if x else "").replace("$nan", "")

    # format column headers
    df.columns = [
        c.replace('_', ' ').title()\
        .replace('Pmpm', 'PMPM')\
        .replace("Pct Change", "% Δ") for c in df
    ]
    return df

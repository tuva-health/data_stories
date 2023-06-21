# Data Stories
A [streamlit](https://streamlit.io/) app for designing and creating data stories using data from
[The Tuva Project](https://thetuvaproject.com/)

## Enivronment setup
This repo requires a few python packages to run the streamlit app, connect to S3, etc.
The list of required packages can be found in the `requirements.txt` file in the root of this repo.
Once you are within you desired working python env (or conda, venv), run the following to install the needed libraries

```pip install -r requirements.txt```

## Configuration
Currently, this app uses a `secrets.toml` file  in the `.streamlit/` folder to store secrets and sensitive information needed for runtime. Create a `secrets.toml`
file in the repo `.streamlit/` folder and add the following key/value pairs to the file.
```
SNOWFLAKE_USER = "<username goes here>"
SNOWFLAKE_PASSWORD = "<password goes here>"
SNOWFLAKE_ACCOUNT = "<snowflake account url>"
SNOWFLAKE_WH = "<name of desired warehouse to use>"
SNOWFLAKE_ROLE = "<name of desired role to use>"
```

## App Start Up
Once the python libraries are installed and the `secrets.toml` file has been configured, the streamlit app can be started
by running the following:

```streamlit run financial_summary.py```

The app should launch in a tab in your default internet browser, or can be reached by going to http://localhost:8501

## Pre-Commit
For code contribution, we use [pre-commit](https://pre-commit.com/) and [black](https://pypi.org/project/black/)
for automated code formatting. Before contributing code to the repo, please run the following from the repo root
folder to set up pre-commit to run:

```pre-commit install```

After successful setup, any files with changes that you are trying to commit to your branch will be checked and
reformatted whenever you run `git commit ...`

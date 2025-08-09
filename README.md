# Reserving App

A minimal Streamlit application that performs claims reserving using the
[`chainladder`](https://pypi.org/project/chainladder/) package. The app
can run locally or be deployed to Streamlit Cloud.

## Running locally

1. Install dependencies with [Pipenv](https://pipenv.pypa.io/en/latest/):
   ```bash
   pipenv install
   ```
2. Launch the app inside the virtual environment:
   ```bash
   pipenv run streamlit run app.py
   ```
   The interface will be available in your browser.

## Deploying to Streamlit Cloud

1. Push this repository to a GitHub account.
2. Sign in to [Streamlit Cloud](https://share.streamlit.io) and create a
   new app pointing to the GitHub repository and the `app.py` file.
3. Streamlit Cloud will automatically install dependencies from the
   generated `requirements.txt` and deploy the app.
   If you add or upgrade packages with Pipenv, regenerate this file using:
   ```bash
   pipenv requirements > requirements.txt
   ```

## Using the app

- **Triangle** tab: Upload a CSV cumulative claims triangle or explore the
  built-in CLRD dataset. When using the sample data you can group or filter
  triangles by company or line of business and choose which measure to analyse.
- **LDF/CDF** tab: View loss development factors (LDFs) and cumulative
  development factors (CDFs) alongside ultimate claims and IBNR by origin period.

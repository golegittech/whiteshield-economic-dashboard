import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import polars as pl
from fredapi import Fred
from datetime import datetime, timedelta

app = FastAPI(title="Whiteshield Economic Recovery Dashboard")
templates = Jinja2Templates(directory="templates")

# --- CLOUD SECURITY UPDATE ---
# 1. Try to find the key in the Cloud Environment Variables (for Render)
api_key = os.getenv("FRED_API_KEY")

# 2. If not found in the cloud, fall back to your local text file (for your laptop)
if not api_key:
    try:
        with open('api_key.txt', 'r', encoding='utf-8') as f:
            api_key = f.read().strip().replace('"', '').replace("'", "")
    except FileNotFoundError:
        print("WARNING: API Key not found!")

# Initialize FRED securely
fred = Fred(api_key=api_key)
# -----------------------------

def get_recovery_data():
    """Fetches both Monthly Macro Data and Daily Market Data."""
    
    # --- 1. MONTHLY DATA (Recovery Index & Inflation) ---
    indicators = {
        "CPIAUCSL": "CPI_Inflation",
        "RSAFS": "Retail_Sales",
        "UNRATE": "Unemployment_Rate",
        "FEDFUNDS": "Fed_Rate",       # NEW: The Medicine
        "MORTGAGE30US": "Mortgage_Rate"
    }

    start_date_monthly = datetime.now() - timedelta(days=6*365)
    dfs = []
    
    for series_id, name in indicators.items():
        data = fred.get_series(series_id, observation_start=start_date_monthly)
        df = pl.DataFrame({"date": data.index.to_list(), name: data.values.tolist()}).drop_nulls()
        df = df.with_columns(pl.col("date").cast(pl.Date))
        dfs.append(df)

    combined_df = dfs[0]
    for df in dfs[1:]:
        combined_df = combined_df.join(df, on="date", how="full", coalesce=True)

    combined_df = combined_df.with_columns([
        pl.col("CPI_Inflation").cast(pl.Float64).fill_nan(None),
        pl.col("Retail_Sales").cast(pl.Float64).fill_nan(None),
        pl.col("Unemployment_Rate").cast(pl.Float64).fill_nan(None),
        pl.col("Fed_Rate").cast(pl.Float64).fill_nan(None),      # NEW
        pl.col("Mortgage_Rate").cast(pl.Float64).fill_nan(None)
    ])
    combined_df = combined_df.sort("date").fill_null(strategy="forward").fill_null(strategy="backward")
    
    combined_df = combined_df.with_columns(
        (((pl.col("CPI_Inflation") - pl.col("CPI_Inflation").shift(12)) / pl.col("CPI_Inflation").shift(12)) * 100).alias("YoY_Inflation")
    )
    combined_df = combined_df.drop_nulls(subset=["YoY_Inflation"])

    cpi_mean, cpi_std = combined_df["CPI_Inflation"].mean(), combined_df["CPI_Inflation"].std()
    retail_mean, retail_std = combined_df["Retail_Sales"].mean(), combined_df["Retail_Sales"].std()
    unemp_mean, unemp_std = combined_df["Unemployment_Rate"].mean(), combined_df["Unemployment_Rate"].std()

    combined_df = combined_df.with_columns([
        (((pl.col("CPI_Inflation") - cpi_mean) / cpi_std) * -1).alias("z_CPI"),
        ((pl.col("Retail_Sales") - retail_mean) / retail_std).alias("z_Retail"),
        (((pl.col("Unemployment_Rate") - unemp_mean) / unemp_std) * -1).alias("z_Unemp")
    ])

    combined_df = combined_df.with_columns(
        ((pl.col("z_CPI") + pl.col("z_Retail") + pl.col("z_Unemp")) / 3).alias("Composite_Z")
    )

    min_z, max_z = combined_df["Composite_Z"].min(), combined_df["Composite_Z"].max()
    combined_df = combined_df.with_columns(
        (((pl.col("Composite_Z") - min_z) / (max_z - min_z)) * 100).alias("Recovery_Index_0_to_100")
    )
    
    # --- 2. DAILY DATA (S&P 500) ---
    start_date_daily = datetime.now() - timedelta(days=5*365)
    sp500_data = fred.get_series("SP500", observation_start=start_date_daily)
    
    sp500_df = pl.DataFrame({
        "date": sp500_data.index.to_list(),
        "SP500": sp500_data.values.tolist()
    })
    
    sp500_df = sp500_df.with_columns([
        pl.col("date").cast(pl.Date),
        pl.col("SP500").cast(pl.Float64, strict=False).fill_nan(None)
    ]).drop_nulls()

    # --- 3. PACKAGE EVERYTHING FOR THE FRONTEND ---
    return {
        "dates": combined_df["date"].dt.to_string("%Y-%m-%d").to_list(),
        "scores": combined_df["Recovery_Index_0_to_100"].round(2).to_list(),
        "inflation": combined_df["YoY_Inflation"].round(2).to_list(),
        "fed_rate": combined_df["Fed_Rate"].round(2).to_list(),           # NEW
        "mortgage_rate": combined_df["Mortgage_Rate"].round(2).to_list(), # NEW
        "daily_dates": sp500_df["date"].dt.to_string("%Y-%m-%d").to_list(),
        "daily_values": sp500_df["SP500"].round(2).to_list()
    }

@app.get("/api/data")
def api_data():
    return get_recovery_data()

@app.get("/", response_class=HTMLResponse)
def serve_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
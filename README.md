# Whiteshield Economic Recovery Dashboard

## Executive Summary

This project is a full-stack, data-driven web application designed to track and visualize the macroeconomic recovery of the United States. It ingests live data from the Federal Reserve Economic Data (FRED) API, processes it using high-performance dataframe operations, and serves it through a highly responsive FastAPI backend to an interactive frontend dashboard.

## Features & Visualizations

The dashboard is separated into distinct analytical lenses to provide a holistic view of the economy:

- Composite Recovery Index (Monthly Macro Pulse): A custom 0-100 normalized index aggregating Unemployment (labor stress), Retail Sales (consumer demand), and CPI (price stability).
- The Transmission Mechanism (Cause & Effect): A multi-metric visualization overlaying YoY Inflation, the Federal Funds Rate, and 30-Year Mortgage Rates to map the real-world impact of central bank monetary policy on the housing market and consumer prices.
- Year-over-Year (YoY) Inflation Rate: Isolates the 12-month rolling percentage change in the Consumer Price Index to track the velocity of inflation.
- Daily Market Sentiment: Tracks the daily closing values of the S&P 500 to contrast lagging macroeconomic data with real-time, forward-looking investor sentiment.
- Interactive Data Explorer: A client-side, zero-latency raw data table allowing stakeholders to dynamically filter historical metrics by year without requiring additional server queries.

## Methodology 

### 1. The Z-Score Normalization
To combine fundamentally different metrics (percentages, millions of dollars, and index values) into a single Composite Recovery Index, the application calculates a Z-Score for each metric over a rolling window. Metrics where "higher is bad" (Unemployment, Inflation) are mathematically inverted. The combined Z-scores are averaged and scaled to a 0-100 range for immediate executive readability.

### 2. The Transmission Mechanism of Monetary Policy
By including the Federal Funds Rate and 30-Year Mortgage Rates, the dashboard closes the analytical loop. It visualizes the cause-and-effect chain reaction: how central bank policy (raising rates) makes borrowing expensive (mortgages spike), which deliberately cools consumer demand and the housing market to ultimately bring down YoY Inflation.

### 3. Metric Selection & Avoiding Multicollinearity
The dashboard intentionally limits its core monthly index to three pillars (Jobs, Spending, Prices). This avoids multicollinearity (double-counting identical economic symptoms) and ensures the final index remains instantly explainable to non-technical stakeholders without becoming a "black box." Quarterly metrics like GDP were excluded to ensure the dashboard remains highly responsive to monthly shifts.

### 4. Leading vs. Lagging Indicators
The dashboard intentionally pairs lagging/coincident indicators (Unemployment, Retail Sales) with a leading indicator (The S&P 500). By plotting them together, stakeholders can visualize how cooling inflation and shifting interest rates act as a catalyst for future market growth.

## Technical Stack 

- Backend Framework: FastAPI & Uvicorn for asynchronous, high-speed API routing and server rendering.
- Data Engineering: Polars. Chosen over Pandas for its superior performance and strict typing. Complex edge cases, such as the "Jagged Edge" reporting lag and hidden floating-point `NaN` values from the FRED Pandas-based API, were explicitly sanitized into Polars `Null` types to ensure flawless chronological forward/backward filling.
- Data Source: `fredapi` pulling directly from the St. Louis Fed.
- Frontend: Vanilla HTML/JS with Plotly.js for lightweight, interactive, and mobile-responsive charting.


## Local Setup & Installation

Prerequisites

Ensure you have Python installed along with the required packages:

pip install fastapi uvicorn polars fredapi pandas plotly jinja2


API Key Configuration

This application requires a free FRED API key.

Create a file named api_key.txt in the root directory.

Paste your 32-character API key on the first line (no quotation marks). The backend will automatically sanitize the string upon boot.

Running the Server

To launch the dashboard locally with hot-reloading:

python -m uvicorn main:app --reload


Navigate to http://127.0.0.1:8000 in your browser.


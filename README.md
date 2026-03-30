# Benjamin Graham Stock Valuation GUI

A Python desktop application built with PyQt6 that evaluates stocks using Benjamin Graham's timeless value investing methodologies. It fetches live market data, historical prices, and fundamental metrics to recommend whether a stock is a **BUY**, **HOLD**, or **SELL** based on a combination of Graham's strict criteria, the Graham Number, and his Revised Intrinsic Value formula.

## Features

*   **Live Data Fetching:** Uses `yfinance` to retrieve real-time stock prices, P/E, P/B, EPS, Book Value, earnings growth, and balance sheet data.
*   **Dual Valuation Models:**
    *   **Graham Number (Deep Value):** Calculates the classic defensive intrinsic value: `Sqrt(22.5 * EPS * BVPS)`.
    *   **Intrinsic Value (Growth):** Calculates value using Graham's revised formula for growth stocks: `Value = EPS * (8.5 + 2g)`.
*   **Checklist Scoring:** Scores the stock against Graham's strict **Defensive** criteria and relaxed **Enterprising** criteria.
*   **Interactive Charting:** Embeds a live `matplotlib` chart to visualize price history across multiple timeframes (1D, 1W, 1M, 3M, 1Y, 5Y, MAX) against the calculated Graham Number and Intrinsic Value.
*   **Dual Recommendation Engine:** Presents separated Buy/Hold/Sell recommendations based independently on the Graham Method and the Growth Intrinsic Value method via intuitive tabs.
*   **Modern UI:** Features a clean, Wealthsimple-inspired light theme with pill-shaped buttons, separated data cards, and crisp typography.
*   **Asynchronous Processing:** Data fetching and chart rendering run in background threads, keeping the GUI fast and responsive.

## Prerequisites

*   Python 3.8 or higher
*   Windows (or Linux/macOS with appropriate virtual environment adjustments)

## Installation & Running (The Easy Way)

If you are on Windows, simply double-click the **`setup_and_run.bat`** file. 
This script will automatically:
1. Check for Python
2. Create a virtual environment (`venv`)
3. Install all required dependencies
4. Launch the application

## Manual Installation

If you prefer to set it up manually or are on macOS/Linux:

1.  **Navigate to the project directory:**
    ```powershell
    cd C:\Users\ppab8\graham_stock_gui
    ```

2.  **Create a virtual environment:**
    ```powershell
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
    *   **Windows (Command Prompt):** `.\venv\Scripts\activate.bat`
    *   **Linux/macOS:** `source venv/bin/activate`

4.  **Install the required dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```

5.  **Run the application:**
    ```powershell
    python main_window.py
    ```

---

## Methodology & Analysis

This application utilizes a multi-layered approach inspired by Benjamin Graham's book, *The Intelligent Investor*. It caters to both conservative investors seeking deep value and modern investors looking for growth at a reasonable price.

### 1. The Graham Number (Deep Value)
The classic formula used to establish an absolute upper limit on how much a defensive investor should pay for a stock.
*   **Formula:** `Sqrt(22.5 * EPS * BVPS)`
*   **Rationale:** Assumes a maximum P/E ratio of 15 and a maximum P/B ratio of 1.5 (15 * 1.5 = 22.5). This metric is heavily biased towards asset-heavy, traditional companies.

### 2. Intrinsic Value (Revised Formula for Growth)
Later in his life, Graham provided a formula to evaluate growth stocks, acknowledging that earnings growth has tangible value.
*   **Formula:** `Value = EPS * (8.5 + 2g)`
*   *Note: This app caps the growth rate (g) at a conservative 15% to prevent hyper-growth anomalies from outputting unrealistic valuations. Base P/E for a no-growth company is set to 8.5.*

### 3. Defensive Criteria (Strict Checklist)
Designed for the passive investor who wants minimal risk. To pass, a stock must be a massive, financially impenetrable fortress.
*   **Adequate Size:** Minimum revenue (adjusted loosely for modern inflation to $2B+).
*   **Strong Financial Condition:** Current Ratio >= 2.0 (Assets are double liabilities).
*   **Earnings Stability:** Positive earnings in all available recent years.
*   **Dividend Record:** Uninterrupted dividend payments.
*   **Valuation Limits:** P/E < 15 and P/B < 1.5.

### 4. Enterprising Criteria (Relaxed Checklist)
Designed for the active investor willing to take on slightly more risk for better returns.
*   **Financial Condition:** Current Ratio >= 1.5, and Total Debt is less than Net Current Assets.
*   **Earnings Stability:** Positive earnings history.
*   **Dividend Record:** Currently pays a dividend (no strict historical requirement).
*   **Earnings Growth:** Current EPS must simply be positive.

### Recommendation Engine (Buy/Hold/Sell Logic)
The final recommendation synthesizes the quantitative values and the qualitative checklists:
*   **BUY:** 
    *   The stock passes the strict **Defensive Checklist** AND trades below the Graham Number.
    *   *OR* The stock is trading at a massive discount (deep value) > 33% below the Graham Number.
    *   *OR* The stock passes the **Enterprising Checklist** AND is trading below its calculated Intrinsic Value (identifying good growth stocks at fair prices).
*   **HOLD:** 
    *   The stock passes the **Enterprising Checklist** and trades below the Graham Number, but fails the strict Defensive checks.
    *   *OR* The stock is trading just slightly above the Graham Number (within 10%) or below its Intrinsic Value.
*   **SELL:** 
    *   The stock is significantly overvalued compared to both the Graham Number and its Intrinsic Value, and fails fundamental safety checks.

## Disclaimer

This software is for educational and informational purposes only and does not constitute financial advice. Data is sourced from Yahoo Finance and may occasionally be delayed, inaccurate, or missing fundamental values. Always do your own research before making investment decisions.

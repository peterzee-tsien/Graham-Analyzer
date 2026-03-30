import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class DataFetcher:
    """Fetches market data and fundamental metrics using yfinance."""

    @staticmethod
    def get_history(ticker_symbol: str, period: str = "1y"):
        """Fetches historical price data with appropriate intervals for the period."""
        try:
            ticker = yf.Ticker(ticker_symbol)
            intervals = {
                '1d': '5m',
                '5d': '15m',
                '1mo': '1d',
                '3mo': '1d',
                '1y': '1d',
                '5y': '1wk',
                'max': '1mo'
            }
            interval = intervals.get(period, '1d')
            return ticker.history(period=period, interval=interval)
        except Exception as e:
            print(f"Error fetching history: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stock_data(ticker_symbol: str, period: str = "1y"):
        """Fetches basic info, historical data, and fundamental metrics for a ticker."""
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            if not info or 'shortName' not in info:
                return None, "Invalid Ticker or No Data Found"

            # 1. Basic Info
            basic_info = {
                "name": info.get("shortName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "market_cap": info.get("marketCap", 0),
                "revenue": info.get("totalRevenue", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "dividend_yield": info.get("dividendYield", 0),
            }

            # 2. Fundamental Data for Graham Formulas
            fundamentals = {
                "eps_ttm": info.get("trailingEps", 0),
                "book_value_per_share": info.get("bookValue", 0),
                "current_ratio": info.get("currentRatio", 0),
                "total_debt": info.get("totalDebt", 0),
                "total_cash": info.get("totalCash", 0),
                "free_cashflow": info.get("freeCashflow", 0),
                "earnings_growth": info.get("earningsGrowth", 0), # Usually a decimal like 0.15
            }

            # Calculate Net Current Assets roughly if not directly available
            try:
                balance_sheet = ticker.balance_sheet
                if not balance_sheet.empty:
                    latest_bs = balance_sheet.iloc[:, 0]
                    fundamentals["current_assets"] = latest_bs.get("Current Assets", 0)
                    fundamentals["current_liabilities"] = latest_bs.get("Current Liabilities", 0)
                    fundamentals["total_liabilities"] = latest_bs.get("Total Liabilities Net Minority Interest", 0)
                    
                    if pd.isna(fundamentals["current_assets"]): fundamentals["current_assets"] = 0
                    if pd.isna(fundamentals["current_liabilities"]): fundamentals["current_liabilities"] = 0
                    if pd.isna(fundamentals["total_liabilities"]): fundamentals["total_liabilities"] = 0
                    
                    if fundamentals["current_ratio"] == 0 and fundamentals["current_liabilities"] > 0:
                        fundamentals["current_ratio"] = fundamentals["current_assets"] / fundamentals["current_liabilities"]
            except Exception as e:
                print(f"Error fetching balance sheet: {e}")
                fundamentals["current_assets"] = 0
                fundamentals["current_liabilities"] = 0
                fundamentals["total_liabilities"] = 0

            # 3. Earnings Stability
            try:
                income_stmt = ticker.financials
                if not income_stmt.empty:
                    net_income = income_stmt.loc["Net Income"] if "Net Income" in income_stmt.index else []
                    fundamentals["earnings_history"] = net_income.tolist() if not net_income.empty else []
                    fundamentals["all_earnings_positive"] = all(val > 0 for val in fundamentals["earnings_history"] if pd.notna(val))
                else:
                    fundamentals["earnings_history"] = []
                    fundamentals["all_earnings_positive"] = False
            except Exception:
                fundamentals["earnings_history"] = []
                fundamentals["all_earnings_positive"] = False

            # 4. Dividend Record
            try:
                dividends = ticker.dividends
                if not dividends.empty:
                    ten_years_ago = pd.Timestamp.now(tz=dividends.index.tz) - pd.DateOffset(years=10)
                    recent_dividends = dividends[dividends.index > ten_years_ago]
                    years_paid = len(recent_dividends.groupby(recent_dividends.index.year))
                    fundamentals["continuous_dividend_10yr"] = years_paid >= 8
                else:
                    fundamentals["continuous_dividend_10yr"] = False
            except Exception:
                fundamentals["continuous_dividend_10yr"] = False

            # 5. Historical Price Data for Charting
            history = DataFetcher.get_history(ticker_symbol, period)

            return {
                "basic_info": basic_info,
                "fundamentals": fundamentals,
                "history": history
            }, None

        except Exception as e:
            return None, f"Error fetching data: {str(e)}"

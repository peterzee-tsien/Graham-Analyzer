import math

class GrahamValuation:
    """Evaluates a stock based on Benjamin Graham's value investing criteria."""

    @staticmethod
    def calculate_graham_number(eps: float, bvps: float) -> float:
        """Calculates the Graham Number. Requires positive EPS and BVPS."""
        if eps is None or bvps is None or eps <= 0 or bvps <= 0:
            return 0.0
        # Graham Number = sqrt(22.5 * EPS * BVPS)
        # 22.5 comes from max P/E of 15 and max P/B of 1.5 (15 * 1.5 = 22.5)
        try:
            return math.sqrt(22.5 * eps * bvps)
        except ValueError:
            return 0.0

    @staticmethod
    def calculate_intrinsic_value(eps: float, growth_rate_decimal: float) -> float:
        """
        Calculates Graham's Revised Intrinsic Value formula.
        V = EPS * (8.5 + 2 * g) * 4.4 / Y
        Assuming Y (current corporate bond yield) is approximately 4.4% for simplicity,
        the formula simplifies to: V = EPS * (8.5 + 2 * g)
        """
        if eps is None or eps <= 0:
            return 0.0
            
        # Default growth rate to a conservative 3% if not available or negative
        if growth_rate_decimal is None or growth_rate_decimal < 0:
            g = 3.0
        else:
            g = growth_rate_decimal * 100 # Convert to percentage (e.g., 0.15 -> 15)
            
        # Cap excessive growth rates at 15% to remain conservative
        g = min(g, 15.0)

        # Base P/E for no-growth company is 8.5
        return eps * (8.5 + 2 * g)

    @staticmethod
    def evaluate(stock_data: dict) -> dict:
        """
        Evaluates the stock based on Defensive and Enterprising criteria.
        Returns a dictionary with results and a recommendation.
        """
        info = stock_data["basic_info"]
        fund = stock_data["fundamentals"]

        current_price = info.get("current_price", 0)
        market_cap = info.get("market_cap", 0)
        revenue = info.get("revenue", 0)
        pe_ratio = info.get("pe_ratio", 0)
        pb_ratio = info.get("pb_ratio", 0)

        eps = fund.get("eps_ttm", 0)
        bvps = fund.get("book_value_per_share", 0)
        current_ratio = fund.get("current_ratio", 0)
        continuous_dividend = fund.get("continuous_dividend_10yr", False)
        all_earnings_positive = fund.get("all_earnings_positive", False)
        total_debt = fund.get("total_debt", 0)
        current_assets = fund.get("current_assets", 0)
        total_liabilities = fund.get("total_liabilities", 0)
        growth_rate = fund.get("earnings_growth", 0)

        graham_number = GrahamValuation.calculate_graham_number(eps, bvps)
        intrinsic_value = GrahamValuation.calculate_intrinsic_value(eps, growth_rate)

        # ---------------------------------------------------------
        # Defensive Criteria Evaluation
        # ---------------------------------------------------------
        defensive = {
            "adequate_size": revenue > 2_000_000_000, # At least $2B in sales (adjusted for modern inflation loosely)
            "strong_financial_condition": current_ratio >= 2.0,
            "earnings_stability": all_earnings_positive, # Should ideally be 10 years, but we check available
            "dividend_record": continuous_dividend,
            "moderate_pe": 0 < pe_ratio <= 15,
            "moderate_pb": 0 < pb_ratio <= 1.5 or (pe_ratio * pb_ratio <= 22.5 if pe_ratio > 0 and pb_ratio > 0 else False)
        }
        
        # Calculate defensive score
        defensive_score = sum(defensive.values())
        defensive_passed = defensive_score >= len(defensive)

        # ---------------------------------------------------------
        # Enterprising Criteria Evaluation
        # ---------------------------------------------------------
        # Less strict than defensive
        
        # Net current assets (NCAV)
        ncav = current_assets - total_liabilities
        
        enterprising = {
            "financial_condition_ratio": current_ratio >= 1.5,
            "financial_condition_debt": total_debt < ncav if ncav > 0 else False,
            "earnings_stability": all_earnings_positive, # At least 5 years positive (reusing the flag)
            "dividend_record": info.get("dividend_yield", 0) > 0, # Current dividend being paid
            "earnings_growth": eps > 0, # Current earnings must be positive
        }

        enterprising_score = sum(enterprising.values())
        enterprising_passed = enterprising_score >= len(enterprising)

        # ---------------------------------------------------------
        # Recommendation Logic
        # ---------------------------------------------------------
        graham_recommendation = "SELL"
        intrinsic_recommendation = "SELL"
        
        margin_of_safety = 0.0
        intrinsic_margin = 0.0

        if graham_number > 0 and current_price > 0:
            margin_of_safety = (graham_number - current_price) / graham_number
            
        if intrinsic_value > 0 and current_price > 0:
            intrinsic_margin = (intrinsic_value - current_price) / intrinsic_value

        # 1. Graham Number Recommendation Logic (Traditional Deep Value)
        is_undervalued_graham = current_price < graham_number
        is_deep_value = current_price < graham_number * 0.66

        if (defensive_passed and is_undervalued_graham) or is_deep_value:
            graham_recommendation = "BUY"
        elif enterprising_passed and is_undervalued_graham:
            graham_recommendation = "HOLD"
        elif current_price <= graham_number * 1.1: 
            graham_recommendation = "HOLD"
            
        # 2. Intrinsic Value Recommendation Logic (Growth Adjusted)
        is_undervalued_intrinsic = current_price < intrinsic_value
        
        if is_undervalued_intrinsic and enterprising_passed and intrinsic_margin >= 0.20:
            # Undervalued, passes basic safety checks, and has at least a 20% margin of safety
            intrinsic_recommendation = "BUY"
        elif is_undervalued_intrinsic:
            intrinsic_recommendation = "HOLD"
        elif current_price <= intrinsic_value * 1.1:
            # Just slightly over intrinsic value
            intrinsic_recommendation = "HOLD"

        return {
            "graham_number": graham_number,
            "intrinsic_value": intrinsic_value,
            "margin_of_safety": margin_of_safety,
            "intrinsic_margin": intrinsic_margin,
            "defensive_criteria": defensive,
            "defensive_score": defensive_score,
            "defensive_passed": defensive_passed,
            "enterprising_criteria": enterprising,
            "enterprising_score": enterprising_score,
            "enterprising_passed": enterprising_passed,
            "graham_recommendation": graham_recommendation,
            "intrinsic_recommendation": intrinsic_recommendation
        }

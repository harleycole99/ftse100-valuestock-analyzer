"""
Warren Buffett Value Investing Analyzer Module
Calculates quantitative metrics, economic moat indicators, intrinsic value via Discounted Cash Flow (DCF),
and composite Buffett Value Scores (0-100) with Buy/Hold/Sell indicators for FTSE 100 stocks.
"""

import math
from typing import Dict, Any, Tuple


class BuffettAnalyzer:
    """
    Implements Warren Buffett's investment evaluation framework:
    1. Moat & Business Quality (ROE, Net Margin, Gross Margin)
    2. Financial Strength (Debt-to-Equity, Cash Flow coverage, Current Ratio)
    3. Value & Multiples (P/E, P/B, PEG, FCF Yield)
    4. Intrinsic Value & Margin of Safety (DCF model)
    """

    def __init__(self, discount_rate: float = 0.09, perpetual_growth: float = 0.025):
        self.discount_rate = discount_rate  # 9% discount rate (typical hurdle rate for value investors)
        self.perpetual_growth = perpetual_growth  # 2.5% terminal growth rate (inflation/GDP rate)

    def normalize_price_and_currency(self, info: Dict[str, Any]) -> Tuple[float, float, str]:
        """
        Extracts current price, market cap, and normalizes GBp (pence) to GBP (£).
        LSE stocks on yfinance are often quoted in GBp (pence).
        Returns (price_gbp, market_cap_gbp, currency_symbol).
        """
        raw_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
        market_cap = info.get('marketCap') or 0.0
        currency = info.get('currency', 'GBp')

        # Check if price is in pence (GBp or GBP with price > 100 for UK stock)
        # Most FTSE 100 stocks are quoted in GBp (pence), e.g. 2500p = £25.00
        if currency.lower() in ['gbp', 'gbp', 'pence'] or (isinstance(raw_price, (int, float)) and raw_price > 100 and market_cap > 1e8):
            # If price is clearly in GBp (e.g. 2450p) but market cap is in GBP (e.g. £50B), adjust price
            # Let's verify ratio: MarketCap / (Shares * Price)
            shares = info.get('sharesOutstanding') or 0
            if shares > 0 and raw_price > 0:
                implied_cap = shares * raw_price
                if implied_cap > market_cap * 50:  # Implied cap is ~100x market cap -> price is in pence
                    price_gbp = raw_price / 100.0
                    return price_gbp, market_cap, '£'

        price_gbp = raw_price
        return price_gbp, market_cap, '£'

    def calculate_dcf_intrinsic_value(
        self,
        fcf: float,
        shares_outstanding: float,
        price_gbp: float,
        earnings_growth: float = 0.05
    ) -> Tuple[float, float]:
        """
        Discounted Cash Flow (DCF) Valuation Model based on Free Cash Flow / Owner Earnings.
        - Projects FCF for 10 years at estimated growth rate.
        - Calculates Terminal Value using Perpetual Growth formula.
        - Discounts all future cash flows back to present value.
        Returns (intrinsic_value_per_share, margin_of_safety_percent).
        """
        if not fcf or fcf <= 0 or not shares_outstanding or shares_outstanding <= 0 or price_gbp <= 0:
            return 0.0, -100.0

        fcf_per_share = fcf / shares_outstanding

        # Cap growth rate conservatively between 2% and 10%
        g = max(0.02, min(0.10, earnings_growth if earnings_growth else 0.05))
        r = self.discount_rate
        g_term = self.perpetual_growth

        pv_fcf = 0.0
        current_fcf_ps = fcf_per_share

        # 10-Year DCF Projection
        for year in range(1, 11):
            current_fcf_ps *= (1 + g)
            pv_fcf += current_fcf_ps / ((1 + r) ** year)

        # Terminal Value
        terminal_value = (current_fcf_ps * (1 + g_term)) / (r - g_term)
        pv_terminal_value = terminal_value / ((1 + r) ** 10)

        intrinsic_value = pv_fcf + pv_terminal_value

        # Calculate Margin of Safety %
        margin_of_safety = ((intrinsic_value - price_gbp) / intrinsic_value) * 100.0 if intrinsic_value > 0 else -100.0

        return round(intrinsic_value, 2), round(margin_of_safety, 1)

    def analyze_ticker(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses raw yfinance info dict and evaluates Warren Buffett metrics & recommendation signals.
        """
        ticker = info.get('symbol', 'UNKNOWN')
        name = info.get('shortName') or info.get('longName') or ticker
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')

        price_gbp, market_cap_gbp, currency = self.normalize_price_and_currency(info)
        shares_outstanding = info.get('sharesOutstanding') or (market_cap_gbp / price_gbp if price_gbp > 0 else 0)

        # Extract Raw Metrics
        pe_ratio = info.get('trailingPE') or info.get('forwardPE')
        pb_ratio = info.get('priceToBook')
        peg_ratio = info.get('pegRatio')
        roe = info.get('returnOnEquity')  # e.g., 0.18 = 18%
        roa = info.get('returnOnAssets')
        gross_margin = info.get('grossMargins')
        net_margin = info.get('profitMargins')
        op_margin = info.get('operatingMargins')
        debt_to_equity = info.get('debtToEquity')  # yfinance gives percentage (e.g. 45.2 = 0.452 or raw)
        
        # Normalize debtToEquity if in percentage format (e.g. 50 = 0.5)
        if debt_to_equity is not None and debt_to_equity > 5.0:
            debt_to_equity = debt_to_equity / 100.0

        current_ratio = info.get('currentRatio')
        quick_ratio = info.get('quickRatio')
        fcf = info.get('freeCashflow') or info.get('operatingCashflow')
        fcf_yield = (fcf / market_cap_gbp) if (fcf and market_cap_gbp > 0) else None
        
        dividend_yield = info.get('dividendYield')  # e.g. 0.042 = 4.2% or 4.2
        if dividend_yield is not None and dividend_yield > 0.5:
            dividend_yield = dividend_yield / 100.0

        payout_ratio = info.get('payoutRatio')
        earnings_growth = info.get('earningsGrowth') or info.get('revenueGrowth') or 0.05

        # --- Calculate Intrinsic Value via DCF ---
        intrinsic_value, margin_of_safety = self.calculate_dcf_intrinsic_value(
            fcf=fcf or 0,
            shares_outstanding=shares_outstanding,
            price_gbp=price_gbp,
            earnings_growth=earnings_growth
        )

        # --- Component Scoring (25 pts each = 100 max) ---

        # 1. Quality & Economic Moat Sub-Score (Max 25 pts)
        quality_score = 0.0
        if roe is not None:
            if roe >= 0.20: quality_score += 10
            elif roe >= 0.15: quality_score += 8
            elif roe >= 0.10: quality_score += 5
            elif roe > 0: quality_score += 2

        if net_margin is not None:
            if net_margin >= 0.15: quality_score += 8
            elif net_margin >= 0.10: quality_score += 6
            elif net_margin >= 0.05: quality_score += 3

        if op_margin is not None or gross_margin is not None:
            margin = op_margin or gross_margin
            if margin >= 0.20: quality_score += 7
            elif margin >= 0.10: quality_score += 4
            elif margin > 0: quality_score += 2

        # 2. Financial Strength & Debt Safety Sub-Score (Max 25 pts)
        health_score = 0.0
        if debt_to_equity is not None:
            if debt_to_equity <= 0.3: health_score += 12
            elif debt_to_equity <= 0.6: health_score += 9
            elif debt_to_equity <= 1.0: health_score += 5
            elif debt_to_equity <= 1.5: health_score += 2
        else:
            health_score += 6  # Neutral baseline if missing

        if current_ratio is not None:
            if current_ratio >= 1.5: health_score += 8
            elif current_ratio >= 1.0: health_score += 5
            elif current_ratio >= 0.8: health_score += 2

        if fcf and fcf > 0:
            health_score += 5

        # 3. Valuation Multiples Sub-Score (Max 25 pts)
        val_score = 0.0
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio <= 12: val_score += 10
            elif pe_ratio <= 16: val_score += 8
            elif pe_ratio <= 20: val_score += 5
            elif pe_ratio <= 25: val_score += 2

        if pb_ratio is not None and pb_ratio > 0:
            if pb_ratio <= 1.5: val_score += 6
            elif pb_ratio <= 2.5: val_score += 4
            elif pb_ratio <= 4.0: val_score += 2

        if fcf_yield is not None and fcf_yield > 0:
            if fcf_yield >= 0.08: val_score += 9
            elif fcf_yield >= 0.05: val_score += 6
            elif fcf_yield >= 0.03: val_score += 3
        elif peg_ratio is not None and 0 < peg_ratio <= 1.5:
            val_score += 5

        # 4. Intrinsic Value & Margin of Safety Sub-Score (Max 25 pts)
        mos_score = 0.0
        if margin_of_safety >= 30: mos_score = 25
        elif margin_of_safety >= 20: mos_score = 20
        elif margin_of_safety >= 10: mos_score = 15
        elif margin_of_safety >= 0: mos_score = 10
        elif margin_of_safety >= -15: mos_score = 5
        else: mos_score = 0

        # Total Composite Buffett Score (0 to 100)
        buffett_score = round(quality_score + health_score + val_score + mos_score, 1)

        # --- Signal Determination Matrix ---
        if buffett_score >= 75 and margin_of_safety >= 15 and (debt_to_equity is None or debt_to_equity <= 0.8):
            signal = 'STRONG BUY'
        elif buffett_score >= 62 and margin_of_safety >= 0:
            signal = 'BUY'
        elif buffett_score >= 48 or (-10 <= margin_of_safety < 0 and buffett_score >= 55):
            signal = 'HOLD'
        else:
            signal = 'SELL'

        # Force SELL signal if severe fundamental red flags
        if (debt_to_equity and debt_to_equity > 3.0) or (payout_ratio and payout_ratio > 1.3) or (pe_ratio and pe_ratio > 50):
            signal = 'SELL'

        return {
            'Ticker': ticker,
            'Name': name,
            'Sector': sector,
            'Industry': industry,
            'Price (£)': round(price_gbp, 2),
            'Market Cap (£B)': round(market_cap_gbp / 1e9, 2) if market_cap_gbp else None,
            'Buffett Score': buffett_score,
            'Signal': signal,
            'Intrinsic Value (£)': intrinsic_value,
            'Margin of Safety (%)': margin_of_safety,
            'P/E Ratio': round(pe_ratio, 2) if pe_ratio else None,
            'P/B Ratio': round(pb_ratio, 2) if pb_ratio else None,
            'PEG Ratio': round(peg_ratio, 2) if peg_ratio else None,
            'ROE (%)': round(roe * 100, 2) if roe is not None else None,
            'Net Margin (%)': round(net_margin * 100, 2) if net_margin is not None else None,
            'Op Margin (%)': round(op_margin * 100, 2) if op_margin is not None else None,
            'Debt/Equity': round(debt_to_equity, 2) if debt_to_equity is not None else None,
            'Current Ratio': round(current_ratio, 2) if current_ratio is not None else None,
            'FCF Yield (%)': round(fcf_yield * 100, 2) if fcf_yield is not None else None,
            'Dividend Yield (%)': round(dividend_yield * 100, 2) if dividend_yield is not None else None,
            'Payout Ratio (%)': round(payout_ratio * 100, 2) if payout_ratio is not None else None,
            'Subscore Quality': round(quality_score, 1),
            'Subscore Health': round(health_score, 1),
            'Subscore Valuation': round(val_score, 1),
            'Subscore MOS': round(mos_score, 1)
        }


"""
ETF and Investment Vehicles Analyzer Module
Evaluates key FTSE 100 index ETFs, UK Value Factor ETFs, and Dividend Investment Trusts
to establish opportunity cost benchmarks for Warren Buffett value investing.
"""

from typing import Dict, Any, List


class ETFAnalyzer:
    """
    Analyzes leading ETFs and Investment Trusts relevant to FTSE 100 & Value Investors:
    - Index Benchmarks (ISF.L, VUKE.L)
    - Mid-Cap Value (VMID.L)
    - High Dividend / Value Factor (IUKD.L, IWVL.L)
    - Dividend Investment Trusts (CTY.L, FCIT.L, SMT.L)
    """

    ETF_METADATA = {
        'ISF.L': {
            'Name': 'iShares Core FTSE 100 UCITS ETF',
            'Category': 'FTSE 100 Index Benchmark',
            'Expense Ratio (%)': 0.07,
            'Description': 'Direct low-cost physical index tracking of top 100 UK blue chips.'
        },
        'VUKE.L': {
            'Name': 'Vanguard FTSE 100 UCITS ETF',
            'Category': 'FTSE 100 Index Benchmark',
            'Expense Ratio (%)': 0.09,
            'Description': 'Vanguard standard UK blue-chip index tracker.'
        },
        'VMID.L': {
            'Name': 'Vanguard FTSE 250 UCITS ETF',
            'Category': 'UK Mid-Cap Benchmark',
            'Expense Ratio (%)': 0.10,
            'Description': 'Tracks FTSE 250 mid-caps with strong UK domestic exposure.'
        },
        'IUKD.L': {
            'Name': 'iShares UK Dividend UCITS ETF',
            'Category': 'UK High Dividend / Value',
            'Expense Ratio (%)': 0.40,
            'Description': 'Selects the top 50 highest dividend-yielding stocks in the UK FTSE 350.'
        },
        'IWVL.L': {
            'Name': 'iShares Edge MSCI World Value Factor ETF',
            'Category': 'Global Value Factor',
            'Expense Ratio (%)': 0.30,
            'Description': 'Global equities screened for high value metrics (low P/E, P/B, FCF).'
        },
        'CTY.L': {
            'Name': 'City of London Investment Trust',
            'Category': 'Dividend Hero Investment Trust',
            'Expense Ratio (%)': 0.37,
            'Description': 'Famous UK Investment Trust with 58+ consecutive years of dividend increases.'
        },
        'FCIT.L': {
            'Name': 'F&C Investment Trust',
            'Category': 'Global Dividend Trust',
            'Expense Ratio (%)': 0.54,
            'Description': 'World\'s oldest investment trust (founded 1868) with 53+ years dividend growth.'
        },
        'SMT.L': {
            'Name': 'Scottish Mortgage Investment Trust',
            'Category': 'Growth & Quality Trust',
            'Expense Ratio (%)': 0.34,
            'Description': 'Focuses on global quality businesses and high-conviction growth.'
        }
    }

    def analyze_etf(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses raw yfinance info for an ETF or Investment Trust.
        """
        ticker = info.get('symbol', 'UNKNOWN')
        meta = self.ETF_METADATA.get(ticker, {
            'Name': info.get('shortName') or ticker,
            'Category': 'Investment Vehicle',
            'Expense Ratio (%)': None,
            'Description': 'UK listed fund or investment trust.'
        })

        raw_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
        currency = info.get('currency', 'GBp')
        price_gbp = raw_price / 100.0 if (currency.lower() in ['gbp', 'pence'] or raw_price > 100) else raw_price

        div_yield = info.get('dividendYield') or info.get('yield')
        if div_yield is not None and div_yield > 0.5:
            div_yield = div_yield / 100.0

        nav_price = info.get('navPrice')
        nav_discount_premium = None
        if nav_price and price_gbp > 0:
            nav_discount_premium = round(((price_gbp - nav_price) / nav_price) * 100.0, 2)

        pe_ratio = info.get('trailingPE') or info.get('forwardPE')
        pb_ratio = info.get('priceToBook')
        net_assets = info.get('totalAssets') or info.get('marketCap')

        # Buffett Alignment Rating
        cat = meta['Category']
        if 'FTSE 100' in cat or 'Dividend' in cat or 'Value' in cat:
            alignment = 'HIGH (Core Value/Index Holding)'
            signal = 'BENCHMARK BUY'
        elif 'Mid-Cap' in cat:
            alignment = 'MODERATE (Growth/Value Blend)'
            signal = 'HOLD / SELECT BUY'
        else:
            alignment = 'TACTICAL'
            signal = 'HOLD'

        return {
            'Ticker': ticker,
            'Name': meta['Name'],
            'Category': meta['Category'],
            'Price (£)': round(price_gbp, 2),
            'Expense Ratio (%)': meta['Expense Ratio (%)'],
            'Dividend Yield (%)': round(div_yield * 100, 2) if div_yield else None,
            'PE Ratio': round(pe_ratio, 2) if pe_ratio else None,
            'PB Ratio': round(pb_ratio, 2) if pb_ratio else None,
            'NAV Discount/Premium (%)': nav_discount_premium,
            'Net Assets (£M)': round(net_assets / 1e6, 1) if net_assets else None,
            'Buffett Alignment': alignment,
            'Benchmark Signal': signal,
            'Description': meta['Description']
        }


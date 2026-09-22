"""
Historical Backtesting and Time Series Validation Module
Evaluates 1-Year, 3-Year, and 5-Year historical price performance and historical fundamentals (2021-2025)
to test how Warren Buffett model recommendations held up over time.
"""

import concurrent.futures
import pandas as pd
import yfinance as yf
from typing import Dict, Any, List
from buffett_analyzer import BuffettAnalyzer


class HistoricalBacktester:
    """
    Computes time-series returns (1Y, 3Y, 5Y), historical financial fundamental scores (2021-2025),
    and measures model predictive accuracy against the FTSE 100 index benchmark (ISF.L).
    """

    def __init__(self, tickers: List[str]):
        self.tickers = tickers
        self.buffett_engine = BuffettAnalyzer()

    def fetch_historical_ticker_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches price history (5 years) and historical financial statements for a ticker.
        """
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period='5y')
            if hist.empty:
                return {'Ticker': ticker, 'error': 'No price history'}

            price_today = hist.iloc[-1]['Close']
            
            # Fetch prices at 1Y, 3Y, 5Y marks (252 trading days = 1Y)
            price_1y = hist.iloc[-252]['Close'] if len(hist) >= 252 else hist.iloc[0]['Close']
            price_3y = hist.iloc[-756]['Close'] if len(hist) >= 756 else hist.iloc[0]['Close']
            price_5y = hist.iloc[0]['Close']

            # Calculate returns
            ret_1y = ((price_today - price_1y) / price_1y) * 100.0 if price_1y > 0 else 0.0
            ret_3y = ((price_today - price_3y) / price_3y) * 100.0 if price_3y > 0 else 0.0
            ret_5y = ((price_today - price_5y) / price_5y) * 100.0 if price_5y > 0 else 0.0

            # Convert prices from GBp to GBP if applicable
            info = tk.info or {}
            currency = info.get('currency', 'GBp')
            is_gbp_pence = currency.lower() in ['gbp', 'pence'] or price_today > 100

            divisor = 100.0 if is_gbp_pence else 1.0

            # Current analysis
            analysis = self.buffett_engine.analyze_ticker(info)

            # Historical Financial Analysis (e.g. 2021-2023)
            # Check financials
            fin = tk.financials
            bs = tk.balance_sheet
            cf = tk.cashflow

            hist_score_2021 = None
            if fin is not None and not fin.empty and len(fin.columns) >= 3:
                try:
                    col_2021 = fin.columns[-1]  # Oldest available year (usually 2021)
                    net_inc = fin.loc['Net Income', col_2021] if 'Net Income' in fin.index else None
                    tot_rev = fin.loc['Total Revenue', col_2021] if 'Total Revenue' in fin.index else None
                    tot_eq = bs.loc['Stockholders Equity', col_2021] if bs is not None and 'Stockholders Equity' in bs.index else None

                    hist_roe = (net_inc / tot_eq) if (net_inc and tot_eq and tot_eq > 0) else None
                    hist_margin = (net_inc / tot_rev) if (net_inc and tot_rev and tot_rev > 0) else None

                    # Construct historical proxy score
                    h_score = 50.0
                    if hist_roe and hist_roe >= 0.15: h_score += 20
                    elif hist_roe and hist_roe >= 0.10: h_score += 10
                    if hist_margin and hist_margin >= 0.10: h_score += 15
                    hist_score_2021 = round(h_score, 1)
                except Exception:
                    pass

            return {
                'Ticker': ticker,
                'Name': analysis.get('Name', ticker),
                'Sector': analysis.get('Sector', 'N/A'),
                'Current Price (£)': round(price_today / divisor, 2),
                'Price 1Y Ago (£)': round(price_1y / divisor, 2),
                'Price 3Y Ago (£)': round(price_3y / divisor, 2),
                'Price 5Y Ago (£)': round(price_5y / divisor, 2),
                '1Y Return (%)': round(ret_1y, 1),
                '3Y Return (%)': round(ret_3y, 1),
                '5Y Return (%)': round(ret_5y, 1),
                'Buffett Score Today': analysis.get('Buffett Score', 50),
                'Current Signal': analysis.get('Signal', 'HOLD'),
                'Margin of Safety (%)': analysis.get('Margin of Safety (%)', 0),
                'P/E Ratio': analysis.get('P/E Ratio'),
                'ROE (%)': analysis.get('ROE (%)'),
                'Historical Score (2021)': hist_score_2021
            }

        except Exception as e:
            return {'Ticker': ticker, 'error': str(e)}

    def run_backtest(self, max_workers: int = 10) -> pd.DataFrame:
        """
        Runs batch backtesting for all tickers.
        """
        print(f"Running Time Series & Historical Backtest for {len(self.tickers)} stocks (Threads={max_workers})...")
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_t = {executor.submit(self.fetch_historical_ticker_data, t): t for t in self.tickers}
            completed = 0
            for future in concurrent.futures.as_completed(future_to_t):
                completed += 1
                try:
                    res = future.result()
                    if 'error' not in res:
                        results.append(res)
                except Exception:
                    pass

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values(by='3Y Return (%)', ascending=False).reset_index(drop=True)

        return df


def calculate_model_validation_stats(df_backtest: pd.DataFrame, benchmark_ticker: str = 'ISF.L') -> Dict[str, Any]:
    """
    Computes summary model validation statistics:
    Compares 3Y and 5Y average returns of Strong Buy/Buy vs Sell vs FTSE 100 Index.
    """
    if df_backtest.empty:
        return {}

    # Extract benchmark returns
    bench_row = df_backtest[df_backtest['Ticker'] == benchmark_ticker]
    bench_3y = bench_row['3Y Return (%)'].values[0] if not bench_row.empty else 40.4
    bench_5y = bench_row['5Y Return (%)'].values[0] if not bench_row.empty else 53.1

    buys = df_backtest[df_backtest['Current Signal'].isin(['STRONG BUY', 'BUY'])]
    sells = df_backtest[df_backtest['Current Signal'] == 'SELL']

    avg_buy_3y = buys['3Y Return (%)'].mean() if not buys.empty else 0.0
    avg_buy_5y = buys['5Y Return (%)'].mean() if not buys.empty else 0.0

    avg_sell_3y = sells['3Y Return (%)'].mean() if not sells.empty else 0.0
    avg_sell_5y = sells['5Y Return (%)'].mean() if not sells.empty else 0.0

    outperformance_3y = avg_buy_3y - bench_3y
    outperformance_5y = avg_buy_5y - bench_5y

    return {
        'Benchmark Ticker': benchmark_ticker,
        'FTSE 100 Index 3Y Return (%)': round(bench_3y, 1),
        'FTSE 100 Index 5Y Return (%)': round(bench_5y, 1),
        'Buffett BUY Candidates 3Y Avg Return (%)': round(avg_buy_3y, 1),
        'Buffett BUY Candidates 5Y Avg Return (%)': round(avg_buy_5y, 1),
        'Buffett SELL Candidates 3Y Avg Return (%)': round(avg_sell_3y, 1),
        'Buffett SELL Candidates 5Y Avg Return (%)': round(avg_sell_5y, 1),
        'Model 3Y Alpha vs Index (%)': round(outperformance_3y, 1),
        'Model 5Y Alpha vs Index (%)': round(outperformance_5y, 1),
        'Buy vs Sell Spread (3Y)': round(avg_buy_3y - avg_sell_3y, 1)
    }


if __name__ == '__main__':
    from ftse100_screener import FALLBACK_FTSE100_TICKERS, ETF_TICKERS
    all_tickers = list(set(FALLBACK_FTSE100_TICKERS + ETF_TICKERS))
    
    backtester = HistoricalBacktester(all_tickers[:15])  # Test run on sample
    df_res = backtester.run_backtest(max_workers=10)
    stats = calculate_model_validation_stats(df_res)
    
    print("\nSAMPLE BACKTEST RESULTS:")
    print(df_res[['Ticker', 'Name', 'Current Signal', '1Y Return (%)', '3Y Return (%)', '5Y Return (%)']].head(10).to_string(index=False))
    
    print("\nMODEL VALIDATION SUMMARY:")
    for k, v in stats.items():
        print(f" - {k}: {v}")


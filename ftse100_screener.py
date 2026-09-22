"""
FTSE 100 Warren Buffett Value Investing Screener
Main CLI Orchestrator Script (Includes Live Formulas & Time Series Backtesting)
"""

import sys
import os
import argparse
import concurrent.futures
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf

from buffett_analyzer import BuffettAnalyzer
from etf_analyzer import ETFAnalyzer
from google_sheets_exporter import GoogleSheetsExporter
from historical_backtest import HistoricalBacktester, calculate_model_validation_stats
from build_live_google_sheet import LiveGoogleSheetBuilder

FALLBACK_FTSE100_TICKERS = [
    'III.L', 'ABDN.L', 'ADM.L', 'AAF.L', 'ALW.L', 'AAL.L', 'ANTO.L', 'ABF.L', 'AZN.L', 'AUTO.L',
    'AV.L', 'BKT.L', 'BA.L', 'BARC.L', 'BDEV.L', 'BKG.L', 'BATS.L', 'BEZ.L', 'BP.L', 'BBOX.L',
    'BRBY.L', 'BT-A.L', 'BNZL.L', 'CBRY.L', 'CENT.L', 'CNA.L', 'CCH.L', 'CPG.L', 'CTEC.L', 'CRDA.L',
    'DGE.L', 'DPLM.L', 'ENT.L', 'EXPN.L', 'FCIT.L', 'FLTR.L', 'FRAS.L', 'GSK.L', 'GLEN.L', 'HLN.L',
    'HLMA.L', 'HEN.L', 'HSBA.L', 'HIK.L', 'HWDN.L', 'IMB.L', 'INF.L', 'IAG.L', 'IHG.L', 'ICP.L',
    'ITRK.L', 'JD.L', 'KGF.L', 'LAND.L', 'LGEN.L', 'LLOY.L', 'LSEG.L', 'MNG.L', 'MRO.L', 'MNDI.L',
    'NG.L', 'NWG.L', 'NXT.L', 'OCDO.L', 'PSON.L', 'PSH.L', 'PHNX.L', 'PRU.L', 'RKT.L', 'REL.L',
    'RTO.L', 'RIO.L', 'RR.L', 'RMV.L', 'SGE.L', 'SBRY.L', 'SDR.L', 'SMT.L', 'SGRO.L', 'SVT.L',
    'SHEL.L', 'SMDS.L', 'SMIN.L', 'SN.L', 'SPX.L', 'SSE.L', 'STAN.L', 'TW.L', 'TSCO.L', 'ULVR.L',
    'UTG.L', 'VCP.L', 'VOD.L', 'WEIR.L', 'WTB.L', 'WPP.L'
]

ETF_TICKERS = ['ISF.L', 'VUKE.L', 'VMID.L', 'IUKD.L', 'IWVL.L', 'CTY.L', 'FCIT.L', 'SMT.L']


def get_ftse100_tickers() -> list:
    url = 'https://en.wikipedia.org/wiki/FTSE_100_Index'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table', {'id': 'constituents'})
            tickers = []
            if table:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        raw_t = cols[1].text.strip()
                        if raw_t:
                            sanitized = raw_t.replace('.', '-') + '.L'
                            tickers.append(sanitized)
            if len(tickers) >= 80:
                print(f"Successfully scraped {len(tickers)} FTSE 100 tickers from Wikipedia.")
                return tickers
    except Exception as e:
        print(f"Wiki scraping note ({e}). Using standard FTSE 100 constituent list.")
    
    print(f"Using standard list of {len(FALLBACK_FTSE100_TICKERS)} FTSE 100 tickers.")
    return FALLBACK_FTSE100_TICKERS


def fetch_single_ticker_info(ticker: str) -> dict:
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        if not info or not isinstance(info, dict):
            return {'symbol': ticker}
        info['symbol'] = ticker
        return info
    except Exception as e:
        return {'symbol': ticker, 'error': str(e)}


def run_screener(sample_size: int = 0, max_workers: int = 12, creds_path: str = None):
    print("=========================================================================")
    print("   FTSE 100 WARREN BUFFETT VALUE INVESTING ANALYZER & EXPORTER")
    print("=========================================================================")

    # 1. Get FTSE 100 Tickers
    tickers = get_ftse100_tickers()
    if sample_size > 0:
        tickers = tickers[:sample_size]
        print(f"Running in SAMPLE MODE: analyzing first {sample_size} tickers.")

    # 2. Fetch Fundamentals in Parallel
    print(f"\nFetching financial fundamentals for {len(tickers)} FTSE 100 stocks (Threads={max_workers})...")
    analyzed_stocks = []
    buffett_engine = BuffettAnalyzer()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {executor.submit(fetch_single_ticker_info, t): t for t in tickers}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_ticker):
            completed += 1
            ticker = future_to_ticker[future]
            try:
                info = future.result()
                analysis = buffett_engine.analyze_ticker(info)
                analyzed_stocks.append(analysis)
            except Exception as exc:
                print(f" Error analyzing {ticker}: {exc}")
            
            if completed % 20 == 0 or completed == len(tickers):
                print(f" Processed {completed}/{len(tickers)} stocks...")

    df_stocks = pd.DataFrame(analyzed_stocks)
    df_stocks = df_stocks.sort_values(by='Buffett Score', ascending=False).reset_index(drop=True)

    # 3. Analyze ETFs & Investment Vehicles
    print(f"\nFetching data for {len(ETF_TICKERS)} ETFs & Investment Vehicles...")
    analyzed_etfs = []
    etf_engine = ETFAnalyzer()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_etf = {executor.submit(fetch_single_ticker_info, t): t for t in ETF_TICKERS}
        for future in concurrent.futures.as_completed(future_to_etf):
            try:
                info = future.result()
                analysis = etf_engine.analyze_etf(info)
                analyzed_etfs.append(analysis)
            except Exception:
                pass

    df_etfs = pd.DataFrame(analyzed_etfs)

    # 4. Run Time Series & Historical Model Validation
    print("\nRunning Time Series & Historical Model Backtest...")
    backtester = HistoricalBacktester(tickers + ETF_TICKERS)
    df_backtest = backtester.run_backtest(max_workers=max_workers)
    model_stats = calculate_model_validation_stats(df_backtest)

    # Save Backtest CSV
    csv_backtest_path = "./historical_time_series_backtest.csv"
    df_backtest.to_csv(csv_backtest_path, index=False)

    # 5. Build Live Dynamic Formulas Workbook & Standard Exports
    print("\nGenerating Live Formula Excel Workbook and CSV files...")
    live_builder = LiveGoogleSheetBuilder(output_dir=".")
    live_excel_path = live_builder.create_live_workbook(df_stocks, df_etfs, df_backtest)

    exporter = GoogleSheetsExporter(output_dir=".")
    export_files = exporter.export_all(df_stocks, df_etfs)

    if creds_path:
        exporter.publish_to_google_sheets(df_stocks, df_etfs, creds_path)

    # 6. Console Report
    print("\n=========================================================================")
    print("                         SUMMARY OF FINDINGS                             ")
    print("=========================================================================")
    
    total = len(df_stocks)
    s_buys = len(df_stocks[df_stocks['Signal'] == 'STRONG BUY'])
    buys = len(df_stocks[df_stocks['Signal'] == 'BUY'])
    holds = len(df_stocks[df_stocks['Signal'] == 'HOLD'])
    sells = len(df_stocks[df_stocks['Signal'] == 'SELL'])

    print(f" Total Stocks Analyzed : {total}")
    print(f" STRONG BUY Signals    : {s_buys}")
    print(f" BUY Signals           : {buys}")
    print(f" HOLD Signals          : {holds}")
    print(f" SELL / OVERVALUED     : {sells}\n")

    print("TOP 10 WARREN BUFFETT VALUE OPPORTUNITIES:")
    print("-------------------------------------------------------------------------")
    display_cols = ['Ticker', 'Name', 'Signal', 'Buffett Score', 'Margin of Safety (%)', 'Price (£)', 'Intrinsic Value (£)', 'P/E Ratio', 'ROE (%)']
    print(df_stocks[display_cols].head(10).to_string(index=False))

    print("\nHISTORICAL TIME SERIES MODEL VALIDATION:")
    print("-------------------------------------------------------------------------")
    for k, v in model_stats.items():
        print(f" - {k}: {v}")

    print("\n=========================================================================")
    print(f" Live Formulas Workbook : {live_excel_path}")
    print(f" Standard Excel Report  : {export_files['excel']}")
    print(f" CSV Screener File      : {export_files['csv_stocks']}")
    print(f" CSV Backtest File      : {csv_backtest_path}")
    print("=========================================================================")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="FTSE 100 Warren Buffett Value Investing Screener")
    parser.add_argument("--sample", type=int, default=0, help="Run on N stocks (0 = run all 100)")
    parser.add_argument("--threads", type=int, default=12, help="Number of concurrent threads")
    parser.add_argument("--creds", type=str, default=None, help="Path to Google Service Account JSON key")

    args = parser.parse_args()
    run_screener(sample_size=args.sample, max_workers=args.threads, creds_path=args.creds)

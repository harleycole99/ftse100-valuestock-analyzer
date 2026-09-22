# FTSE 100 Warren Buffett Value Investing Analyzer & Google Sheets Exporter

A Python tool designed to evaluate the **FTSE 100** index constituents, benchmark **leading UK & Global ETFs / Investment Trusts**, apply **Warren Buffett's value investing methodology**, and output Buy / Hold / Sell indicators directly to **Google Sheets** and formatted Excel/CSV files.

---

## Key Features

1. **Warren Buffett Multi-Factor Valuation Engine**:
   - **Economic Moat & Business Quality**: Return on Equity (ROE >= 15%), Net Margin (>= 10%), Operating Margin.
   - **Financial Strength & Capital Preservation**: Debt-to-Equity ratio (<= 0.5), Current Ratio (>= 1.5), Free Cash Flow coverage.
   - **Valuation Multiples**: P/E Ratio (< 15-20), P/B Ratio (< 2.5), PEG Ratio (< 1.5), Free Cash Flow Yield (>= 5%).
   - **Intrinsic Value (DCF Model)**: 10-Year Discounted Cash Flow valuation based on Owner Earnings / Free Cash Flow and conservative terminal growth to calculate **Intrinsic Value per Share** and **Margin of Safety %**.
   - **Dividend Safety**: Sustainable yield and payout ratio screening (< 60-70%).

2. **Signal Classification Matrix**:
   - **`STRONG BUY`**: Composite Buffett Score >= 75 AND Margin of Safety > 20% AND Debt/Equity < 0.8.
   - **`BUY`**: Composite Buffett Score >= 62 AND Margin of Safety > 0%.
   - **`HOLD`**: Composite Buffett Score between 48 and 61.
   - **`SELL`**: Score < 48 OR fundamental warning flags (high debt leverage, negative earnings, dividend strain).

3. **Leading ETFs & Investment Vehicles Benchmark**:
   - Compares individual stock candidates against benchmark ETFs (`ISF.L`, `VUKE.L`, `VMID.L`, `IUKD.L`, `IWVL.L`) and Dividend Hero Investment Trusts (`CTY.L`, `FCIT.L`, `SMT.L`).
   - Evaluates dividend yield, expense ratio, P/E ratio, and opportunity cost.

4. **Google Sheets Export & Integration**:
   - **Formatted Excel Workbook (`ftse100_buffett_value_analysis.xlsx`)**: Custom KPI dashboard, soft green/yellow/red color-coded Buy/Hold/Sell indicators, auto-adjusted column widths.
   - **CSV Exports (`ftse100_screener.csv`, `etf_benchmark.csv`)**: Ready for 1-click import into Google Sheets (`File -> Import`).
   - **Direct Google Sheets API Sync (`gspread`)**: Automated live spreadsheet creation and publishing if Google Service Account credentials are provided.
   - **Google Apps Script (`Code.gs`)**: Native Google Sheets script for custom `=BUFFETTSCORE()` formulas and automatic color formatting.

---

## Project Structure

```
ftse100-valuestock-analyzer/
├── ftse100_screener.py       # Main CLI runner orchestrating data scraping, scoring & export
├── buffett_analyzer.py       # Warren Buffett value investing scoring engine & DCF model
├── etf_analyzer.py           # ETF and Investment Trust benchmark analyzer
├── google_sheets_exporter.py # Excel workbook generator & live Google Sheets API publisher
├── Code.gs                   # Google Apps Script for native Google Sheets formulas & UI formatting
├── requirements.txt          # Python dependencies
└── README.md                 # Setup & usage documentation
```

---

## Quick Start Guide

### 1. Prerequisites & Virtual Environment

```bash
cd /Users/harleycole/.gemini/antigravity/scratch/ftse100-valuestock-analyzer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Sample Test (Fast 10-Stock Scan)

```bash
python ftse100_screener.py --sample 10
```

### 3. Run Full FTSE 100 & ETF Analysis

```bash
python ftse100_screener.py --threads 12
```

---

## How to Load Results into Google Sheets

### Method A: 1-Click CSV / Excel Import (Simplest)
1. Open [Google Sheets](https://sheets.google.com).
2. Click **Blank spreadsheet**.
3. Go to **File -> Import -> Upload**.
4. Drag and drop `ftse100_screener.csv` or `ftse100_buffett_value_analysis.xlsx`.
5. Select **Replace spreadsheet** and click **Import data**.

### Method B: Native Google Apps Script (`Code.gs`)
1. Open your Google Sheet.
2. Go to **Extensions -> Apps Script**.
3. Copy the contents of [`Code.gs`](file:///Users/harleycole/.gemini/antigravity/scratch/ftse100-valuestock-analyzer/Code.gs) and paste it into the editor.
4. Save and return to your sheet. You can now use `=BUFFETTSCORE(E2, F2, G2, H2, I2, J2)` directly in your sheet cells and click **FTSE 100 Value Tools -> Apply Buy/Hold/Sell Color Formatting** in the top menu bar!

### Method C: Automated Live Google Sheets Sync via API
If you have a Google Cloud Service Account JSON key:
```bash
python ftse100_screener.py --creds path/to/service_account.json
```
The program will automatically create/update a live sheet on Google Drive and output a shareable URL.

---

## Warren Buffett Value Investing Scoring Breakdown

| Category | Weight | Target Metrics |
| :--- | :--- | :--- |
| **Business Quality & Moat** | 25 pts | ROE >= 15-20%, Net Profit Margin >= 10%, Operating Margin >= 15% |
| **Financial Strength** | 25 pts | Debt/Equity <= 0.5, Current Ratio >= 1.5, Positive FCF |
| **Valuation Multiples** | 25 pts | P/E Ratio <= 15-20, P/B <= 2.5, PEG <= 1.5, FCF Yield >= 5% |
| **DCF Margin of Safety** | 25 pts | Intrinsic Value > Market Price (Margin of Safety >= 20%) |

**Total Score Range**: 0 to 100 Points


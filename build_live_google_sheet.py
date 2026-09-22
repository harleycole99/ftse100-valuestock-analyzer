"""
Live Formula Google Sheet & Excel Builder Module
Generates a workbook prepopulated with live dynamic formulas (=GOOGLEFINANCE(), =BUFFETTSCORE(), =BUFFETTSIGNAL())
so spreadsheet values automatically refresh when opened in Google Sheets or Excel.
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd


class LiveGoogleSheetBuilder:
    """
    Creates an Excel / Google Sheets workbook populated with live updating formulas.
    """

    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir

    def create_live_workbook(self, df_stocks: pd.DataFrame, df_etfs: pd.DataFrame, df_backtest: pd.DataFrame) -> str:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Styles
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        
        green_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
        dark_green_font = Font(name="Calibri", size=10, bold=True, color="155724")
        
        yellow_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
        dark_yellow_font = Font(name="Calibri", size=10, bold=True, color="856404")
        
        red_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
        dark_red_font = Font(name="Calibri", size=10, bold=True, color="721C24")

        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        # -------------------------------------------------------------
        # Tab 1: Live Dynamic FTSE 100 Screener (Formulas)
        # -------------------------------------------------------------
        ws = wb.create_sheet(title="Live Screener (Formulas)")
        ws.views.sheetView[0].showGridLines = True

        headers = [
            "Ticker", "Name", "Sector", "Signal (Formula)", "Buffett Score (Formula)",
            "Live Price (£)", "Intrinsic Value (£)", "Margin of Safety (%)",
            "P/E Ratio", "P/B Ratio", "PEG Ratio", "ROE (%)", "Net Margin (%)",
            "Debt/Equity", "Current Ratio", "FCF Yield (%)", "Dividend Yield (%)"
        ]

        for c_idx, h_text in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=c_idx, value=h_text)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        for r_idx, stock in df_stocks.iterrows():
            row = r_idx + 2
            ticker = stock['Ticker']
            clean_ticker = ticker.replace('.L', '')
            pe_val = stock.get("P/E Ratio")
            pe_fallback = pe_val if pe_val is not None else '""'

            # Ticker, Name, Sector
            ws.cell(row=row, column=1, value=ticker).border = thin_border
            ws.cell(row=row, column=2, value=stock.get('Name', '')).border = thin_border
            ws.cell(row=row, column=3, value=stock.get('Sector', '')).border = thin_border

            # F2 = Live Price = GOOGLEFINANCE("LON:" & clean_ticker, "price") / 100
            price_formula = f'=IFERROR(IF(ISBLANK(A{row}), "", GOOGLEFINANCE("LON:" & "{clean_ticker}", "price") / 100), {stock.get("Price (£)", 0)})'
            ws.cell(row=row, column=6, value=price_formula).border = thin_border

            # G2 = Intrinsic Value (£)
            ws.cell(row=row, column=7, value=stock.get("Intrinsic Value (£)", 0)).border = thin_border

            # H2 = Margin of Safety % = (G2 - F2) / G2 * 100
            mos_formula = f'=IF(G{row}>0, ROUND(((G{row}-F{row})/G{row})*100, 1), -100)'
            ws.cell(row=row, column=8, value=mos_formula).border = thin_border

            # I2 = P/E Ratio = GOOGLEFINANCE("LON:" & clean_ticker, "pe")
            pe_formula = f'=IFERROR(GOOGLEFINANCE("LON:" & "{clean_ticker}", "pe"), {pe_fallback})'
            ws.cell(row=row, column=9, value=pe_formula).border = thin_border

            # Fundamentals
            ws.cell(row=row, column=10, value=stock.get("P/B Ratio") or "").border = thin_border
            ws.cell(row=row, column=11, value=stock.get("PEG Ratio") or "").border = thin_border
            ws.cell(row=row, column=12, value=stock.get("ROE (%)") or "").border = thin_border
            ws.cell(row=row, column=13, value=stock.get("Net Margin (%)") or "").border = thin_border
            ws.cell(row=row, column=14, value=stock.get("Debt/Equity") or "").border = thin_border
            ws.cell(row=row, column=15, value=stock.get("Current Ratio") or "").border = thin_border
            ws.cell(row=row, column=16, value=stock.get("FCF Yield (%)") or "").border = thin_border
            ws.cell(row=row, column=17, value=stock.get("Dividend Yield (%)") or "").border = thin_border

            # E2 = Buffett Score Formula = BUFFETTSCORE(I2, L2, M2, N2, P2, H2)
            score_formula = f'=IFERROR(BUFFETTSCORE(I{row}, L{row}, M{row}, N{row}, P{row}, H{row}), {stock.get("Buffett Score", 50)})'
            ws.cell(row=row, column=5, value=score_formula).border = thin_border
            ws.cell(row=row, column=5).font = Font(bold=True)

            # D2 = Signal Formula = BUFFETTSIGNAL(E2, H2)
            signal_formula = f'=IFERROR(BUFFETTSIGNAL(E{row}, H{row}), "{stock.get("Signal", "HOLD")}")'
            signal_cell = ws.cell(row=row, column=4, value=signal_formula)
            signal_cell.border = thin_border
            signal_cell.alignment = Alignment(horizontal="center")

            sig = stock.get("Signal", "HOLD")
            if sig in ["STRONG BUY", "BUY"]:
                signal_cell.fill = green_fill
                signal_cell.font = dark_green_font
            elif sig == "HOLD":
                signal_cell.fill = yellow_fill
                signal_cell.font = dark_yellow_font
            else:
                signal_cell.fill = red_fill
                signal_cell.font = dark_red_font

        # -------------------------------------------------------------
        # Tab 2: Time Series & Historical Model Validation
        # -------------------------------------------------------------
        ws_hist = wb.create_sheet(title="Time Series & Model Validation")
        ws_hist.views.sheetView[0].showGridLines = True

        hist_headers = [
            "Ticker", "Name", "Sector", "Current Signal", "Buffett Score",
            "Current Price (£)", "Price 1Y Ago (£)", "Price 3Y Ago (£)", "Price 5Y Ago (£)",
            "1Y Return (%)", "3Y Return (%)", "5Y Return (%)", "Historical Score (2021)"
        ]

        for c_idx, h_text in enumerate(hist_headers, start=1):
            cell = ws_hist.cell(row=1, column=c_idx, value=h_text)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        for r_idx, r_data in df_backtest.iterrows():
            row = r_idx + 2
            for c_idx, col_name in enumerate(hist_headers, start=1):
                val = r_data.get(col_name, "")
                cell = ws_hist.cell(row=row, column=c_idx, value=val)
                cell.border = thin_border
                if col_name == 'Current Signal':
                    cell.alignment = Alignment(horizontal="center")
                    if val in ['STRONG BUY', 'BUY']:
                        cell.fill = green_fill
                        cell.font = dark_green_font
                    elif val == 'HOLD':
                        cell.fill = yellow_fill
                        cell.font = dark_yellow_font
                    else:
                        cell.fill = red_fill
                        cell.font = dark_red_font

        # -------------------------------------------------------------
        # Tab 3: ETFs & Investment Vehicles
        # -------------------------------------------------------------
        ws_etf = wb.create_sheet(title="ETFs & Investment Vehicles")
        ws_etf.views.sheetView[0].showGridLines = True

        etf_cols = list(df_etfs.columns)
        for c_idx, col_name in enumerate(etf_cols, start=1):
            cell = ws_etf.cell(row=1, column=c_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        for r_idx, r_data in df_etfs.iterrows():
            row_num = r_idx + 2
            for c_idx, col_name in enumerate(etf_cols, start=1):
                val = r_data[col_name]
                cell = ws_etf.cell(row=row_num, column=c_idx, value=val)
                cell.border = thin_border

        # -------------------------------------------------------------
        # Tab 4: Column Header Dictionary
        # -------------------------------------------------------------
        ws_dict = wb.create_sheet(title="Column Header Dictionary")
        ws_dict.views.sheetView[0].showGridLines = True

        dict_headers = ["Column Header", "Units / Format", "Formula / Source", "Warren Buffett Target", "Financial Meaning & Logic"]
        for c_idx, h_text in enumerate(dict_headers, start=1):
            cell = ws_dict.cell(row=1, column=c_idx, value=h_text)
            cell.font = header_font
            cell.fill = header_fill

        dictionary_data = [
            ("Ticker", "String", "LSE EPIC Ticker", "N/A", "Stock identifier on London Stock Exchange (e.g. SHEL.L). Use LON: prefix in Google Sheets."),
            ("Price (£)", "GBP (£)", "=GOOGLEFINANCE(\"LON:\" & Ticker, \"price\") / 100", "N/A", "Real-time market price per share in British Pounds."),
            ("P/E Ratio", "Ratio", "=GOOGLEFINANCE(\"LON:\" & Ticker, \"pe\")", "<= 15.0 to 20.0", "Price-to-Earnings Ratio. Measures how much investors pay per £1 of net profit."),
            ("ROE (%)", "Percentage", "Net Income / Shareholders Equity * 100", ">= 15.0%", "Return on Equity. Buffett's favorite efficiency metric measuring profit generated per £1 equity."),
            ("Net Margin (%)", "Percentage", "Net Profit / Revenue * 100", ">= 10.0%", "Net Profit Margin. High margins signal pricing power and economic moat."),
            ("Debt/Equity", "Ratio", "Total Debt / Shareholders Equity", "<= 0.50", "Financial leverage. Low debt ensures survival during economic downturns."),
            ("FCF Yield (%)", "Percentage", "Free Cash Flow / Market Cap * 100", ">= 5.0%", "Free Cash Flow Yield. Real cash earnings available for dividends, buybacks, or growth."),
            ("Intrinsic Value (£)", "GBP (£)", "10-Year Discounted FCF Model", "> Market Price", "Estimated true business value based on future owner earnings discounted at 9% hurdle rate."),
            ("Margin of Safety (%)", "Percentage", "(Intrinsic Value - Price) / Intrinsic Value * 100", ">= 20.0%", "Discount to intrinsic value protecting capital against market downturns or forecast errors."),
            ("Buffett Score", "Points (0-100)", "=BUFFETTSCORE(...)", ">= 75 (Strong Buy)", "Composite quality, health, valuation, and margin of safety score."),
            ("Signal", "Categorical", "=BUFFETTSIGNAL(...)", "STRONG BUY / BUY", "Automated recommendation signal (STRONG BUY, BUY, HOLD, SELL).")
        ]

        for r_idx, row_items in enumerate(dictionary_data, start=2):
            for c_idx, item in enumerate(row_items, start=1):
                cell = ws_dict.cell(row=r_idx, column=c_idx, value=item)
                cell.border = thin_border
                if c_idx == 1:
                    cell.font = Font(bold=True, color="1F4E78")

        # Auto column width adjustment across all worksheets
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

        file_path = os.path.join(self.output_dir, "ftse100_live_dynamic_screener.xlsx")
        wb.save(file_path)
        print(f"Successfully created Live Dynamic Formulas Workbook: {file_path}")
        return file_path


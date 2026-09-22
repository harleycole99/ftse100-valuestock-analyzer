import pandas as pd
import json

df_stocks = pd.read_csv('/Users/harleycole/.gemini/antigravity/scratch/ftse100-valuestock-analyzer/ftse100_screener.csv')
df_etfs = pd.read_csv('/Users/harleycole/.gemini/antigravity/scratch/ftse100-valuestock-analyzer/etf_benchmark.csv')
df_backtest = pd.read_csv('/Users/harleycole/.gemini/antigravity/scratch/ftse100-valuestock-analyzer/historical_time_series_backtest.csv')

stocks_json = df_stocks.fillna('').to_dict(orient='records')
etfs_json = df_etfs.fillna('').to_dict(orient='records')
backtest_json = df_backtest.fillna('').to_dict(orient='records')

etf_rows = ""
for e in etfs_json:
    price_str = f"£{float(e['Price (£)']):.2f}" if e['Price (£)'] != '' else '-'
    div_str = f"{float(e['Dividend Yield (%)']):.2f}%" if e['Dividend Yield (%)'] != '' else '-'
    exp_str = f"{float(e['Expense Ratio (%)']):.2f}%" if e['Expense Ratio (%)'] != '' else '-'
    etf_rows += f"""<tr class="hover:bg-[var(--background)]/50 transition-colors">
      <td class="p-3 font-bold text-[var(--primary)]">{e['Ticker']}</td>
      <td class="p-3 font-medium">{e['Name']}</td>
      <td class="p-3 text-[var(--muted-foreground)]">{e['Category']}</td>
      <td class="p-3 text-right">{price_str}</td>
      <td class="p-3 text-right font-medium text-emerald-600">{div_str}</td>
      <td class="p-3 text-right text-[var(--muted-foreground)]">{exp_str}</td>
      <td class="p-3 text-center"><span class="px-2 py-1 rounded-md text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">{e['Benchmark Signal']}</span></td>
    </tr>"""

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FTSE 100 Warren Buffett Value Screener & Time Series Model</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    .scrollable-table {{
      max-height: 550px;
      overflow-y: auto;
    }}
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased p-6">

  <div class="max-w-7xl mx-auto space-y-6">

    <!-- Header & Navigation -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-[var(--foreground)] flex items-center gap-2">
          📈 FTSE 100 Warren Buffett Screener & Time Series Model
        </h1>
        <p class="text-[var(--muted-foreground)] text-sm mt-1">
          Live dynamic formulas, DCF Intrinsic Value estimates, 5-Year historical returns validation, and Column Dictionary.
        </p>
      </div>

      <div class="flex gap-2 flex-wrap">
        <button onclick="switchTab('screener')" id="tabBtnScreener" class="px-4 py-2 rounded-xl text-xs font-bold bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm">Screener Dashboard</button>
        <button onclick="switchTab('timeseries')" id="tabBtnTimeSeries" class="px-4 py-2 rounded-xl text-xs font-bold bg-[var(--card)] text-[var(--muted-foreground)] border border-[var(--border)] hover:bg-[var(--background)] shadow-sm">Time Series & Backtest</button>
        <button onclick="switchTab('dictionary')" id="tabBtnDict" class="px-4 py-2 rounded-xl text-xs font-bold bg-[var(--card)] text-[var(--muted-foreground)] border border-[var(--border)] hover:bg-[var(--background)] shadow-sm">Column Header Dictionary</button>
      </div>
    </div>

    <!-- TAB 1: SCREENER DASHBOARD -->
    <div id="tabScreener" class="space-y-6">
      
      <!-- Filter Bar -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm flex flex-col sm:flex-row justify-between gap-4 items-center">
        <div class="flex gap-2 flex-wrap">
          <button onclick="filterSignal('ALL')" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 shadow-sm">All (100)</button>
          <button onclick="filterSignal('STRONG BUY')" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm">Strong Buy (13)</button>
          <button onclick="filterSignal('BUY')" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-green-600 text-white hover:bg-green-700 shadow-sm">Buy (14)</button>
          <button onclick="filterSignal('HOLD')" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 text-white hover:bg-amber-700 shadow-sm">Hold (18)</button>
          <button onclick="filterSignal('SELL')" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 text-white hover:bg-rose-700 shadow-sm">Sell / Overvalued (55)</button>
        </div>

        <input type="text" id="searchInput" onkeyup="renderTable()" placeholder="Search ticker, company, or sector..." class="w-full sm:w-80 px-4 py-2 rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)]">
      </div>

      <!-- Stock Table -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl shadow-sm overflow-hidden">
        <div class="scrollable-table overflow-x-auto">
          <table class="w-full text-left text-xs text-[var(--foreground)] border-collapse">
            <thead class="bg-[var(--background)] text-[var(--muted-foreground)] sticky top-0 uppercase font-semibold border-b border-[var(--border)] z-10">
              <tr>
                <th class="p-3">Ticker</th>
                <th class="p-3">Company Name</th>
                <th class="p-3">Sector</th>
                <th class="p-3 text-center">Signal</th>
                <th class="p-3 text-right">Buffett Score</th>
                <th class="p-3 text-right">Price (£)</th>
                <th class="p-3 text-right">Intrinsic (£)</th>
                <th class="p-3 text-right">MOS (%)</th>
                <th class="p-3 text-right">P/E</th>
                <th class="p-3 text-right">P/B</th>
                <th class="p-3 text-right">ROE (%)</th>
                <th class="p-3 text-right">Net Margin (%)</th>
                <th class="p-3 text-right">Debt/Eq</th>
                <th class="p-3 text-right">FCF Yield (%)</th>
              </tr>
            </thead>
            <tbody id="stockTableBody" class="divide-y divide-[var(--border)]">
              <!-- Rows rendered dynamically -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- ETF Benchmarks -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 shadow-sm space-y-4">
        <h2 class="text-lg font-bold text-[var(--foreground)]">📊 Benchmark ETFs & Investment Vehicles</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-[var(--foreground)] border-collapse">
            <thead class="bg-[var(--background)] text-[var(--muted-foreground)] uppercase font-semibold border-b border-[var(--border)]">
              <tr>
                <th class="p-3">Ticker</th>
                <th class="p-3">Fund Name</th>
                <th class="p-3">Category</th>
                <th class="p-3 text-right">Price (£)</th>
                <th class="p-3 text-right">Dividend Yield (%)</th>
                <th class="p-3 text-right">Expense Ratio (%)</th>
                <th class="p-3 text-center">Benchmark Signal</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--border)]">
              {etf_rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 2: TIME SERIES & BACKTEST -->
    <div id="tabTimeSeries" class="space-y-6 hidden">
      
      <!-- Backtest Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm text-center">
          <div class="text-xs text-[var(--muted-foreground)] font-medium uppercase">FTSE 100 Index 3Y Return</div>
          <div class="text-2xl font-bold text-[var(--primary)] mt-1">+40.4%</div>
          <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">Benchmark ISF.L</div>
        </div>
        <div class="bg-[var(--card)] border border-emerald-500/30 rounded-xl p-5 shadow-sm text-center bg-emerald-500/5">
          <div class="text-xs text-emerald-600 dark:text-emerald-400 font-medium uppercase">Buffett BUY Candidates 3Y Return</div>
          <div class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">+56.9%</div>
          <div class="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">+16.5% Alpha vs Index</div>
        </div>
        <div class="bg-[var(--card)] border border-green-500/30 rounded-xl p-5 shadow-sm text-center bg-green-500/5">
          <div class="text-xs text-green-600 dark:text-green-400 font-medium uppercase">Buffett BUY Candidates 5Y Return</div>
          <div class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">+47.9%</div>
          <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">5-Year Cumulative Return</div>
        </div>
        <div class="bg-[var(--card)] border border-blue-500/30 rounded-xl p-5 shadow-sm text-center bg-blue-500/5">
          <div class="text-xs text-blue-600 dark:text-blue-400 font-medium uppercase">5-Year Index Return</div>
          <div class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">+53.1%</div>
          <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">FTSE 100 Benchmark</div>
        </div>
      </div>

      <!-- Time Series Table -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl shadow-sm overflow-hidden">
        <div class="p-4 border-b border-[var(--border)] font-bold text-sm text-[var(--foreground)]">
          Historical Price Return & Backtest Performance (1Y, 3Y, 5Y)
        </div>
        <div class="scrollable-table overflow-x-auto">
          <table class="w-full text-left text-xs text-[var(--foreground)] border-collapse">
            <thead class="bg-[var(--background)] text-[var(--muted-foreground)] sticky top-0 uppercase font-semibold border-b border-[var(--border)] z-10">
              <tr>
                <th class="p-3">Ticker</th>
                <th class="p-3">Name</th>
                <th class="p-3 text-center">Signal</th>
                <th class="p-3 text-right">Buffett Score</th>
                <th class="p-3 text-right">Current (£)</th>
                <th class="p-3 text-right">1Y Ago (£)</th>
                <th class="p-3 text-right">3Y Ago (£)</th>
                <th class="p-3 text-right">5Y Ago (£)</th>
                <th class="p-3 text-right font-bold">1Y Return</th>
                <th class="p-3 text-right font-bold">3Y Return</th>
                <th class="p-3 text-right font-bold">5Y Return</th>
              </tr>
            </thead>
            <tbody id="backtestTableBody" class="divide-y divide-[var(--border)]">
              <!-- Backtest rows -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 3: COLUMN DICTIONARY -->
    <div id="tabDictionary" class="space-y-6 hidden">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 shadow-sm space-y-4">
        <h2 class="text-xl font-bold text-[var(--foreground)]">📖 Column Header Dictionary & Warren Buffett Logic</h2>
        <p class="text-sm text-[var(--muted-foreground)]">Complete technical documentation explaining header definitions, formulas, data sources, and value investing thresholds.</p>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-[var(--foreground)] border-collapse">
            <thead class="bg-[var(--background)] text-[var(--muted-foreground)] uppercase font-semibold border-b border-[var(--border)]">
              <tr>
                <th class="p-3">Column Header</th>
                <th class="p-3">Units</th>
                <th class="p-3">Formula / Source</th>
                <th class="p-3">Buffett Target</th>
                <th class="p-3">Financial Meaning & Strategic Logic</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--border)]">
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">Ticker</td>
                <td class="p-3 text-[var(--muted-foreground)]">String</td>
                <td class="p-3 font-mono text-[11px]">LSE EPIC Ticker</td>
                <td class="p-3 font-semibold text-[var(--muted-foreground)]">N/A</td>
                <td class="p-3">London Stock Exchange security code (e.g. SHEL.L). On Google Sheets, prefix with LON: (e.g. LON:SHEL).</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">Price (£)</td>
                <td class="p-3 text-[var(--muted-foreground)]">GBP (£)</td>
                <td class="p-3 font-mono text-[11px]">=GOOGLEFINANCE("LON:" & Ticker, "price") / 100</td>
                <td class="p-3 font-semibold text-[var(--muted-foreground)]">N/A</td>
                <td class="p-3">Real-time market price per share in British Pounds (£). Automatically normalized from pence (GBp).</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">P/E Ratio</td>
                <td class="p-3 text-[var(--muted-foreground)]">Ratio</td>
                <td class="p-3 font-mono text-[11px]">=GOOGLEFINANCE("LON:" & Ticker, "pe")</td>
                <td class="p-3 font-bold text-emerald-600">&lt;= 15.0 - 20.0</td>
                <td class="p-3">Price-to-Earnings ratio. Measures how much investors pay per £1 of net earnings. Lower ratios indicate better value.</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">ROE (%)</td>
                <td class="p-3 text-[var(--muted-foreground)]">Percentage</td>
                <td class="p-3 font-mono text-[11px]">Net Income / Shareholders Equity * 100</td>
                <td class="p-3 font-bold text-emerald-600">&gt;= 15.0%</td>
                <td class="p-3">Return on Equity. Warren Buffett's favorite efficiency metric! Measures how effectively management generates profits on shareholder equity.</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">Net Margin (%)</td>
                <td class="p-3 text-[var(--muted-foreground)]">Percentage</td>
                <td class="p-3 font-mono text-[11px]">Net Profit / Total Revenue * 100</td>
                <td class="p-3 font-bold text-emerald-600">&gt;= 10.0%</td>
                <td class="p-3">Net Profit Margin. Percentage of revenue converted into bottom-line profit. High margins signal pricing power and economic moat.</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">Debt/Equity</td>
                <td class="p-3 text-[var(--muted-foreground)]">Ratio</td>
                <td class="p-3 font-mono text-[11px]">Total Debt / Shareholders Equity</td>
                <td class="p-3 font-bold text-emerald-600">&lt;= 0.50</td>
                <td class="p-3">Financial leverage. Low debt ensures business survival during economic downturns and prevents high interest burden.</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">FCF Yield (%)</td>
                <td class="p-3 text-[var(--muted-foreground)]">Percentage</td>
                <td class="p-3 font-mono text-[11px]">Free Cash Flow / Market Cap * 100</td>
                <td class="p-3 font-bold text-emerald-600">&gt;= 5.0%</td>
                <td class="p-3">Free Cash Flow Yield. Real cash earnings available for dividend payouts, share buybacks, or debt repayment.</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">Intrinsic Value (£)</td>
                <td class="p-3 text-[var(--muted-foreground)]">GBP (£)</td>
                <td class="p-3 font-mono text-[11px]">10-Year Discounted FCF Model</td>
                <td class="p-3 font-bold text-emerald-600">&gt; Market Price</td>
                <td class="p-3">Estimated true economic business value per share based on projected owner earnings discounted at 9% hurdle rate.</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">Margin of Safety (%)</td>
                <td class="p-3 text-[var(--muted-foreground)]">Percentage</td>
                <td class="p-3 font-mono text-[11px]">(Intrinsic Value - Price) / Intrinsic Value * 100</td>
                <td class="p-3 font-bold text-emerald-600">&gt;= 20.0%</td>
                <td class="p-3">Benjamin Graham & Warren Buffett's core principle. Buying at a discount protects capital against market downturns or forecast errors.</td>
              </tr>
              <tr class="hover:bg-[var(--background)]/50">
                <td class="p-3 font-bold text-[var(--primary)]">Buffett Score</td>
                <td class="p-3 text-[var(--muted-foreground)]">Points (0-100)</td>
                <td class="p-3 font-mono text-[11px]">=BUFFETTSCORE(...)</td>
                <td class="p-3 font-bold text-emerald-600">&gt;= 75 (Strong Buy)</td>
                <td class="p-3">Composite score summing Moat (25), Financial Health (25), Valuation Multiples (25), and Margin of Safety (25).</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>

  <script>
    const STOCKS_DATA = {json.dumps(stocks_json)};
    const BACKTEST_DATA = {json.dumps(backtest_json)};
    let activeFilter = 'ALL';

    function switchTab(tabName) {{
      document.getElementById('tabScreener').classList.add('hidden');
      document.getElementById('tabTimeSeries').classList.add('hidden');
      document.getElementById('tabDictionary').classList.add('hidden');

      document.getElementById('tabBtnScreener').className = "px-4 py-2 rounded-xl text-xs font-bold bg-[var(--card)] text-[var(--muted-foreground)] border border-[var(--border)] hover:bg-[var(--background)] shadow-sm";
      document.getElementById('tabBtnTimeSeries').className = "px-4 py-2 rounded-xl text-xs font-bold bg-[var(--card)] text-[var(--muted-foreground)] border border-[var(--border)] hover:bg-[var(--background)] shadow-sm";
      document.getElementById('tabBtnDict').className = "px-4 py-2 rounded-xl text-xs font-bold bg-[var(--card)] text-[var(--muted-foreground)] border border-[var(--border)] hover:bg-[var(--background)] shadow-sm";

      if (tabName === 'screener') {{
        document.getElementById('tabScreener').classList.remove('hidden');
        document.getElementById('tabBtnScreener').className = "px-4 py-2 rounded-xl text-xs font-bold bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm";
      }} else if (tabName === 'timeseries') {{
        document.getElementById('tabTimeSeries').classList.remove('hidden');
        document.getElementById('tabBtnTimeSeries').className = "px-4 py-2 rounded-xl text-xs font-bold bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm";
        renderBacktestTable();
      }} else if (tabName === 'dictionary') {{
        document.getElementById('tabDictionary').classList.remove('hidden');
        document.getElementById('tabBtnDict').className = "px-4 py-2 rounded-xl text-xs font-bold bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm";
      }}
    }}

    function filterSignal(sig) {{
      activeFilter = sig;
      renderTable();
    }}

    function renderTable() {{
      const search = document.getElementById('searchInput').value.toLowerCase();
      let filtered = STOCKS_DATA.filter(s => {{
        if (activeFilter !== 'ALL' && s.Signal !== activeFilter) return false;
        if (search) {{
          const t = (s.Ticker || '').toLowerCase();
          const n = (s.Name || '').toLowerCase();
          const sec = (s.Sector || '').toLowerCase();
          if (!t.includes(search) && !n.includes(search) && !sec.includes(search)) return false;
        }}
        return true;
      }});

      filtered.sort((a, b) => (b['Buffett Score'] || 0) - (a['Buffett Score'] || 0));

      const tbody = document.getElementById('stockTableBody');
      tbody.innerHTML = filtered.map(s => {{
        let badgeClass = 'bg-gray-500/10 text-gray-500 border-gray-500/20';
        if (s.Signal === 'STRONG BUY') badgeClass = 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-bold border-emerald-500/30';
        else if (s.Signal === 'BUY') badgeClass = 'bg-green-500/15 text-green-600 dark:text-green-400 font-bold border-green-500/30';
        else if (s.Signal === 'HOLD') badgeClass = 'bg-amber-500/15 text-amber-600 dark:text-amber-400 font-bold border-amber-500/30';
        else if (s.Signal === 'SELL') badgeClass = 'bg-rose-500/15 text-rose-600 dark:text-rose-400 font-bold border-rose-500/30';

        let mosColor = (s['Margin of Safety (%)'] >= 20) ? 'text-emerald-600 font-bold' : (s['Margin of Safety (%)'] >= 0 ? 'text-green-600 font-semibold' : 'text-rose-500');

        return `<tr class="hover:bg-[var(--background)]/50 transition-colors">
          <td class="p-3 font-bold text-[var(--primary)]">${{s.Ticker}}</td>
          <td class="p-3 font-medium max-w-[180px] truncate" title="${{s.Name}}">${{s.Name}}</td>
          <td class="p-3 text-[var(--muted-foreground)] max-w-[140px] truncate">${{s.Sector}}</td>
          <td class="p-3 text-center"><span class="px-2.5 py-1 rounded-md text-[10px] border ${{badgeClass}}">${{s.Signal}}</span></td>
          <td class="p-3 text-right font-bold text-base text-[var(--foreground)]">${{s['Buffett Score']}}</td>
          <td class="p-3 text-right font-medium">£${{s['Price (£)'] !== '' ? Number(s['Price (£)']).toFixed(2) : '-'}}</td>
          <td class="p-3 text-right font-medium">£${{s['Intrinsic Value (£)'] !== '' ? Number(s['Intrinsic Value (£)']).toFixed(2) : '-'}}</td>
          <td class="p-3 text-right ${{mosColor}}">${{s['Margin of Safety (%)'] !== '' ? Number(s['Margin of Safety (%)']).toFixed(1) + '%' : '-'}}</td>
          <td class="p-3 text-right text-[var(--muted-foreground)]">${{s['P/E Ratio'] !== '' ? Number(s['P/E Ratio']).toFixed(1) : '-'}}</td>
          <td class="p-3 text-right text-[var(--muted-foreground)]">${{s['P/B Ratio'] !== '' ? Number(s['P/B Ratio']).toFixed(1) : '-'}}</td>
          <td class="p-3 text-right font-medium">${{s['ROE (%)'] !== '' ? Number(s['ROE (%)']).toFixed(1) + '%' : '-'}}</td>
          <td class="p-3 text-right text-[var(--muted-foreground)]">${{s['Net Margin (%)'] !== '' ? Number(s['Net Margin (%)']).toFixed(1) + '%' : '-'}}</td>
          <td class="p-3 text-right text-[var(--muted-foreground)]">${{s['Debt/Equity'] !== '' ? Number(s['Debt/Equity']).toFixed(2) : '-'}}</td>
          <td class="p-3 text-right font-medium text-emerald-600">${{s['FCF Yield (%)'] !== '' ? Number(s['FCF Yield (%)']).toFixed(1) + '%' : '-'}}</td>
        </tr>`;
      }}).join('');
    }}

    function renderBacktestTable() {{
      const tbody = document.getElementById('backtestTableBody');
      tbody.innerHTML = BACKTEST_DATA.map(b => {{
        let ret1y = b['1Y Return (%)'] !== '' ? Number(b['1Y Return (%)']) : 0;
        let ret3y = b['3Y Return (%)'] !== '' ? Number(b['3Y Return (%)']) : 0;
        let ret5y = b['5Y Return (%)'] !== '' ? Number(b['5Y Return (%)']) : 0;

        let col1y = ret1y >= 0 ? 'text-emerald-600 font-semibold' : 'text-rose-500';
        let col3y = ret3y >= 0 ? 'text-emerald-600 font-bold' : 'text-rose-500';
        let col5y = ret5y >= 0 ? 'text-emerald-600 font-bold' : 'text-rose-500';

        return `<tr class="hover:bg-[var(--background)]/50 transition-colors">
          <td class="p-3 font-bold text-[var(--primary)]">${{b.Ticker}}</td>
          <td class="p-3 font-medium max-w-[180px] truncate">${{b.Name}}</td>
          <td class="p-3 text-center"><span class="px-2 py-0.5 rounded text-[10px] bg-gray-500/10">${{b['Current Signal'] || 'HOLD'}}</span></td>
          <td class="p-3 text-right font-bold">${{b['Buffett Score Today'] || '-'}}</td>
          <td class="p-3 text-right">£${{b['Current Price (£)'] !== '' ? Number(b['Current Price (£)']).toFixed(2) : '-'}}</td>
          <td class="p-3 text-right text-[var(--muted-foreground)]">£${{b['Price 1Y Ago (£)'] !== '' ? Number(b['Price 1Y Ago (£)']).toFixed(2) : '-'}}</td>
          <td class="p-3 text-right text-[var(--muted-foreground)]">£${{b['Price 3Y Ago (£)'] !== '' ? Number(b['Price 3Y Ago (£)']).toFixed(2) : '-'}}</td>
          <td class="p-3 text-right text-[var(--muted-foreground)]">£${{b['Price 5Y Ago (£)'] !== '' ? Number(b['Price 5Y Ago (£)']).toFixed(2) : '-'}}</td>
          <td class="p-3 text-right ${{col1y}}">${{ret1y >= 0 ? '+' : ''}}${{ret1y.toFixed(1)}}%</td>
          <td class="p-3 text-right ${{col3y}}">${{ret3y >= 0 ? '+' : ''}}${{ret3y.toFixed(1)}}%</td>
          <td class="p-3 text-right ${{col5y}}">${{ret5y >= 0 ? '+' : ''}}${{ret5y.toFixed(1)}}%</td>
        </tr>`;
      }}).join('');
    }}

    renderTable();
  </script>
</body>
</html>"""

out_path = '/Users/harleycole/.gemini/antigravity/brain/cff130ee-8a8d-47d3-bf51-18401d5957bd/ftse100_spreadsheet_viewer.html'
with open(out_path, 'w') as f:
    f.write(html_content)

print(f"Updated HTML artifact successfully at: {out_path}")

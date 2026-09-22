/**
 * Google Apps Script for FTSE 100 Warren Buffett Value Investing Screener
 * Paste this into Google Sheets via: Extensions -> Apps Script
 */

/**
 * Custom Menu on Google Sheet open
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('FTSE 100 Value Tools')
    .addItem('Apply Buy/Hold/Sell Color Formatting', 'applyColorFormatting')
    .addItem('Recalculate Summary Statistics', 'recalculateSummaryStats')
    .addToUi();
}

/**
 * Custom Formula: Calculates Warren Buffett Value Score (0 to 100)
 * Usage in Google Sheet cell: =BUFFETTSCORE(E2, F2, G2, H2, I2, J2)
 *
 * @param {number} pe P/E Ratio
 * @param {number} roe Return on Equity (%) e.g. 18 for 18%
 * @param {number} netMargin Net Profit Margin (%) e.g. 12 for 12%
 * @param {number} debtEquity Debt to Equity Ratio e.g. 0.45
 * @param {number} fcfYield Free Cash Flow Yield (%) e.g. 6.5 for 6.5%
 * @param {number} marginOfSafety Margin of Safety (%) from DCF e.g. 25 for 25%
 * @return {number} Composite Buffett Score (0-100)
 * @customfunction
 */
function BUFFETTSCORE(pe, roe, netMargin, debtEquity, fcfYield, marginOfSafety) {
  var score = 0;

  // 1. Quality & Moat (Max 25 pts)
  if (roe >= 20) score += 10;
  else if (roe >= 15) score += 8;
  else if (roe >= 10) score += 5;

  if (netMargin >= 15) score += 8;
  else if (netMargin >= 10) score += 6;
  else if (netMargin >= 5) score += 3;

  score += 7; // Op margin baseline

  // 2. Financial Strength (Max 25 pts)
  if (debtEquity <= 0.3) score += 12;
  else if (debtEquity <= 0.6) score += 9;
  else if (debtEquity <= 1.0) score += 5;

  score += 13; // Liquidity baseline

  // 3. Valuation Multiples (Max 25 pts)
  if (pe > 0 && pe <= 12) score += 10;
  else if (pe > 0 && pe <= 16) score += 8;
  else if (pe > 0 && pe <= 20) score += 5;

  if (fcfYield >= 8) score += 15;
  else if (fcfYield >= 5) score += 10;
  else if (fcfYield >= 3) score += 5;

  // 4. Margin of Safety (Max 25 pts)
  if (marginOfSafety >= 30) score += 25;
  else if (marginOfSafety >= 20) score += 20;
  else if (marginOfSafety >= 10) score += 15;
  else if (marginOfSafety >= 0) score += 10;

  return Math.min(100, Math.max(0, Math.round(score)));
}

/**
 * Custom Formula: Returns Signal based on Buffett Score and Margin of Safety
 * Usage: =BUFFETTSIGNAL(B2, H2)
 * @customfunction
 */
function BUFFETTSIGNAL(score, marginOfSafety) {
  if (score >= 75 && marginOfSafety >= 15) return 'STRONG BUY';
  if (score >= 62 && marginOfSafety >= 0) return 'BUY';
  if (score >= 48) return 'HOLD';
  return 'SELL';
}

/**
 * Automatically applies color conditional formatting to Signal column
 */
function applyColorFormatting() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var range = sheet.getDataRange();
  var values = range.getValues();

  var signalColIdx = -1;
  for (var c = 0; c < values[0].length; c++) {
    if (values[0][c].toString().trim().toUpperCase() === 'SIGNAL') {
      signalColIdx = c;
      break;
    }
  }

  if (signalColIdx === -1) {
    SpreadsheetApp.getUi().alert('Could not find a header named "Signal" in the active sheet.');
    return;
  }

  for (var r = 1; r < values.length; r++) {
    var cell = sheet.getRange(r + 1, signalColIdx + 1);
    var signalVal = values[r][signalColIdx].toString().trim().toUpperCase();

    if (signalVal === 'STRONG BUY' || signalVal === 'BUY') {
      cell.setBackground('#D4EDDA').setFontColor('#155724').setFontWeight('bold');
    } else if (signalVal === 'HOLD') {
      cell.setBackground('#FFF3CD').setFontColor('#856404').setFontWeight('bold');
    } else if (signalVal === 'SELL' || signalVal === 'SELL / OVERVALUED') {
      cell.setBackground('#F8D7DA').setFontColor('#721C24').setFontWeight('bold');
    }
  }

  SpreadsheetApp.getUi().alert('Buy/Hold/Sell signals successfully formatted!');
}


#!/usr/bin/env python3
"""ETF 자산배분 모델용 데이터 수집 파이프라인"""

import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, date
from pathlib import Path

OUT = Path(__file__).parent
START = "2005-01-01"
END = datetime.now().strftime("%Y-%m-%d")

# ── 1. ETF 메타데이터 ──
ETF_META = {
    "SPY": {"asset_class": "Equity", "region": "US", "sector": "Large Cap"},
    "QQQ": {"asset_class": "Equity", "region": "US", "sector": "Tech/Growth"},
    "IWM": {"asset_class": "Equity", "region": "US", "sector": "Small Cap"},
    "EFA": {"asset_class": "Equity", "region": "Developed ex-US", "sector": "Broad"},
    "VEA": {"asset_class": "Equity", "region": "Developed ex-US", "sector": "Broad"},
    "VWO": {"asset_class": "Equity", "region": "Emerging", "sector": "Broad"},
    "EEM": {"asset_class": "Equity", "region": "Emerging", "sector": "Broad"},
    "TLT": {"asset_class": "Fixed Income", "region": "US", "sector": "Long-Term Treasury"},
    "IEF": {"asset_class": "Fixed Income", "region": "US", "sector": "Mid-Term Treasury"},
    "SHY": {"asset_class": "Fixed Income", "region": "US", "sector": "Short-Term Treasury"},
    "TIP": {"asset_class": "Fixed Income", "region": "US", "sector": "TIPS"},
    "HYG": {"asset_class": "Fixed Income", "region": "US", "sector": "High Yield"},
    "GLD": {"asset_class": "Commodity", "region": "Global", "sector": "Gold"},
    "DBC": {"asset_class": "Commodity", "region": "Global", "sector": "Broad Commodity"},
    "USO": {"asset_class": "Commodity", "region": "Global", "sector": "Crude Oil"},
    "VNQ": {"asset_class": "Real Estate", "region": "US", "sector": "REITs"},
    "UUP": {"asset_class": "Currency", "region": "US", "sector": "Dollar Index"},
}

MACRO_TICKERS = {"^VIX": "VIX"}  # yfinance 대체 매크로

FRED_SERIES = {
    "FEDFUNDS": "Fed Funds Rate",
    "DGS10": "10Y Treasury",
    "DGS2": "2Y Treasury",
    "T10Y2Y": "10Y-2Y Spread",
    "CPIAUCSL": "CPI",
    "T10YIE": "Breakeven Inflation 10Y",
    "MANEMP": "Manufacturing Employment",
    "UNRATE": "Unemployment Rate",
    "ICSA": "Initial Jobless Claims",
    "GDP": "GDP",
    "M2SL": "M2 Money Supply",
}


def collect_etf():
    """ETF 일봉 데이터 수집"""
    tickers = list(ETF_META.keys())
    print(f"Downloading ETF data for {len(tickers)} tickers...")
    raw = yf.download(tickers, start=START, end=END, auto_adjust=False, group_by="ticker", threads=True)

    frames = []
    for t in tickers:
        try:
            if len(tickers) == 1:
                df = raw.copy()
            else:
                df = raw[t].copy()
            df = df.dropna(how="all")
            if df.empty:
                print(f"  ⚠ {t}: no data")
                continue
            # Flatten MultiIndex columns if needed
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            df["ticker"] = t
            df.index.name = "date"
            # log returns on Adj Close
            adj_col = [c for c in df.columns if "adj" in c.lower() or c == "Adj Close"]
            if adj_col:
                df["log_return"] = np.log(df[adj_col[0]] / df[adj_col[0]].shift(1))
            frames.append(df.reset_index())
            print(f"  ✓ {t}: {len(df)} rows, {df.index.min().date()} ~ {df.index.max().date()}")
        except Exception as e:
            print(f"  ✗ {t}: {e}")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.set_index(["date", "ticker"]).sort_index()
    combined.to_parquet(OUT / "etf_daily.parquet")
    print(f"ETF data saved: {len(combined)} rows\n")
    return combined


def collect_macro():
    """매크로 데이터 수집 (FRED via pandas-datareader, fallback yfinance)"""
    frames = {}

    # Try FRED via pandas-datareader
    try:
        from pandas_datareader import data as pdr
        for code, name in FRED_SERIES.items():
            try:
                s = pdr.DataReader(code, "fred", START, END)
                s = s.iloc[:, 0]
                s.name = code
                frames[code] = s
                print(f"  ✓ FRED {code}: {len(s)} rows")
            except Exception as e:
                print(f"  ✗ FRED {code}: {e}")
    except ImportError:
        print("  pandas-datareader not available, skipping FRED")

    # VIX via yfinance
    for ticker, name in MACRO_TICKERS.items():
        try:
            df = yf.download(ticker, start=START, end=END, auto_adjust=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            s = df["Close"]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            s.name = name
            frames[name] = s
            print(f"  ✓ {name}: {len(s)} rows")
        except Exception as e:
            print(f"  ✗ {name}: {e}")

    if not frames:
        print("No macro data collected!")
        return pd.DataFrame()

    macro = pd.DataFrame(frames)
    macro.index.name = "date"
    # Resample everything to daily, ffill then bfill
    macro = macro.asfreq("B")  # business day
    macro = macro.ffill().bfill()
    macro.to_parquet(OUT / "macro_daily.parquet")
    print(f"Macro data saved: {macro.shape}\n")
    return macro


def save_metadata():
    with open(OUT / "etf_metadata.json", "w") as f:
        json.dump(ETF_META, f, indent=2, ensure_ascii=False)
    print("Metadata saved.\n")


def write_summary(etf_df, macro_df):
    lines = ["# 데이터 수집 결과 요약\n"]
    lines.append(f"수집일시: {datetime.now().isoformat()}\n")

    # ETF summary
    lines.append("## ETF 일봉 데이터\n")
    if not etf_df.empty:
        tickers = etf_df.index.get_level_values("ticker").unique()
        lines.append(f"- 종목수: {len(tickers)}")
        dates = etf_df.index.get_level_values("date")
        lines.append(f"- 기간: {dates.min().date()} ~ {dates.max().date()}")
        lines.append(f"- 총 행수: {len(etf_df):,}")
        missing = etf_df.isnull().sum()
        lines.append(f"- 결측치:\n")
        for col in missing.index:
            if missing[col] > 0:
                lines.append(f"  - {col}: {missing[col]:,}")
        lines.append("")
        lines.append("| Ticker | Rows | Start | End |")
        lines.append("|--------|------|-------|-----|")
        for t in sorted(tickers):
            sub = etf_df.loc[(slice(None), t), :]
            d = sub.index.get_level_values("date")
            lines.append(f"| {t} | {len(sub):,} | {d.min().date()} | {d.max().date()} |")
    lines.append("")

    # Macro summary
    lines.append("## 매크로 데이터\n")
    if not macro_df.empty:
        lines.append(f"- 지표수: {len(macro_df.columns)}")
        lines.append(f"- 기간: {macro_df.index.min().date()} ~ {macro_df.index.max().date()}")
        lines.append(f"- 결측치 (ffill/bfill 후):\n")
        for col in macro_df.columns:
            n = macro_df[col].isnull().sum()
            lines.append(f"  - {col}: {n}")

    summary = "\n".join(lines)
    (OUT / "data_summary.md").write_text(summary)
    print("Summary saved.")


if __name__ == "__main__":
    save_metadata()
    etf_df = collect_etf()
    macro_df = collect_macro()
    write_summary(etf_df, macro_df)
    print("\n✅ Done!")

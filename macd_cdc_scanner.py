"""
JTS MACD+CDC Scanner v3.0
สแกน 100 หุ้น SET บน Monthly timeframe
Logic ผ่อนลง:
  BUY  = MACD zone<0 + MACD cross up + histogram ชมพู→เขียว + EMA12 > EMA26
  SELL = MACD zone>0 + MACD cross down + histogram เขียวอ่อน→แดง + EMA12 < EMA26
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────
WEBHOOK_URL = "https://n8n.jupetor-cmms.com/webhook/tradingview-jts"
TIMEFRAME   = "1mo"
PERIOD      = "10y"

# ─── 100 หุ้น SET (อัปเดตแล้ว) ───────────────────────────
STOCKS = [
    "PTT.BK",    "AOT.BK",    "CPALL.BK",  "SCB.BK",    "KBANK.BK",
    "BBL.BK",    "KTB.BK",    "BAY.BK",    "TTB.BK",    "TISCO.BK",
    "SCC.BK",    "SCCC.BK",   "TBSP.BK",   "TPIPL.BK",  "PTTEP.BK",
    "PTTGC.BK",  "TOP.BK",    "IRPC.BK",   "BCP.BK",    "GULF.BK",
    "GPSC.BK",   "EGCO.BK",   "RATCH.BK",  "BGRIM.BK",  "CPN.BK",
    "CRC.BK",    "BJC.BK",    "HMPRO.BK",  "MINT.BK",   "ERW.BK",
    "CENTEL.BK", "SHR.BK",    "AWC.BK",    "TRUE.BK",   "ADVANC.BK",
    "JAS.BK",    "BH.BK",     "BCH.BK",    "CHG.BK",    "NTV.BK",
    "CPF.BK",    "TU.BK",     "BTG.BK",    "GFPT.BK",   "NRF.BK",
    "BEM.BK",    "BTS.BK",    "CK.BK",     "ITD.BK",    "WHA.BK",
    "AMATA.BK",  "ROJNA.BK",  "LH.BK",     "AP.BK",     "QH.BK",
    "SIRI.BK",   "ORI.BK",    "OSP.BK",    "SAPPE.BK",  "CBG.BK",
    "ICHI.BK",   "OISHI.BK",  "KCE.BK",    "DELTA.BK",  "HANA.BK",
    "SVI.BK",    "IVL.BK",    "SAWAD.BK",  "MTC.BK",    "TIDLOR.BK",
    "AEONTS.BK", "KTC.BK",    "BEAUTY.BK", "MALEE.BK",  "TKN.BK",
    "TNP.BK",    "JMART.BK",  "SPALI.BK",  "PSH.BK",    "SC.BK",
    "NOBLE.BK",  "BANPU.BK",  "STA.BK",    "NCH.BK",    "PYLON.BK",
    "GLOBAL.BK", "MAJOR.BK",  "RS.BK",     "VGI.BK",    "WORK.BK",
    "TQM.BK",    "THCOM.BK",  "INSET.BK",  "DIF.BK",    "JASIF.BK",
    "INTUCH.BK", "SINGER.BK", "SECURE.BK", "BE8.BK",    "MFEC.BK",
]

# ─── EMA ──────────────────────────────────────────────────
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

# ─── MACD ─────────────────────────────────────────────────
def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast    = ema(close, fast)
    ema_slow    = ema(close, slow)
    macd_line   = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram

# ─── Scan ─────────────────────────────────────────────────
def scan_history(df):
    close = df["Close"].squeeze()
    if len(close) < 30:
        return None, None, None

    fast_ema  = ema(close, 12)
    slow_ema  = ema(close, 26)
    macd_line, signal_line, hist = calc_macd(close)

    current_position = "NONE"
    last_signal_date = None
    new_signal       = None

    bars = len(close)

    for i in range(2, bars):
        m   = macd_line.iloc[i]
        s   = signal_line.iloc[i]
        h   = hist.iloc[i]
        h1  = hist.iloc[i - 1]
        h2  = hist.iloc[i - 2]
        pm  = macd_line.iloc[i - 1]
        ps  = signal_line.iloc[i - 1]
        f   = fast_ema.iloc[i]
        sl  = slow_ema.iloc[i]

        zone_bear = m < 0 and s < 0
        zone_bull = m > 0 and s > 0

        macd_cross_up   = pm <= ps and m > s
        macd_cross_down = pm >= ps and m < s

        is_green       = h > 0 and h > h1
        is_red         = h < 0 and h < h1

        pink_to_green = (h1 < 0 and h1 > h2) and is_green
        light_to_red  = (h1 > 0 and h1 < h2) and is_red

        cdc_bull = f > sl   # EMA12 > EMA26
        cdc_bear = f < sl   # EMA12 < EMA26

        # ── BUY ──
        # MACD zone<0 + cross up + ชมพู→เขียว + EMA12 > EMA26
        if zone_bear and macd_cross_up and pink_to_green and cdc_bull:
            current_position = "BUY"
            last_signal_date = df.index[i]
            if i == bars - 1:
                new_signal = "BUY"

        # ── SELL ──
        # MACD zone>0 + cross down + เขียวอ่อน→แดง + EMA12 < EMA26
        if zone_bull and macd_cross_down and light_to_red and cdc_bear:
            current_position = "SELL"
            last_signal_date = df.index[i]
            if i == bars - 1:
                new_signal = "SELL"

    return current_position, last_signal_date, new_signal

# ─── ส่ง Webhook ──────────────────────────────────────────
def send_webhook(symbol, signal, price, last_date):
    name  = symbol.replace(".BK", "")
    emoji = "✅" if signal == "BUY" else "🔴"
    payload = {
        "symbol":  name,
        "signal":  signal,
        "price":   round(price, 2),
        "message": (
            f"{emoji} {signal} — {name}\n"
            f"ราคา: {round(price, 2)} บาท\n"
            f"Timeframe: Monthly\n"
            f"สัญญาณล่าสุด: {last_date.strftime('%m/%Y') if last_date else '-'}\n"
            f"เวลา: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print(f"    → webhook: {r.status_code}")
    except Exception as e:
        print(f"    → webhook error: {e}")

# ─── Main ──────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  JTS MACD+CDC Scanner v3.0 — Monthly")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*60}\n")

    results = []

    for i, symbol in enumerate(STOCKS, 1):
        print(f"[{i:3d}/{len(STOCKS)}] {symbol:<15}", end=" ")
        try:
            df = yf.download(symbol, period=PERIOD, interval=TIMEFRAME,
                             progress=False, auto_adjust=True)

            if df.empty or len(df) < 30:
                print("⚠️  ข้อมูลน้อย")
                continue

            position, last_date, new_signal = scan_history(df)
            price = float(df["Close"].iloc[-1].squeeze() if hasattr(df["Close"].iloc[-1], 'squeeze') else df["Close"].iloc[-1])

            icon     = "🟢" if position == "BUY" else "🔴" if position == "SELL" else "⬜"
            new      = " ← ใหม่!" if new_signal else ""
            date_str = last_date.strftime("%m/%Y") if last_date else "-"

            print(f"{icon} {position:<5} (ล่าสุด: {date_str}){new}")

            results.append({
                "symbol":   symbol.replace(".BK", ""),
                "position": position,
                "date":     date_str,
                "price":    round(price, 2),
                "new":      bool(new_signal)
            })

            if new_signal:
                send_webhook(symbol, new_signal, price, last_date)

        except Exception as e:
            print(f"❌ {e}")

    # ─── สรุป ───
    print(f"\n{'='*60}")
    print(f"  สรุปสถานะปัจจุบัน")
    print(f"{'='*60}")

    buy_list  = [r for r in results if r["position"] == "BUY"]
    sell_list = [r for r in results if r["position"] == "SELL"]
    new_list  = [r for r in results if r["new"]]

    print(f"\n🟢 BUY  ({len(buy_list)} ตัว):")
    for r in buy_list:
        new = " ← ใหม่!" if r["new"] else ""
        print(f"   {r['symbol']:<12} ราคา {r['price']:>8.2f}  (สัญญาณ: {r['date']}){new}")

    print(f"\n🔴 SELL ({len(sell_list)} ตัว):")
    for r in sell_list:
        new = " ← ใหม่!" if r["new"] else ""
        print(f"   {r['symbol']:<12} ราคา {r['price']:>8.2f}  (สัญญาณ: {r['date']}){new}")

    print(f"\n⚡ สัญญาณใหม่เดือนนี้ ({len(new_list)} ตัว):")
    for r in new_list:
        icon = "🟢" if r["position"] == "BUY" else "🔴"
        print(f"   {icon} {r['symbol']:<12} {r['position']}  ราคา {r['price']:>8.2f}")

    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()

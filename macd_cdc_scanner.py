"""
JTS MACD+CDC Scanner v4.0
BUY  = MACD zone<0 + EMA12 > EMA26
SELL = MACD zone>0 + EMA12 < EMA26
(ผ่อนมากเพื่อ debug ก่อน)
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

WEBHOOK_URL = "https://n8n.jupetor-cmms.com/webhook/tradingview-jts"
TIMEFRAME   = "1mo"
PERIOD      = "10y"

STOCKS = [
    "PTT.BK",    "AOT.BK",    "CPALL.BK",  "SCB.BK",    "KBANK.BK",
    "BBL.BK",    "KTB.BK",    "BAY.BK",    "TTB.BK",    "TISCO.BK",
    "SCC.BK",    "SCCC.BK",   "TBSP.BK",   "TPIPL.BK",  "PTTEP.BK",
    "PTTGC.BK",  "TOP.BK",    "IRPC.BK",   "BCP.BK",    "GULF.BK",
    "GPSC.BK",   "EGCO.BK",   "RATCH.BK",  "BGRIM.BK",  "CPN.BK",
    "CRC.BK",    "BJC.BK",    "HMPRO.BK",  "MINT.BK",   "ERW.BK",
    "CENTEL.BK", "AWC.BK",    "TRUE.BK",   "ADVANC.BK", "JAS.BK",
    "BH.BK",     "BCH.BK",    "CHG.BK",    "CPF.BK",    "TU.BK",
    "BTG.BK",    "GFPT.BK",   "BEM.BK",    "BTS.BK",    "CK.BK",
    "WHA.BK",    "AMATA.BK",  "LH.BK",     "AP.BK",     "QH.BK",
    "SIRI.BK",   "ORI.BK",    "OSP.BK",    "CBG.BK",    "ICHI.BK",
    "KCE.BK",    "DELTA.BK",  "HANA.BK",   "SVI.BK",    "IVL.BK",
    "SAWAD.BK",  "MTC.BK",    "TIDLOR.BK", "AEONTS.BK", "KTC.BK",
    "MALEE.BK",  "TKN.BK",    "JMART.BK",  "SPALI.BK",  "PSH.BK",
    "SC.BK",     "BANPU.BK",  "STA.BK",    "PYLON.BK",  "GLOBAL.BK",
    "MAJOR.BK",  "RS.BK",     "VGI.BK",    "TQM.BK",    "DIF.BK",
    "JASIF.BK",  "SINGER.BK", "BE8.BK",    "MFEC.BK",   "NRF.BK",
    "SAPPE.BK",  "OISHI.BK",  "TNP.BK",    "NCH.BK",    "NOBLE.BK",
    "BEAUTY.BK", "ROJNA.BK",  "BGRIM.BK",  "SECURE.BK", "WORK.BK",
    "INSET.BK",  "THCOM.BK",  "ITD.BK",    "NTV.BK",    "INTUCH.BK",
]

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_macd(close):
    ema12 = ema(close, 12)
    ema26 = ema(close, 26)
    macd  = ema12 - ema26
    sig   = ema(macd, 9)
    hist  = macd - sig
    return macd, sig, hist

def scan(df):
    close = df["Close"].squeeze()
    if len(close) < 30:
        return None, None, None

    fast = ema(close, 12)
    slow = ema(close, 26)
    macd_line, sig_line, hist = calc_macd(close)

    position = "NONE"
    last_date = None
    new_signal = None
    bars = len(close)

    for i in range(2, bars):
        m  = macd_line.iloc[i]
        s  = sig_line.iloc[i]
        h  = hist.iloc[i]
        h1 = hist.iloc[i-1]
        h2 = hist.iloc[i-2]
        pm = macd_line.iloc[i-1]
        ps = sig_line.iloc[i-1]
        f  = fast.iloc[i]
        sl = slow.iloc[i]

        zone_bear = m < 0 and s < 0
        zone_bull = m > 0 and s > 0
        cross_up   = pm <= ps and m > s
        cross_down = pm >= ps and m < s
        pink_to_green = (h1 < 0 and h1 > h2) and (h > 0 and h > h1)
        light_to_red  = (h1 > 0 and h1 < h2) and (h < 0 and h < h1)
        cdc_bull = f > sl
        cdc_bear = f < sl

        # BUY: zone<0 + cross up + ชมพู→เขียว + cdc bull
        if zone_bear and cross_up and pink_to_green and cdc_bull:
            position  = "BUY"
            last_date = df.index[i]
            new_signal = "BUY" if i == bars-1 else None

        # SELL: zone>0 + cross down + เขียวอ่อน→แดง + cdc bear
        elif zone_bull and cross_down and light_to_red and cdc_bear:
            position  = "SELL"
            last_date = df.index[i]
            new_signal = "SELL" if i == bars-1 else None

        # ── debug: แสดง partial match ──
        if i == bars-1:
            matches = []
            if zone_bear: matches.append("zone<0")
            if zone_bull: matches.append("zone>0")
            if cross_up:  matches.append("crossUp")
            if cross_down: matches.append("crossDown")
            if pink_to_green: matches.append("pink→green")
            if light_to_red:  matches.append("green→red")
            if cdc_bull: matches.append("cdcBull")
            if cdc_bear: matches.append("cdcBear")
            if matches:
                print(f"      debug: {', '.join(matches)}")

    return position, last_date, new_signal

def send_webhook(symbol, signal, price, last_date):
    name  = symbol.replace(".BK", "")
    emoji = "✅" if signal == "BUY" else "🔴"
    payload = {
        "symbol": name, "signal": signal, "price": round(price, 2),
        "message": (
            f"{emoji} {signal} — {name}\n"
            f"ราคา: {round(price, 2)} บาท\n"
            f"Timeframe: Monthly\n"
            f"สัญญาณ: {last_date.strftime('%m/%Y') if last_date else '-'}\n"
            f"เวลา: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print(f"    → webhook: {r.status_code}")
    except Exception as e:
        print(f"    → webhook error: {e}")

def main():
    print(f"\n{'='*60}")
    print(f"  JTS MACD+CDC Scanner v4.0 — Monthly")
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

            position, last_date, new_signal = scan(df)
            price    = float(df["Close"].iloc[-1].item() if hasattr(df["Close"].iloc[-1], 'item') else df["Close"].iloc[-1])
            icon     = "🟢" if position == "BUY" else "🔴" if position == "SELL" else "⬜"
            date_str = last_date.strftime("%m/%Y") if last_date else "-"
            new      = " ← ใหม่!" if new_signal else ""

            print(f"{icon} {str(position):<5} (ล่าสุด: {date_str}){new}")
            results.append({"symbol": symbol.replace(".BK",""), "position": position,
                            "date": date_str, "price": round(price,2), "new": bool(new_signal)})
            if new_signal:
                send_webhook(symbol, new_signal, price, last_date)

        except Exception as e:
            print(f"❌ {e}")

    print(f"\n{'='*60}")
    print(f"  สรุปสถานะปัจจุบัน")
    print(f"{'='*60}")
    buy_list  = [r for r in results if r["position"] == "BUY"]
    sell_list = [r for r in results if r["position"] == "SELL"]
    new_list  = [r for r in results if r["new"]]

    print(f"\n🟢 BUY  ({len(buy_list)} ตัว):")
    for r in buy_list:
        print(f"   {r['symbol']:<12} ราคา {r['price']:>8.2f}  ({r['date']}){' ← ใหม่!' if r['new'] else ''}")

    print(f"\n🔴 SELL ({len(sell_list)} ตัว):")
    for r in sell_list:
        print(f"   {r['symbol']:<12} ราคา {r['price']:>8.2f}  ({r['date']}){' ← ใหม่!' if r['new'] else ''}")

    print(f"\n⚡ สัญญาณใหม่เดือนนี้ ({len(new_list)} ตัว):")
    for r in new_list:
        icon = "🟢" if r["position"] == "BUY" else "🔴"
        print(f"   {icon} {r['symbol']:<12} {r['position']}  ราคา {r['price']:>8.2f}")

    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()

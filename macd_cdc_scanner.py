"""
JTS MACD Scanner v5.0
BUY  = MACD zone<0 + MACD cross up + histogram ชมพู→เขียว
SELL = MACD zone>0 + MACD cross down + histogram เขียวอ่อน→แดง
"""

import yfinance as yf
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
    "BEAUTY.BK", "ROJNA.BK",  "SECURE.BK", "WORK.BK",   "INSET.BK",
    "THCOM.BK",  "ITD.BK",    "NTV.BK",    "OSP.BK",    "BGRIM.BK",
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

    macd_line, sig_line, hist = calc_macd(close)

    position  = "NONE"
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

        zone_bear = m < 0 and s < 0
        zone_bull = m > 0 and s > 0
        cross_up   = pm <= ps and m > s
        cross_down = pm >= ps and m < s

        # ชมพู = hist<0 และกำลังดีขึ้น
        # เขียว = hist>0 และกำลังเพิ่ม
        pink_to_green = (h1 < 0 and h1 > h2) and (h > 0 and h > h1)

        # เขียวอ่อน = hist>0 และกำลังลด
        # แดง = hist<0 และกำลังลด
        light_to_red = (h1 > 0 and h1 < h2) and (h < 0 and h < h1)

        # BUY = zone<0 + cross up + ชมพู→เขียว
        if zone_bear and cross_up and pink_to_green:
            position  = "BUY"
            last_date = df.index[i]
            if i == bars - 1:
                new_signal = "BUY"

        # SELL = zone>0 + cross down + เขียวอ่อน→แดง
        elif zone_bull and cross_down and light_to_red:
            position  = "SELL"
            last_date = df.index[i]
            if i == bars - 1:
                new_signal = "SELL"

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
    print(f"  JTS MACD Scanner v5.0 — Monthly")
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
            price    = float(df["Close"].iloc[-1].item())
            icon     = "🟢" if position == "BUY" else "🔴" if position == "SELL" else "⬜"
            date_str = last_date.strftime("%m/%Y") if last_date else "-"
            new      = " ← ใหม่!" if new_signal else ""

            print(f"{icon} {str(position):<5} (ล่าสุด: {date_str}){new}")
            results.append({"symbol": symbol.replace(".BK",""), "position": position,
                            "date": date_str, "price": round(price,2), "new": bool(new_signal)})
            
        if position == "BUY" or position == "SELL":
              send_webhook(symbol, position, price, last_date)

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

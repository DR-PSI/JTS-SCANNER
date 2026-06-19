"""
JTS MACD Scanner v7.0
กรองหุ้นที่ momentum กำลังกลับตัว
SET100 + MAI รวม ~300 ตัว
"""

import yfinance as yf
import requests
import json
from datetime import datetime, timezone, timedelta

WEBHOOK_URL      = "https://n8n.jupetor-cmms.com/webhook/tradingview-jts"
WEBHOOK_SAVE_URL = "https://n8n.jupetor-cmms.com/webhook/scanner-save"
TIMEFRAME        = "1mo"
PERIOD           = "10y"
THAI_TZ          = timezone(timedelta(hours=7))

# ── SET100 (~150 ตัว) ──────────────────────────────────────
SET100 = [
    # กลุ่มพลังงาน
    "PTT.BK","PTTEP.BK","PTTGC.BK","TOP.BK","IRPC.BK","BCP.BK",
    "GULF.BK","GPSC.BK","EGCO.BK","RATCH.BK","BGRIM.BK","BANPU.BK",
    "CK.BK","STEC.BK",
    # กลุ่มธนาคาร
    "SCB.BK","KBANK.BK","BBL.BK","KTB.BK","BAY.BK","TTB.BK",
    "TISCO.BK","KKP.BK","TCAP.BK",
    # กลุ่มค้าปลีก
    "CPALL.BK","CRC.BK","BJC.BK","HMPRO.BK","ROBINS.BK","COM7.BK",
    "DOHOME.BK","GLOBAL.BK","MAKRO.BK",
    # กลุ่มอาหาร
    "CPF.BK","TU.BK","BTG.BK","GFPT.BK","OSP.BK","CBG.BK",
    "ICHI.BK","OISHI.BK","SAPPE.BK","MALEE.BK","TKN.BK","NRF.BK",
    # กลุ่มอสังหา
    "LH.BK","AP.BK","QH.BK","SIRI.BK","ORI.BK","SPALI.BK",
    "PSH.BK","SC.BK","NOBLE.BK","PLUS.BK","ANAN.BK","PRUKSA.BK",
    # กลุ่มสุขภาพ
    "BH.BK","BCH.BK","CHG.BK","NTV.BK","BDMS.BK","PR9.BK",
    "RJH.BK","RAM.BK","SKR.BK",
    # กลุ่มสื่อสาร
    "ADVANC.BK","TRUE.BK","INTUCH.BK","JAS.BK","THCOM.BK",
    "DIF.BK","JASIF.BK","INSET.BK",
    # กลุ่มท่องเที่ยว
    "AOT.BK","MINT.BK","ERW.BK","CENTEL.BK","SHR.BK","AWC.BK",
    "MAJOR.BK","RS.BK","VGI.BK",
    # กลุ่มอุตสาหกรรม
    "SCC.BK","SCCC.BK","TBSP.BK","TPIPL.BK","IVL.BK","TPI.BK",
    "IRPC.BK","HMC.BK","STA.BK",
    # กลุ่มเทคโนโลยี
    "DELTA.BK","KCE.BK","HANA.BK","SVI.BK","BE8.BK","MFEC.BK",
    "WORK.BK","INSET.BK","SECURE.BK",
    # กลุ่มการเงิน
    "SAWAD.BK","MTC.BK","TIDLOR.BK","AEONTS.BK","KTC.BK",
    "TQM.BK","SINGER.BK","JMART.BK","JMT.BK",
    # กลุ่มนิคม/โลจิสติกส์
    "WHA.BK","AMATA.BK","ROJNA.BK","BEM.BK","BTS.BK",
    "WHART.BK","FTREIT.BK",
    # กลุ่มอื่นๆ
    "PTT.BK","CPN.BK","BBL.BK","BEAUTY.BK","TNP.BK","NCH.BK",
    "PYLON.BK","ITD.BK","NTV.BK","NOBLE.BK","SVI.BK","IVL.BK",
]

# ── MAI (~150 ตัว) ─────────────────────────────────────────
MAI = [
    # กลุ่มเทคโนโลยี/IT
    "SYNEX.BK","SVOA.BK","SIS.BK","INET.BK","ITEL.BK",
    "FORTH.BK","FPI.BK","AQUA.BK","AIT.BK","ADVICE.BK",
    # กลุ่มสุขภาพ
    "EKH.BK","LPH.BK","VIBHA.BK","WPH.BK","NEW.BK",
    "PRINC.BK","ABSOLUTE.BK","DELTA.BK",
    # กลุ่มอาหาร/เครื่องดื่ม
    "KAMART.BK","SABUY.BK","GEL.BK","EVER.BK","YUASA.BK",
    "MILL.BK","CPL.BK","CFRESH.BK","ASIAN.BK","SORKON.BK",
    # กลุ่มอสังหา/ก่อสร้าง
    "RICHY.BK","LDC.BK","MC.BK","FANCY.BK","MONO.BK",
    "SISB.BK","EARTH.BK","MASTER.BK","TIGER.BK","CITY.BK",
    # กลุ่มพลังงาน
    "BCPG.BK","SUPER.BK","SOLAR.BK","TPCH.BK","TSE.BK",
    "SPCG.BK","ACE.BK","GUNKUL.BK","PPS.BK","SKE.BK",
    # กลุ่มค้าปลีก/บริการ
    "MEGA.BK","BEAUTY.BK","KEBSIAM.BK","M.BK","NPK.BK",
    "OCC.BK","PAP.BK","PPM.BK","PDI.BK","PCSGH.BK",
    # กลุ่มยานยนต์/อุตสาหกรรม
    "SAT.BK","STANLY.BK","SMIT.BK","SUC.BK","SWC.BK",
    "TCC.BK","TEAMG.BK","THREL.BK","TIW.BK","TKS.BK",
    # กลุ่มสื่อ/บันเทิง
    "GMM.BK","GRAMMY.BK","GYT.BK","HTC.BK","II.BK",
    "IRC.BK","JKN.BK","JSP.BK","JTS.BK","KASET.BK",
    # กลุ่มการเงิน
    "MBKET.BK","MBK.BK","MLINK.BK","MSC.BK","NUSA.BK",
    "NYT.BK","OTO.BK","PAF.BK","PG.BK","PHOL.BK",
    # กลุ่มอื่นๆ
    "PLANB.BK","PLE.BK","PM.BK","PMC.BK","PPS.BK",
    "PPT.BK","PRG.BK","PRIN.BK","PRO.BK","PSL.BK",
    "PTG.BK","PTTEP.BK","QTC.BK","RCL.BK","RCI.BK",
    "RPCX.BK","RPH.BK","SAK.BK","SAMART.BK","SAUCE.BK",
    "SCN.BK","SE.BK","SEAFCO.BK","SEAOIL.BK","SFP.BK",
    "SGF.BK","SGP.BK","SHANG.BK","SKOM.BK","SKR.BK",
    "SLP.BK","SMART.BK","SMK.BK","SMT.BK","SNP.BK",
    "SOHO.BK","SOLAR.BK","SPA.BK","SPRC.BK","SPS.BK",
    "SQ.BK","SSF.BK","SSP.BK","SST.BK","STAR.BK",
    "STPI.BK","SUN.BK","SUSCO.BK","SVH.BK","SWC.BK",
]

STOCKS = list(dict.fromkeys(SET100 + MAI))  # ลบ duplicate

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
    position = "NONE"; last_date = None; new_signal = None
    bars = len(close)

    for i in range(2, bars):
        m  = macd_line.iloc[i]; s  = sig_line.iloc[i]
        h  = hist.iloc[i];      h1 = hist.iloc[i-1]; h2 = hist.iloc[i-2]
        pm = macd_line.iloc[i-1]; ps = sig_line.iloc[i-1]

        zone_bear     = m < 0 and s < 0
        zone_bull     = m > 0 and s > 0
        cross_up      = pm <= ps and m > s
        cross_down    = pm >= ps and m < s
        pink_to_green = (h1 < 0 and h1 > h2) and (h > 0 and h > h1)
        light_to_red  = (h1 > 0 and h1 < h2) and (h < 0 and h < h1)

        if zone_bear and cross_up and pink_to_green:
            position = "BUY"; last_date = df.index[i]
            if i == bars - 1: new_signal = "BUY"
        elif zone_bull and cross_down and light_to_red:
            position = "SELL"; last_date = df.index[i]
            if i == bars - 1: new_signal = "SELL"

    return position, last_date, new_signal

def send_line(symbol, signal, price, last_date):
    name     = symbol.replace(".BK", "")
    emoji    = "⚠️" if signal == "BUY" else "🔴"
    label    = "Ready to Buy" if signal == "BUY" else "Ready to Sell"
    now_thai = datetime.now(THAI_TZ).strftime('%d/%m/%Y %H:%M')
    payload  = {
        "symbol": name, "signal": signal, "price": round(price, 2),
        "message": (
            f"{emoji} {label} — {name}\n"
            f"ราคา: {round(price, 2)} บาท\n"
            f"Timeframe: Monthly\n"
            f"สัญญาณ: {last_date.strftime('%m/%Y') if last_date else '-'}\n"
            f"เวลา: {now_thai}"
        ),
        "time": datetime.now(THAI_TZ).strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print(f"    → LINE: {r.status_code}")
    except Exception as e:
        print(f"    → LINE error: {e}")

def save_json(results):
    """บันทึก scanner-data.json สำหรับ GitHub Pages"""
    data = {
        "updated": datetime.now(THAI_TZ).strftime('%d/%m/%Y %H:%M'),
        "stocks":  results
    }
    with open("scanner-data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  → บันทึก scanner-data.json ({len(results)} ตัว)")

def main():
    now_thai = datetime.now(THAI_TZ).strftime('%d/%m/%Y %H:%M:%S')
    print(f"\n{'='*60}")
    print(f"  JTS MACD Scanner v7.0 — Monthly ({len(STOCKS)} หุ้น)")
    print(f"  {now_thai}")
    print(f"{'='*60}\n")

    results = []

    for i, symbol in enumerate(STOCKS, 1):
        print(f"[{i:3d}/{len(STOCKS)}] {symbol:<15}", end=" ")
        try:
            df = yf.download(symbol, period=PERIOD, interval=TIMEFRAME,
                             progress=False, auto_adjust=True)
            if df.empty or len(df) < 30:
                print("⚠️  ข้อมูลน้อย"); continue

            position, last_date, new_signal = scan(df)
            price    = float(df["Close"].iloc[-1].item())
            icon     = "🟢" if position == "BUY" else "🔴" if position == "SELL" else "⬜"
            date_str = last_date.strftime("%m/%Y") if last_date else "-"
            new      = " ← ใหม่!" if new_signal else ""

            print(f"{icon} {str(position):<5} (ล่าสุด: {date_str}){new}")

            results.append({
                "symbol":   symbol.replace(".BK", ""),
                "position": position,
                "date":     date_str,
                "price":    round(price, 2),
                "new":      bool(new_signal)
            })

            if position in ("BUY", "SELL"):
                send_line(symbol, position, price, last_date)

        except Exception as e:
            print(f"❌ {e}")

    # บันทึก JSON
    save_json(results)

    # สรุป
    buy_list  = [r for r in results if r["position"] == "BUY"]
    sell_list = [r for r in results if r["position"] == "SELL"]
    new_list  = [r for r in results if r["new"]]

    print(f"\n{'='*60}")
    print(f"  สรุปสถานะปัจจุบัน")
    print(f"{'='*60}")
    print(f"\n🟢 กำลังกลับตัวขึ้น ({len(buy_list)} ตัว):")
    for r in buy_list:
        print(f"   {r['symbol']:<12} ราคา {r['price']:>8.2f}  ({r['date']}){' ← ใหม่!' if r['new'] else ''}")
    print(f"\n🔴 กำลังกลับตัวลง ({len(sell_list)} ตัว):")
    for r in sell_list:
        print(f"   {r['symbol']:<12} ราคา {r['price']:>8.2f}  ({r['date']}){' ← ใหม่!' if r['new'] else ''}")
    print(f"\n⚡ สัญญาณใหม่เดือนนี้ ({len(new_list)} ตัว):")
    for r in new_list:
        icon = "🟢" if r["position"] == "BUY" else "🔴"
        print(f"   {icon} {r['symbol']:<12} {r['position']}  ราคา {r['price']:>8.2f}")
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()

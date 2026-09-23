# 로컬 확인용 데모 원재료. draft/data 의 샘플 CSV 를 확인된 원천 테이블 모양(대문자 열, 날짜는 YYYYMMDD 문자열)으로 만든다.
#   raw_commit ← FEIAI0488NTA 모양 (sql/ALT_Commit.sql 결과)
#   raw_pcap   ← FEIAI0432NTA 모양 (sql/ALT_PCAP.sql 결과): 분기말 기준 설립 이후 누적, 최신 제공일 한 벌,
#               통화 유형별 long 행(CURR_ID, CURR_TYP), GCM 보고 기준, 날짜는 'YYYY-MM-DD'
#               PCAP 은 한 분기 늦게 들어오므로 기준일(9/22) 시점에는 6/30 까지만 있다고 가정
#   raw_target ← data/ALT_Target.xlsx '목표' 시트 (실제 경로와 동일)
#   raw_fund   ← sql/ALT_Fund.sql 결과 (펀드명·자산군은 아직 원천 미확인이지만 데모에서는 채운다)
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "draft" / "data"
PCAP_LAST = "2026-06-30"     # 데모에서 마지막으로 제공된 PCAP 기준일
FX_USD = {"KRW": 1350.0, "USD": 1.0, "EUR": 0.92, "JPY": 150.0}   # 1 USD 당 통화 단위 (FMCBI0006NTA 모양)


def load_demo():
    """(raw_commit, raw_pcap, raw_target, raw_fund) 를 돌려준다"""
    tx = pd.read_csv(DATA_DIR / "transactions.csv", encoding="utf-8-sig")
    tg = pd.read_csv(DATA_DIR / "targets.csv", encoding="utf-8-sig")
    tx["date"] = pd.to_datetime(tx["date"])
    tx["currency"] = tx["currency"].fillna("KRW")
    code = "F" + (tx["fund"].astype("category").cat.codes + 1).astype(str).str.zfill(4)   # 펀드코드 흉내
    tx["code"] = code

    c = tx[tx["type"] == "약정"]
    raw_commit = pd.DataFrame({
        "WRK_DT": c["date"].dt.strftime("%Y%m%d"),
        "FUND_CD": c["code"],
        "CCY": c["currency"],
        "AMT_LOCAL": c["local_amount"].astype(float),
        # SQL 처럼 KRW 펀드만 원화를 채우고 외화는 비운다 (processor 가 약정일 환율로 환산)
        "AMT_KRW": c["amount"].astype(float).where(c["currency"] == "KRW"),
    })

    # 분기말 누적 (설립 이후). 실제 SQL 결과처럼 통화 유형별 long 행: CP=원화(KRW) 행, CD=펀드 통화 행. GCM 보고 기준만
    f = tx[tx["type"].isin(["집행", "분배"])].copy()
    f["Q_END"] = f["date"].dt.to_period("Q").dt.end_time.dt.normalize()
    f = f[f["Q_END"] <= pd.Timestamp(PCAP_LAST)]
    q = f.pivot_table(index=["code", "currency", "Q_END"], columns="type", values=["amount", "local_amount"], aggfunc="sum", fill_value=0.0)
    q = q.groupby(level="code").cumsum().reset_index()
    funded_krw = q[("amount", "집행")] if ("amount", "집행") in q else 0.0
    distrb_krw = q[("amount", "분배")] if ("amount", "분배") in q else 0.0
    funded_loc = q[("local_amount", "집행")] if ("local_amount", "집행") in q else 0.0
    distrb_loc = q[("local_amount", "분배")] if ("local_amount", "분배") in q else 0.0
    base = {"PROV_DT": "2026-09-18", "WRK_DT": q["Q_END"].dt.strftime("%Y-%m-%d"), "FUND_CD": q["code"],
            "RPRT_NM": "AS Reported by GCM", "COMMIT_AMT": 0.0, "NAV_AMT": 0.0}
    cp = pd.DataFrame(dict(base, CURR_ID="KRW", CURR_TYP="CP", FUNDED_AMT=funded_krw, DISTRB_AMT=distrb_krw))
    cd = pd.DataFrame(dict(base, CURR_ID=q["currency"], CURR_TYP="CD", FUNDED_AMT=funded_loc, DISTRB_AMT=distrb_loc))
    raw_pcap = pd.concat([cp, cd], ignore_index=True)[
        ["PROV_DT", "WRK_DT", "FUND_CD", "CURR_ID", "CURR_TYP", "RPRT_NM", "COMMIT_AMT", "FUNDED_AMT", "DISTRB_AMT", "NAV_AMT"]]

    # 목표는 실제 경로와 같게 엑셀 양식(data/ALT_Target.xlsx '목표' 시트)에서 읽는다
    raw_target = pd.read_excel(Path(__file__).resolve().parent / "data" / "ALT_Target.xlsx", sheet_name="목표")

    first = c.sort_values("date").drop_duplicates("code")
    # 액티브 프로그램 코드(AVTV_PGM_CD) 흉내: 자산군별 코드 중 하나를 펀드 번호로 돌려 가며 배정
    pgm_pool = {"사모벤처": ["XPV01", "XPV03", "XPV04", "XPV05", "XPV09", "XPV10", "XPV11"],
                "부동산": ["XRE01", "XRE02", "XRE03", "XRE04"], "인프라": ["XIF02", "XIF03", "XIF05", "XIF06"]}
    pgm = [pgm_pool[cls][int(code[1:]) % len(pgm_pool[cls])] for code, cls in zip(first["code"], first["asset_class"])]
    raw_fund = pd.DataFrame({
        "FUND_CD": first["code"].values,
        "FUND_NM": first["fund"].values,
        "ASSET_CLS": first["asset_class"].values,
        "PGM_CD": pgm,
        "CCY": first["currency"].values,
        "VINTAGE_YR": first["date"].dt.year.values,
    })
    return raw_commit, raw_pcap, raw_target, raw_fund


def load_demo_fx():
    """FMCBI0006NTA 모양의 환율 데모 (월초 일자, 1 USD 당 통화 단위). sql/ALT_FX.sql 결과 모양: WRK_DT, CURR_ID, USD_RATE
    샘플 거래를 만들 때 쓴 환율(draft/scripts/make_sample_data.py 의 fx)과 같은 값을 써서 환산 결과가 원본과 맞도록 한다"""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent / "draft" / "scripts"))
    import make_sample_data as gen
    rows = []
    for d in pd.date_range("2018-01-01", "2026-12-01", freq="MS"):
        krw_per_usd = gen.fx(d.date(), "USD")
        rows.append({"WRK_DT": d.strftime("%Y%m%d"), "CURR_ID": "KRW", "USD_RATE": krw_per_usd})
        rows.append({"WRK_DT": d.strftime("%Y%m%d"), "CURR_ID": "USD", "USD_RATE": 1.0})
        rows.append({"WRK_DT": d.strftime("%Y%m%d"), "CURR_ID": "EUR", "USD_RATE": krw_per_usd / gen.fx(d.date(), "EUR")})
    return pd.DataFrame(rows)

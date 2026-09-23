# 로컬 확인용 데모 원재료. draft/data 의 샘플 CSV 를 확인된 원천 테이블 모양(대문자 열, 날짜는 YYYYMMDD 문자열)으로 만든다.
#   raw_commit ← FEIAI0488NTA 모양 (sql/ALT_Commit.sql 결과)
#   raw_pcap   ← FEIAI0432NTA 모양 (sql/ALT_PCAP.sql 결과): 분기말 기준 설립 이후 누적, 최신 제공일 한 벌,
#               통화 유형별 long 행(CURR_ID, CURR_TYP), GCM 보고 기준, 날짜는 'YYYY-MM-DD'
#               PCAP 은 한 분기 늦게 들어오므로 기준일(9/22) 시점에는 6/30 까지만 있다고 가정
#   raw_target ← sql/ALT_Target.sql 결과
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
        "AMT_KRW": c["amount"].astype(float),
        "AMT_LOCAL": c["local_amount"].astype(float),
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

    raw_target = pd.DataFrame({
        "TARGET_YR": tg["year"].astype(int),
        "ASSET_CLS": tg["asset_class"],
        "COMMIT_KRW": tg["commitment"].astype(float),
        "DRAW_KRW": tg["drawdown"].astype(float),
        "DIST_KRW": tg["distribution"].astype(float),
        "NET_KRW": pd.to_numeric(tg["net"], errors="coerce"),
    })
    first = c.sort_values("date").drop_duplicates("code")
    raw_fund = pd.DataFrame({
        "FUND_CD": first["code"].values,
        "FUND_NM": first["fund"].values,
        "ASSET_CLS": first["asset_class"].values,
        "CCY": first["currency"].values,
        "VINTAGE_YR": first["date"].dt.year.values,
    })
    return raw_commit, raw_pcap, raw_target, raw_fund


def load_demo_fx():
    """FMCBI0006NTA 모양의 환율 데모 (월말, 1 USD 당 통화 단위). sql/ALT_FX.sql 결과 모양: WRK_DT, CURR_ID, USD_RATE"""
    dates = pd.date_range("2018-01-31", "2026-12-31", freq="ME") if hasattr(pd.offsets, "MonthEnd") else pd.date_range("2018-01-31", "2026-12-31", freq="M")
    rows = [{"WRK_DT": d.strftime("%Y%m%d"), "CURR_ID": c, "USD_RATE": r} for d in dates for c, r in FX_USD.items()]
    return pd.DataFrame(rows)

# 로컬 확인용 데모 원재료. draft/data 의 샘플 CSV 를 Oracle 이 돌려주는 모양(대문자 열, WRK_DT 는 YYYYMMDD 문자열)으로 만든다.
# 실제 데이터 구조가 확정되면 sql/*.sql 이 같은 열 이름을 돌려주도록 맞춘다.
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "draft" / "data"


def load_demo():
    """(raw_cf, raw_target, raw_fund) 를 돌려준다. 각각 sql/ALT_CashFlow.sql, ALT_Target.sql, ALT_Fund.sql 의 결과 모양."""
    tx = pd.read_csv(DATA_DIR / "transactions.csv", encoding="utf-8-sig")
    tg = pd.read_csv(DATA_DIR / "targets.csv", encoding="utf-8-sig")

    raw_cf = pd.DataFrame({
        "WRK_DT": pd.to_datetime(tx["date"]).dt.strftime("%Y%m%d"),
        "FUND_NM": tx["fund"],
        "ASSET_CLS": tx["asset_class"],
        "CCY": tx["currency"].fillna("KRW"),
        "TX_TYPE": tx["type"],
        "AMT_KRW": tx["amount"].astype(float),
        "AMT_LOCAL": tx["local_amount"].astype(float),
    })
    raw_target = pd.DataFrame({
        "TARGET_YR": tg["year"].astype(int),
        "ASSET_CLS": tg["asset_class"],
        "COMMIT_KRW": tg["commitment"].astype(float),
        "DRAW_KRW": tg["drawdown"].astype(float),
        "DIST_KRW": tg["distribution"].astype(float),
        "NET_KRW": pd.to_numeric(tg["net"], errors="coerce"),
    })
    first = tx[tx["type"] == "약정"].sort_values("date").drop_duplicates("fund")
    raw_fund = pd.DataFrame({
        "FUND_NM": first["fund"].values,
        "ASSET_CLS": first["asset_class"].values,
        "CCY": first["currency"].fillna("KRW").values,
        "VINTAGE_YR": pd.to_datetime(first["date"]).dt.year.values,
    })
    return raw_cf, raw_target, raw_fund

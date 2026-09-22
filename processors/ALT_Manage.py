# ------------------------------------------------------------
# processors/ALT_Manage.py
# 무엇: 대체투자 약정·집행·분배·순증 현황 탭(ALT_Manage)의 가공 모듈
#
# 입력 (모두 loader.load_data 결과, Oracle 이라 열 이름은 대문자)
#   raw_cf     sql/ALT_CashFlow.sql  long 형태의 현금흐름
#              WRK_DT(YYYYMMDD 또는 날짜), FUND_CD(선택), FUND_NM, ASSET_CLS, CCY, TX_TYPE(약정|집행|분배), AMT_KRW, AMT_LOCAL
#              FUND_CD 가 있으면 펀드 키로 쓰고 FUND_NM 은 표시 이름, 없으면 FUND_NM 이 키
#   raw_target sql/ALT_Target.sql    연도·자산군별 목표
#              TARGET_YR, ASSET_CLS, COMMIT_KRW, DRAW_KRW, DIST_KRW, NET_KRW(NULL 허용)
#   raw_fund   sql/ALT_Fund.sql      펀드 마스터 (선택, None 이면 현금흐름에서 유추)
#              FUND_CD(선택), FUND_NM, ASSET_CLS, CCY, VINTAGE_YR
#   asof       기준일 (None 이면 raw_cf 의 마지막 거래일). 기준일 이후 거래는 제외
#
# 출력 (사전)  실패하면 {}
#   asof        기준일 pd.Timestamp
#   unit        원화 단위 표기 "억원"      local_unit 외화 단위 표기 "백만"
#   classes     자산군 목록 (표시 순서, '전체' 제외)
#   years       목표가 있는 연도 목록 (오름차순)
#   base_year   기준연도 (기준일이 속한 연도. 목표가 없으면 마지막 목표 연도)
#   target      DataFrame [YEAR, CLS, 약정, 집행, 분배, 순증]   CLS 에 '전체' 포함
#   monthly     DataFrame [YEAR, MONTH, CLS, 약정, 집행, 분배, 순증, 건수]
#                 월별 실적. '전체' 포함. 기준일 이후 월은 없음. 실적 없는 달은 0
#   cum         monthly 와 같은 열, 연초부터 누적
#   kpi         DataFrame [YEAR, CLS, METRIC, MONTHS, TARGET, ACTUAL, RATIO, REMAIN, PREV]
#                 연도·자산군·지표별 목표/현황/달성률. MONTHS 는 집계에 들어간 마지막 월,
#                 PREV 는 전년 동기(같은 월 범위) 실적. 전년 자료 없으면 NaN
#   funds       DataFrame [FUND_KEY, FUND, CLS, CCY, VINTAGE, YEAR, 약정, 집행, 분배, 순증,
#                          약정_L, 집행_L, 분배_L, 순증_L, 누적약정, 누적집행, 집행률]
#                 펀드·연도별 실적(원화, _L 은 펀드 통화). 누적은 그 연도까지, 집행률 = 누적집행/누적약정
#
# 단위: 원화는 억원, 펀드 통화는 KRW 펀드면 억원·외화 펀드면 백만.
#      SQL 이 이미 그 단위로 돌려준다고 가정한다 (확인 사항: 원 단위면 SQL 에서 나눈다)
# 순증 = 집행 − 분배 (투자잔액 증가분)
# ------------------------------------------------------------
import pandas as pd

METRICS = ["약정", "집행", "분배", "순증"]
FLOW_TYPES = ["약정", "집행", "분배"]
CLASS_ORDER = ["사모벤처", "부동산", "인프라"]   # 표시 순서. 목록에 없는 자산군은 뒤에 이름순
ALL = "전체"
UNIT = "억원"
LOCAL_UNIT = "백만"
# 거래유형 코드가 영문으로 올 때를 대비한 보정 (SQL 에서 한글로 돌려주면 그대로 통과)
TYPE_MAP = {"COMMIT": "약정", "COMMITMENT": "약정", "DRAW": "집행", "DRAWDOWN": "집행", "CALL": "집행",
            "DIST": "분배", "DISTRIBUTION": "분배"}


def _to_date(s):
    """YYYYMMDD 문자열/숫자 또는 이미 날짜인 열을 날짜로 통일"""
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s)
    return pd.to_datetime(s.astype(str).str.strip().str[:8], format="%Y%m%d", errors="coerce")


def _prep_cf(raw):
    """현금흐름 원재료 표준화"""
    df = raw.copy()
    df.columns = df.columns.str.upper()
    df["WRK_DT"] = _to_date(df["WRK_DT"])
    df["FUND_NM"] = df["FUND_NM"].astype(str).str.strip()
    # 펀드 키: FUND_CD 가 있으면 코드, 없으면 이름. 표시는 FUND_NM
    df["FUND_KEY"] = df["FUND_CD"].astype(str).str.strip() if "FUND_CD" in df else df["FUND_NM"]
    df["ASSET_CLS"] = df["ASSET_CLS"].astype(str).str.strip()
    df["CCY"] = df["CCY"].fillna("KRW").astype(str).str.strip().str.upper().replace("", "KRW") if "CCY" in df else "KRW"
    df["TX_TYPE"] = df["TX_TYPE"].astype(str).str.strip()
    df["TX_TYPE"] = df["TX_TYPE"].map(lambda t: TYPE_MAP.get(t.upper(), t))
    df["AMT_KRW"] = pd.to_numeric(df["AMT_KRW"], errors="coerce").fillna(0.0)
    if "AMT_LOCAL" in df:
        local = pd.to_numeric(df["AMT_LOCAL"], errors="coerce")
    else:
        local = pd.Series(pd.NA, index=df.index, dtype="float")
    # 로컬 금액이 비어 있으면 KRW 펀드는 원화 금액, 외화 펀드는 0 으로 둔다
    df["AMT_LOCAL"] = local.where(local.notna(), df["AMT_KRW"].where(df["CCY"] == "KRW", 0.0)).astype(float)
    df = df.dropna(subset=["WRK_DT"])
    df = df[df["TX_TYPE"].isin(FLOW_TYPES)]
    return df[["WRK_DT", "FUND_KEY", "FUND_NM", "ASSET_CLS", "CCY", "TX_TYPE", "AMT_KRW", "AMT_LOCAL"]]


def _prep_target(raw):
    """목표 원재료 표준화. 순증 목표가 비어 있으면 집행 − 분배"""
    df = raw.copy()
    df.columns = df.columns.str.upper()
    df = df.rename(columns={"TARGET_YR": "YEAR", "ASSET_CLS": "CLS", "COMMIT_KRW": "약정",
                            "DRAW_KRW": "집행", "DIST_KRW": "분배", "NET_KRW": "순증"})
    for m in FLOW_TYPES:
        df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0.0)
    net = pd.to_numeric(df["순증"], errors="coerce") if "순증" in df else pd.Series(pd.NA, index=df.index, dtype="float")
    df["순증"] = net.where(net.notna(), df["집행"] - df["분배"]).astype(float)
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce").astype(int)
    df["CLS"] = df["CLS"].astype(str).str.strip()
    return df.groupby(["YEAR", "CLS"], as_index=False)[METRICS].sum()


def _prep_fund(raw):
    """펀드 마스터 표준화 (선택 입력)"""
    if raw is None or raw.empty:
        return None
    df = raw.copy()
    df.columns = df.columns.str.upper()
    df["FUND_NM"] = df["FUND_NM"].astype(str).str.strip()
    df["FUND_KEY"] = df["FUND_CD"].astype(str).str.strip() if "FUND_CD" in df else df["FUND_NM"]
    df["CCY"] = (df["CCY"].fillna("KRW").astype(str).str.strip().str.upper() if "CCY" in df else "KRW")
    df["VINTAGE_YR"] = pd.to_numeric(df["VINTAGE_YR"], errors="coerce") if "VINTAGE_YR" in df else pd.NA
    return df.drop_duplicates("FUND_KEY").set_index("FUND_KEY")


def _class_order(names):
    """자산군 표시 순서: CLASS_ORDER 먼저, 나머지는 이름순"""
    names = set(names)
    return [c for c in CLASS_ORDER if c in names] + sorted(names - set(CLASS_ORDER))


def _last_month(year, asof):
    """그 연도에서 집계에 포함할 마지막 월. 과거 연도 12, 기준 연도는 기준일의 월, 미래 연도 0"""
    if year < asof.year:
        return 12
    if year == asof.year:
        return asof.month
    return 0


def _with_total(df, keys):
    """자산군별 표에 '전체'(합계) 행을 덧붙인다"""
    total = df.groupby(keys, as_index=False)[METRICS + (["건수"] if "건수" in df else [])].sum()
    total["CLS"] = ALL
    return pd.concat([df, total], ignore_index=True)


def process_ALT_Manage(raw_cf, raw_target, raw_fund=None, asof=None):
    if any(x is None or x.empty for x in [raw_cf, raw_target]):
        return {}
    cf = _prep_cf(raw_cf)
    tg = _prep_target(raw_target)
    if cf.empty or tg.empty:
        return {}
    fund_master = _prep_fund(raw_fund)

    asof = pd.Timestamp(asof) if asof is not None else cf["WRK_DT"].max()
    cf = cf[cf["WRK_DT"] <= asof]

    classes = _class_order(set(tg["CLS"]) | set(cf["ASSET_CLS"]))
    years = sorted(tg["YEAR"].unique().tolist())
    base_year = asof.year if asof.year in years else years[-1]

    # ---- 목표 (전체 포함)
    target = _with_total(tg, ["YEAR"])[["YEAR", "CLS"] + METRICS]

    # ---- 월별 실적: 연도 × 월(마지막 월까지) × 자산군 격자를 만들고 실적을 얹는다
    cf = cf.assign(YEAR=cf["WRK_DT"].dt.year, MONTH=cf["WRK_DT"].dt.month)
    piv = cf.pivot_table(index=["YEAR", "MONTH", "ASSET_CLS"], columns="TX_TYPE",
                         values="AMT_KRW", aggfunc="sum", fill_value=0.0)
    for t in FLOW_TYPES:
        if t not in piv.columns:
            piv[t] = 0.0
    cnt = cf[cf["TX_TYPE"] == "약정"].groupby(["YEAR", "MONTH", "ASSET_CLS"]).size().rename("건수")
    flows = piv[FLOW_TYPES].join(cnt).fillna({"건수": 0}).reset_index().rename(columns={"ASSET_CLS": "CLS"})

    grid = []
    for y in sorted(set(years) | set(cf["YEAR"].unique().tolist())):
        for m in range(1, _last_month(y, asof) + 1):
            for c in classes:
                grid.append((y, m, c))
    monthly = pd.DataFrame(grid, columns=["YEAR", "MONTH", "CLS"]).merge(flows, how="left", on=["YEAR", "MONTH", "CLS"])
    monthly[FLOW_TYPES + ["건수"]] = monthly[FLOW_TYPES + ["건수"]].fillna(0.0)
    monthly["순증"] = monthly["집행"] - monthly["분배"]
    monthly["건수"] = monthly["건수"].astype(int)
    monthly = _with_total(monthly, ["YEAR", "MONTH"])[["YEAR", "MONTH", "CLS"] + METRICS + ["건수"]]
    monthly = monthly.sort_values(["YEAR", "CLS", "MONTH"]).reset_index(drop=True)

    cum = monthly.copy()
    cum[METRICS + ["건수"]] = cum.groupby(["YEAR", "CLS"])[METRICS + ["건수"]].cumsum()

    # ---- KPI: 연도 × 자산군(전체 포함) × 지표
    rows = []
    cum_idx = cum.set_index(["YEAR", "CLS", "MONTH"])
    tg_idx = target.set_index(["YEAR", "CLS"])
    for y in years:
        months = _last_month(y, asof)
        for c in [ALL] + classes:
            for m in METRICS:
                t = float(tg_idx[m].get((y, c), 0.0))
                a = float(cum_idx[m].get((y, c, months), 0.0)) if months > 0 else 0.0
                p = cum_idx[m].get((y - 1, c, months)) if months > 0 else None
                rows.append({"YEAR": y, "CLS": c, "METRIC": m, "MONTHS": months, "TARGET": t, "ACTUAL": a,
                             "RATIO": (a / t) if t else pd.NA, "REMAIN": (t - a) if t else pd.NA,
                             "PREV": float(p) if p is not None and not pd.isna(p) else pd.NA})
    kpi = pd.DataFrame(rows)

    # ---- 펀드·연도별 실적 (원화 + 펀드 통화)
    # 펀드 키 하나에 표시 이름 하나 (마지막 거래의 이름)
    names = cf.sort_values("WRK_DT").groupby("FUND_KEY")["FUND_NM"].last()
    fy = cf.pivot_table(index=["FUND_KEY", "ASSET_CLS", "CCY", "YEAR"], columns="TX_TYPE",
                        values=["AMT_KRW", "AMT_LOCAL"], aggfunc="sum", fill_value=0.0)
    funds = pd.DataFrame(index=fy.index)
    for t in FLOW_TYPES:
        funds[t] = fy[("AMT_KRW", t)] if ("AMT_KRW", t) in fy.columns else 0.0
        funds[t + "_L"] = fy[("AMT_LOCAL", t)] if ("AMT_LOCAL", t) in fy.columns else 0.0
    funds["순증"] = funds["집행"] - funds["분배"]
    funds["순증_L"] = funds["집행_L"] - funds["분배_L"]
    funds = funds.reset_index().rename(columns={"ASSET_CLS": "CLS"}).sort_values(["FUND_KEY", "YEAR"])
    funds["FUND"] = funds["FUND_KEY"].map(names)
    funds["누적약정"] = funds.groupby("FUND_KEY")["약정"].cumsum()
    funds["누적집행"] = funds.groupby("FUND_KEY")["집행"].cumsum()
    funds["집행률"] = funds["누적집행"] / funds["누적약정"].replace(0, pd.NA)
    first_commit = cf[cf["TX_TYPE"] == "약정"].groupby("FUND_KEY")["YEAR"].min()
    funds["VINTAGE"] = funds["FUND_KEY"].map(first_commit)
    if fund_master is not None:
        vin = funds["FUND_KEY"].map(fund_master["VINTAGE_YR"])
        funds["VINTAGE"] = vin.where(vin.notna(), funds["VINTAGE"])
    funds["VINTAGE"] = funds["VINTAGE"].where(funds["VINTAGE"].notna(), funds["YEAR"]).astype(int)
    funds = funds[["FUND_KEY", "FUND", "CLS", "CCY", "VINTAGE", "YEAR"] + METRICS + [m + "_L" for m in METRICS]
                  + ["누적약정", "누적집행", "집행률"]].reset_index(drop=True)

    return {
        "asof": asof,
        "unit": UNIT,
        "local_unit": LOCAL_UNIT,
        "classes": classes,
        "years": years,
        "base_year": base_year,
        "target": target,
        "monthly": monthly,
        "cum": cum,
        "kpi": kpi,
        "funds": funds,
    }

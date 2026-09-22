# ------------------------------------------------------------
# processors/ALT_Manage.py
# 무엇: 대체투자 약정·집행·분배·순증 현황 탭(ALT_Manage)의 가공 모듈
#
# 입력 (모두 loader.load_data 결과, Oracle 이라 열 이름은 대문자)
#   raw_commit sql/ALT_Commit.sql  약정 내역 (FEIAI0488NTA)
#              WRK_DT(약정일), FUND_CD, CCY, AMT_KRW, AMT_LOCAL
#   raw_pcap   sql/ALT_PCAP.sql    집행·분배·NAV 분기 스냅샷 (FEIAI0432NTA, 최신 제공일 한 벌)
#              WRK_DT(기준일=PCAP_DATE), FUND_CD, FUNDED_KRW, FUNDED_LOCAL, DISTRB_KRW, DISTRB_LOCAL, NAV_KRW(선택)
#              기본은 설립 이후 누적값으로 보고 분기 증분으로 바꾼다. 기간 증분이면 pcap_cumulative=False
#   raw_target sql/ALT_Target.sql  연도·자산군별 목표
#              TARGET_YR, ASSET_CLS, COMMIT_KRW, DRAW_KRW, DIST_KRW, NET_KRW(NULL 허용)
#   raw_fund   sql/ALT_Fund.sql    펀드 마스터 (선택)  FUND_CD, FUND_NM, ASSET_CLS, CCY, VINTAGE_YR
#              없으면 약정 내역에서 통화·빈티지를 유추하고 펀드명은 코드, 자산군은 '미분류'
#   asof       기준일 (None 이면 약정·PCAP 의 마지막 날짜). 기준일 이후 자료는 제외
#
# 출력 (사전)  실패하면 {}
#   asof        약정 기준일 pd.Timestamp        asof_flow  집행·분배 기준일 (기준일 이하 마지막 PCAP 기준일)
#   flow_freq   집행·분배 자료 주기 "Q"(PCAP 분기) 또는 "M"
#   unit        원화 단위 표기 "억원"           local_unit 외화 단위 표기 "백만"
#   classes     자산군 목록 (표시 순서, '전체' 제외)
#   years       목표가 있는 연도 목록          base_year 기준연도 (기준일이 속한 연도, 없으면 마지막 목표 연도)
#   target      DataFrame [YEAR, CLS, 약정, 집행, 분배, 순증]   CLS 에 '전체' 포함
#   monthly     DataFrame [YEAR, MONTH, CLS, 약정, 집행, 분배, 순증, 건수]
#                 월별 실적, '전체' 포함. 약정 기준일 이후 월은 없고, 집행·분배·순증은 PCAP 기준일 이후 월이 NaN
#   cum         monthly 와 같은 열, 연초부터 누적
#   kpi         DataFrame [YEAR, CLS, METRIC, MONTHS, TARGET, ACTUAL, RATIO, REMAIN, PREV]
#                 MONTHS 는 지표별 집계 마지막 월 (약정은 기준일, 집행·분배·순증은 PCAP 기준일 기준)
#                 PREV 는 전년 같은 월 범위 실적, 전년 자료 없으면 NaN
#   funds       DataFrame [FUND_KEY, FUND, CLS, CCY, VINTAGE, YEAR, 약정, 집행, 분배, 순증,
#                          약정_L, 집행_L, 분배_L, 순증_L, 누적약정, 누적집행, 집행률]
#                 펀드·연도별 실적(원화, _L 은 펀드 통화). 누적은 그 연도까지, 집행률 = 누적집행/누적약정
#
# 단위: 원화는 억원, 펀드 통화는 KRW 펀드면 억원·외화 펀드면 백만. SQL 이 그 단위로 돌려준다고 가정 (확인 사항)
# 순증 = 집행 − 분배 (투자잔액 증가분)
# ------------------------------------------------------------
import pandas as pd

METRICS = ["약정", "집행", "분배", "순증"]
FLOW_TYPES = ["약정", "집행", "분배"]
PCAP_METRICS = ["집행", "분배", "순증"]                 # PCAP(분기) 기준일을 따르는 지표
CLASS_ORDER = ["사모벤처", "부동산", "인프라"]          # 표시 순서. 목록에 없는 자산군은 뒤에 이름순
ALL = "전체"
UNIT = "억원"
LOCAL_UNIT = "백만"
NO_CLASS = "미분류"


def _to_date(s):
    """YYYYMMDD 문자열/숫자 또는 이미 날짜인 열을 날짜로 통일"""
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s)
    return pd.to_datetime(s.astype(str).str.strip().str[:8], format="%Y%m%d", errors="coerce")


def _num(df, col):
    """숫자 열 표준화. 없으면 0"""
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0) if col in df else pd.Series(0.0, index=df.index)


def _prep_commit(raw):
    """약정 원재료 → long 현금흐름 (TX_TYPE=약정)"""
    df = raw.copy()
    df.columns = df.columns.str.upper()
    df["WRK_DT"] = _to_date(df["WRK_DT"])
    df["FUND_KEY"] = df["FUND_CD"].astype(str).str.strip()
    df["CCY"] = df["CCY"].fillna("KRW").astype(str).str.strip().str.upper().replace("", "KRW") if "CCY" in df else "KRW"
    df["AMT_KRW"] = _num(df, "AMT_KRW")
    local = pd.to_numeric(df["AMT_LOCAL"], errors="coerce") if "AMT_LOCAL" in df else pd.Series(pd.NA, index=df.index, dtype="float")
    df["AMT_LOCAL"] = local.where(local.notna(), df["AMT_KRW"].where(df["CCY"] == "KRW", 0.0)).astype(float)
    df["TX_TYPE"] = "약정"
    df = df.dropna(subset=["WRK_DT"])
    return df[["WRK_DT", "FUND_KEY", "CCY", "TX_TYPE", "AMT_KRW", "AMT_LOCAL"]]


def _prep_pcap(raw, cumulative):
    """PCAP 원재료 → long 현금흐름 (TX_TYPE=집행/분배). 누적값이면 펀드별 기준일 순 차분으로 증분을 만든다"""
    df = raw.copy()
    df.columns = df.columns.str.upper()
    df["WRK_DT"] = _to_date(df["WRK_DT"])
    df["FUND_KEY"] = df["FUND_CD"].astype(str).str.strip()
    cols = ["FUNDED_KRW", "FUNDED_LOCAL", "DISTRB_KRW", "DISTRB_LOCAL"]
    for c in cols:
        df[c] = _num(df, c)
    df = df.dropna(subset=["WRK_DT"]).sort_values(["FUND_KEY", "WRK_DT"])
    df = df.drop_duplicates(["FUND_KEY", "WRK_DT"], keep="last")
    if cumulative:
        # 첫 기준일의 증분은 그 시점 누적값 (이력이 잘려 있으면 첫 분기에 몰린다 — 확인 사항)
        for c in cols:
            d = df.groupby("FUND_KEY")[c].diff()
            df[c] = d.where(d.notna(), df[c])
    funded = df[["WRK_DT", "FUND_KEY"]].assign(TX_TYPE="집행", AMT_KRW=df["FUNDED_KRW"], AMT_LOCAL=df["FUNDED_LOCAL"])
    distrb = df[["WRK_DT", "FUND_KEY"]].assign(TX_TYPE="분배", AMT_KRW=df["DISTRB_KRW"], AMT_LOCAL=df["DISTRB_LOCAL"])
    return pd.concat([funded, distrb], ignore_index=True)


def _prep_target(raw):
    """목표 원재료 표준화. 순증 목표가 비어 있으면 집행 − 분배"""
    df = raw.copy()
    df.columns = df.columns.str.upper()
    df = df.rename(columns={"TARGET_YR": "YEAR", "ASSET_CLS": "CLS", "COMMIT_KRW": "약정",
                            "DRAW_KRW": "집행", "DIST_KRW": "분배", "NET_KRW": "순증"})
    for m in FLOW_TYPES:
        df[m] = _num(df, m)
    net = pd.to_numeric(df["순증"], errors="coerce") if "순증" in df else pd.Series(pd.NA, index=df.index, dtype="float")
    df["순증"] = net.where(net.notna(), df["집행"] - df["분배"]).astype(float)
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce").astype(int)
    df["CLS"] = df["CLS"].astype(str).str.strip()
    return df.groupby(["YEAR", "CLS"], as_index=False)[METRICS].sum()


def _prep_fund(raw):
    """펀드 마스터 표준화 (선택 입력). FUND_KEY 를 index 로"""
    if raw is None or raw.empty:
        return None
    df = raw.copy()
    df.columns = df.columns.str.upper()
    df["FUND_KEY"] = df["FUND_CD"].astype(str).str.strip()
    df["FUND_NM"] = df["FUND_NM"].astype(str).str.strip() if "FUND_NM" in df else df["FUND_KEY"]
    df["ASSET_CLS"] = df["ASSET_CLS"].fillna(NO_CLASS).astype(str).str.strip() if "ASSET_CLS" in df else NO_CLASS
    df["CCY"] = df["CCY"].fillna("KRW").astype(str).str.strip().str.upper() if "CCY" in df else "KRW"
    df["VINTAGE_YR"] = pd.to_numeric(df["VINTAGE_YR"], errors="coerce") if "VINTAGE_YR" in df else pd.NA
    return df.drop_duplicates("FUND_KEY").set_index("FUND_KEY")[["FUND_NM", "ASSET_CLS", "CCY", "VINTAGE_YR"]]


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


def _with_total(df, keys, cols):
    """자산군별 표에 '전체'(합계) 행을 덧붙인다"""
    total = df.groupby(keys, as_index=False)[cols].sum(min_count=1)
    total["CLS"] = ALL
    return pd.concat([df, total], ignore_index=True)


def process_ALT_Manage(raw_commit, raw_pcap, raw_target, raw_fund=None, asof=None, pcap_cumulative=True):
    if any(x is None or x.empty for x in [raw_commit, raw_pcap, raw_target]):
        return {}
    commit = _prep_commit(raw_commit)
    pcap = _prep_pcap(raw_pcap, pcap_cumulative)
    tg = _prep_target(raw_target)
    if commit.empty or pcap.empty or tg.empty:
        return {}
    fund_master = _prep_fund(raw_fund)

    # ---- 기준일: 약정은 asof, 집행·분배는 asof 이하 마지막 PCAP 기준일
    asof = pd.Timestamp(asof) if asof is not None else max(commit["WRK_DT"].max(), pcap["WRK_DT"].max())
    commit = commit[commit["WRK_DT"] <= asof]
    pcap = pcap[pcap["WRK_DT"] <= asof]
    asof_flow = pcap["WRK_DT"].max() if len(pcap) else asof

    # ---- 펀드 속성(이름·자산군·통화·빈티지): 마스터 우선, 없으면 약정에서 유추
    first_commit = commit.sort_values("WRK_DT").drop_duplicates("FUND_KEY").set_index("FUND_KEY")
    attrs = pd.DataFrame(index=first_commit.index.union(pcap["FUND_KEY"].unique()))
    attrs["FUND_NM"] = attrs.index.to_series()
    attrs["ASSET_CLS"] = NO_CLASS
    attrs["CCY"] = first_commit["CCY"].reindex(attrs.index).fillna("KRW")
    attrs["VINTAGE_YR"] = first_commit["WRK_DT"].dt.year.reindex(attrs.index)
    if fund_master is not None:
        fm = fund_master.reindex(attrs.index)
        for c in ["FUND_NM", "ASSET_CLS", "CCY", "VINTAGE_YR"]:
            attrs[c] = fm[c].where(fm[c].notna(), attrs[c])
    attrs["VINTAGE_YR"] = pd.to_numeric(attrs["VINTAGE_YR"], errors="coerce")

    # ---- long 현금흐름 하나로 합치고 펀드 속성을 붙인다
    cf = pd.concat([commit[["WRK_DT", "FUND_KEY", "TX_TYPE", "AMT_KRW", "AMT_LOCAL"]], pcap], ignore_index=True)
    cf = cf.join(attrs[["FUND_NM", "ASSET_CLS", "CCY"]], on="FUND_KEY")
    cf["YEAR"] = cf["WRK_DT"].dt.year
    cf["MONTH"] = cf["WRK_DT"].dt.month

    classes = _class_order(set(tg["CLS"]) | set(cf["ASSET_CLS"]))
    years = sorted(tg["YEAR"].unique().tolist())
    base_year = asof.year if asof.year in years else years[-1]

    # ---- 목표 (전체 포함)
    target = _with_total(tg, ["YEAR"], METRICS)[["YEAR", "CLS"] + METRICS]

    # ---- 월별 실적: 연도 × 월(약정 기준일까지) × 자산군 격자에 실적을 얹는다
    piv = cf.pivot_table(index=["YEAR", "MONTH", "ASSET_CLS"], columns="TX_TYPE",
                         values="AMT_KRW", aggfunc="sum", fill_value=0.0)
    for t in FLOW_TYPES:
        if t not in piv.columns:
            piv[t] = 0.0
    cnt = cf[cf["TX_TYPE"] == "약정"].groupby(["YEAR", "MONTH", "ASSET_CLS"]).size().rename("건수")
    flows = piv[FLOW_TYPES].join(cnt).fillna({"건수": 0}).reset_index().rename(columns={"ASSET_CLS": "CLS"})

    grid = [(y, m, c) for y in sorted(set(years) | set(cf["YEAR"].unique().tolist()))
            for m in range(1, _last_month(y, asof) + 1) for c in classes]
    monthly = pd.DataFrame(grid, columns=["YEAR", "MONTH", "CLS"]).merge(flows, how="left", on=["YEAR", "MONTH", "CLS"])
    monthly[FLOW_TYPES + ["건수"]] = monthly[FLOW_TYPES + ["건수"]].fillna(0.0)
    monthly["순증"] = monthly["집행"] - monthly["분배"]
    monthly["건수"] = monthly["건수"].astype(int)
    monthly = _with_total(monthly, ["YEAR", "MONTH"], METRICS + ["건수"])
    monthly = monthly.sort_values(["YEAR", "CLS", "MONTH"]).reset_index(drop=True)
    cum = monthly.copy()
    cum[METRICS + ["건수"]] = cum.groupby(["YEAR", "CLS"])[METRICS + ["건수"]].cumsum()
    # 집행·분배·순증은 PCAP 기준일 이후 월을 비운다 (없는 자료를 0 으로 보이지 않게)
    after_pcap = (monthly["YEAR"] > asof_flow.year) | ((monthly["YEAR"] == asof_flow.year) & (monthly["MONTH"] > asof_flow.month))
    monthly.loc[after_pcap, PCAP_METRICS] = pd.NA
    cum.loc[after_pcap, PCAP_METRICS] = pd.NA
    monthly = monthly[["YEAR", "MONTH", "CLS"] + METRICS + ["건수"]]
    cum = cum[["YEAR", "MONTH", "CLS"] + METRICS + ["건수"]]

    # ---- KPI: 연도 × 자산군(전체 포함) × 지표. 지표별로 기준월이 다르다
    rows = []
    cum_idx = cum.set_index(["YEAR", "CLS", "MONTH"])
    tg_idx = target.set_index(["YEAR", "CLS"])
    for y in years:
        for c in [ALL] + classes:
            for m in METRICS:
                months = _last_month(y, asof_flow if m in PCAP_METRICS else asof)
                t = float(tg_idx[m].get((y, c), 0.0))
                a = cum_idx[m].get((y, c, months)) if months > 0 else None
                a = float(a) if a is not None and not pd.isna(a) else 0.0
                p = cum_idx[m].get((y - 1, c, months)) if months > 0 else None
                rows.append({"YEAR": y, "CLS": c, "METRIC": m, "MONTHS": months, "TARGET": t, "ACTUAL": a,
                             "RATIO": (a / t) if t else pd.NA, "REMAIN": (t - a) if t else pd.NA,
                             "PREV": float(p) if p is not None and not pd.isna(p) else pd.NA})
    kpi = pd.DataFrame(rows)

    # ---- 펀드·연도별 실적 (원화 + 펀드 통화)
    fy = cf.pivot_table(index=["FUND_KEY", "YEAR"], columns="TX_TYPE",
                        values=["AMT_KRW", "AMT_LOCAL"], aggfunc="sum", fill_value=0.0)
    funds = pd.DataFrame(index=fy.index)
    for t in FLOW_TYPES:
        funds[t] = fy[("AMT_KRW", t)] if ("AMT_KRW", t) in fy.columns else 0.0
        funds[t + "_L"] = fy[("AMT_LOCAL", t)] if ("AMT_LOCAL", t) in fy.columns else 0.0
    funds["순증"] = funds["집행"] - funds["분배"]
    funds["순증_L"] = funds["집행_L"] - funds["분배_L"]
    funds = funds.reset_index().sort_values(["FUND_KEY", "YEAR"])
    funds["FUND"] = funds["FUND_KEY"].map(attrs["FUND_NM"])
    funds["CLS"] = funds["FUND_KEY"].map(attrs["ASSET_CLS"])
    funds["CCY"] = funds["FUND_KEY"].map(attrs["CCY"])
    funds["VINTAGE"] = funds["FUND_KEY"].map(attrs["VINTAGE_YR"])
    funds["VINTAGE"] = funds["VINTAGE"].where(funds["VINTAGE"].notna(), funds["YEAR"]).astype(int)
    funds["누적약정"] = funds.groupby("FUND_KEY")["약정"].cumsum()
    funds["누적집행"] = funds.groupby("FUND_KEY")["집행"].cumsum()
    funds["집행률"] = funds["누적집행"] / funds["누적약정"].replace(0, pd.NA)
    funds = funds[["FUND_KEY", "FUND", "CLS", "CCY", "VINTAGE", "YEAR"] + METRICS + [m + "_L" for m in METRICS]
                  + ["누적약정", "누적집행", "집행률"]].reset_index(drop=True)

    return {
        "asof": asof,
        "asof_flow": asof_flow,
        "flow_freq": "Q",
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

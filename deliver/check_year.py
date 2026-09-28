import pandas as pd


def to_dt(s):
    t = s.astype(str).str.replace("-", "").str[:8]
    return pd.to_datetime(t, format="%Y%m%d", errors="coerce")


cls_of = raw_fund.drop_duplicates("FUND_CD").set_index("FUND_CD")["ASSET_CLS"]

fx = raw_fx.copy()
fx["WRK_DT"] = to_dt(fx["WRK_DT"])
fx = fx.dropna(subset=["WRK_DT"]).drop_duplicates(["WRK_DT", "CURR_ID"], keep="last").sort_values("WRK_DT")

cm = raw_commit.copy()
cm["WRK_DT"] = to_dt(cm["WRK_DT"])
cm["CLS"] = cm["FUND_CD"].map(cls_of).fillna("미분류")

pc = raw_pcap.copy()
pc["WRK_DT"] = to_dt(pc["WRK_DT"])
pc = pc[(pc["CURR_ID"] == "KRW") & pc["WRK_DT"].notna()]
pc = pc.sort_values(["FUND_CD", "WRK_DT", "CURR_TYP"]).drop_duplicates(["FUND_CD", "WRK_DT"], keep="last")


krw_s = fx[fx["CURR_ID"] == "KRW"].set_index("WRK_DT")["USD_RATE"]


def rate(ccy, e):
    """e 이하에서 KRW·통화가 같은 날 모두 있는 마지막 날의 원/1단위와 그 날짜"""
    if ccy == "USD":
        r = krw_s
    else:
        u = fx[fx["CURR_ID"] == ccy].set_index("WRK_DT")["USD_RATE"]
        r = (krw_s / u.replace(0, float("nan"))).dropna()
    r = r[r.index <= e]
    if r.empty:
        return float("nan"), None
    return r.iloc[-1], r.index[-1]


def check(Y, asof):
    s = pd.Timestamp(str(Y) + "0101")
    e = pd.Timestamp(asof)

    c = cm[(cm["WRK_DT"] >= s) & (cm["WRK_DT"] <= e)].copy()
    fxr = {y: rate(y, e) for y in c["CCY"].unique() if y != "KRW"}       # 적용환율 = 기준일(e) 환율
    c["KRW"] = [a if y == "KRW" else l * fxr[y][0] for a, l, y in zip(c["AMT_KRW"], c["AMT_LOCAL"], c["CCY"])]

    cur = pc[(pc["WRK_DT"] >= s) & (pc["WRK_DT"] <= e)].groupby("FUND_CD").last()
    prv = pc[pc["WRK_DT"] < s].groupby("FUND_CD").last()
    cols = ["FUNDED_AMT", "DISTRB_AMT"]
    f = cur[cols] - prv[cols].reindex(cur.index).fillna(0)
    f["CLS"] = pd.Series(f.index, index=f.index).map(cls_of).fillna("미분류")

    out = pd.DataFrame({
        "약정": c.groupby("CLS")["KRW"].sum(),
        "집행": -f.groupby("CLS")["FUNDED_AMT"].sum(),
        "회수": f.groupby("CLS")["DISTRB_AMT"].sum(),
    }).fillna(0)
    out["순증"] = out["집행"] - out["회수"]
    out.loc["합계"] = out.sum()

    print(Y, "| 약정", s.strftime("%Y%m%d"), "~", asof, len(c), "건, 환율 없음", int(c["KRW"].isna().sum()), "건",
          "| PCAP", cur["WRK_DT"].max().strftime("%Y%m%d"), "까지", len(f), "펀드")
    for y, (v, d) in sorted(fxr.items()):
        print("  환율", y, "%.4f" % v, "원/단위", d.strftime("%Y%m%d") if d is not None else "없음")
    with pd.option_context("display.float_format", "{:,.0f}".format):
        print(out)
    print()
    return out


r2025 = check(2025, "20251231")
r2026 = check(2026, "20260731")

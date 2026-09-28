import pandas as pd

# 표 표시: 100만 이상은 쉼표 정수, 그보다 작은 수(환율 등)는 소수 넷째 자리 (e+12 지수 표기 방지)
pd.set_option("display.float_format", lambda x: "{:,.0f}".format(x) if abs(x) >= 1e6 else "{:,.4f}".format(x))


def to_dt(s):
    t = s.astype(str).str.replace("-", "").str[:8]
    return pd.to_datetime(t, format="%Y%m%d", errors="coerce")


def txt(s):
    """코드·통화 문자열 정리: 앞뒤 공백 제거, 대문자"""
    return s.astype(str).str.strip().str.upper()


# 자산군 = 펀드코드 맨 앞 글자 (헤지펀드 H 는 사모벤처)
CODE_CLS = {"P": "사모벤처", "D": "사모벤처", "Z": "사모벤처", "H": "사모벤처",
            "R": "부동산", "I": "인프라", "S": "인프라"}


def cls_of(codes):
    return codes.str[:1].map(CODE_CLS).fillna("미분류")


fx = raw_fx.copy()
fx["WRK_DT"] = to_dt(fx["WRK_DT"])
fx["CURR_ID"] = txt(fx["CURR_ID"])
fx = fx.dropna(subset=["WRK_DT"]).drop_duplicates(["WRK_DT", "CURR_ID"], keep="last").sort_values("WRK_DT")

cm = raw_commit.copy()
cm["WRK_DT"] = to_dt(cm["WRK_DT"])
cm["FUND_CD"] = txt(cm["FUND_CD"])
cm["CCY"] = txt(cm["CCY"])
cm["CLS"] = cls_of(cm["FUND_CD"])

pc = raw_pcap.copy()
pc["WRK_DT"] = to_dt(pc["WRK_DT"])
pc["FUND_CD"] = txt(pc["FUND_CD"])
pc["CURR_ID"] = txt(pc["CURR_ID"])
pc["CURR_TYP"] = txt(pc["CURR_TYP"])
pc = pc[(pc["CURR_ID"] == "KRW") & pc["WRK_DT"].notna()]
pc = pc.sort_values(["FUND_CD", "WRK_DT", "CURR_TYP"]).drop_duplicates(["FUND_CD", "WRK_DT"], keep="last")     # CP 우선


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


def last_val(d, col):
    """펀드별로 col 이 비어 있지 않은 마지막 값 (groupby 없이)"""
    d = d.dropna(subset=[col]).sort_values(["FUND_CD", "WRK_DT"])
    return d.drop_duplicates("FUND_CD", keep="last").set_index("FUND_CD")[col]


def by_cls(v):
    """펀드코드 인덱스 값 → 자산군별 합계 (groupby 없이)"""
    k = cls_of(pd.Series(v.index, index=v.index))
    return pd.Series({x: v[k == x].sum() for x in sorted(k.unique())}, dtype=float)


def check(Y, asof):
    s = pd.Timestamp(str(Y) + "0101")
    e = pd.Timestamp(asof)

    c = cm[(cm["WRK_DT"] >= s) & (cm["WRK_DT"] <= e)].copy()
    fxr = {y: rate(y, e) for y in c["CCY"].unique() if y != "KRW"}       # 적용환율 = 기준일(e) 환율
    c["KRW"] = [a if y == "KRW" else l * fxr[y][0] for a, l, y in zip(c["AMT_KRW"], c["AMT_LOCAL"], c["CCY"])]
    commit = pd.Series({x: c.loc[c["CLS"] == x, "KRW"].sum() for x in sorted(c["CLS"].unique())}, dtype=float)

    now = pc[(pc["WRK_DT"] >= s) & (pc["WRK_DT"] <= e)]      # 올해 PCAP
    old = pc[pc["WRK_DT"] < s]                                # 작년 말까지 PCAP
    inc = {}
    for col in ["FUNDED_AMT", "DISTRB_AMT"]:
        a = last_val(now, col)
        b = last_val(old, col).reindex(a.index).fillna(0)
        inc[col] = by_cls(a - b)                              # 올해 누적 − 작년 말 누적

    out = pd.DataFrame({"약정": commit, "집행": -inc["FUNDED_AMT"], "회수": inc["DISTRB_AMT"]}).fillna(0)
    out["순증"] = out["집행"] - out["회수"]
    out.loc["합계"] = out.sum()

    m = now["WRK_DT"].max()
    print(Y, "| 약정", s.strftime("%Y%m%d"), "~", asof, len(c), "건, 환율 없음", int(c["KRW"].isna().sum()), "건",
          "| PCAP", m.strftime("%Y%m%d") if pd.notna(m) else "없음", "까지", now["FUND_CD"].nunique(), "펀드")
    for y, (v, d) in sorted(fxr.items()):
        print("  환율 1 %s = %.4f 원 (%s)" % (y, v, d.strftime("%Y%m%d") if d is not None else "환율 없음"))
    print(out)
    print()
    return out


r2025 = check(2025, "20251231")
r2026 = check(2026, "20260731")

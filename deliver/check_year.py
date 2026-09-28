import pandas as pd

# 표 표시: 100만 이상은 쉼표 정수, 그보다 작은 수(환율 등)는 소수 넷째 자리 (e+12 지수 표기 방지)
pd.set_option("display.float_format", lambda x: "{:,.0f}".format(x) if abs(x) >= 1e6 else "{:,.4f}".format(x))


def to_dt(s):
    t = s.astype(str).str.strip().str.replace("-", "").str[:8]
    d = pd.to_datetime(t, format="%Y%m%d", errors="coerce")
    xl = t.str.isdigit() & (t.str.len() == 5)                            # 46239 같은 엑셀 날짜 숫자
    n = pd.to_numeric(t.where(xl), errors="coerce")
    return d.fillna(pd.Timestamp("1899-12-30") + pd.to_timedelta(n, unit="D"))


# 자산군 = 펀드코드 맨 앞 글자 (헤지펀드 H 는 사모벤처)
CODE_CLS = {"P": "사모벤처", "D": "사모벤처", "Z": "사모벤처", "H": "사모벤처",
            "R": "부동산", "I": "인프라", "S": "인프라"}


def cls_of(codes):
    if not isinstance(codes, pd.Series):                 # 코드 하나(글자)가 들어와도 동작 (.map(cls_of) 로 불러도 됨)
        return CODE_CLS.get(str(codes)[:1], "미분류")
    return codes.str[:1].map(CODE_CLS).fillna("미분류")


fx = raw_fx.copy()
fx["WRK_DT"] = to_dt(fx["WRK_DT"])
fx = fx.dropna(subset=["WRK_DT"]).drop_duplicates(["WRK_DT", "CURR_ID"], keep="last").sort_values("WRK_DT")

cm = raw_commit.copy()
cm["WRK_DT"] = to_dt(cm["WRK_DT"])
cm["CLS"] = cls_of(cm["FUND_CD"])

pc = raw_pcap.copy()
pc["WRK_DT"] = to_dt(pc["WRK_DT"])
pc = pc[(pc["CURR_TYP"] == "CD") & pc["WRK_DT"].notna()]                       # 로컬(투자 통화) 행만
pc = pc.sort_values(["FUND_CD", "WRK_DT"]).drop_duplicates(["FUND_CD", "WRK_DT"], keep="last")
nocd = sorted(set(raw_pcap["FUND_CD"]) - set(pc["FUND_CD"]))                   # CD 행이 없어 집행·회수에서 빠지는 펀드


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

    now = pc[(pc["WRK_DT"] >= s) & (pc["WRK_DT"] <= e)]      # 올해 PCAP (로컬)
    old = pc[pc["WRK_DT"] < s]                                # 작년 말까지 PCAP (로컬)
    ccy = last_val(now, "CURR_ID")                            # 펀드별 로컬 통화
    for y in ccy.unique():
        if y != "KRW" and y not in fxr:
            fxr[y] = rate(y, e)                               # PCAP 통화도 기준일(e) 환율
    fx_of = ccy.map(lambda y: 1.0 if y == "KRW" else fxr[y][0])
    inc = {}
    for col in ["FUNDED_AMT", "DISTRB_AMT"]:
        a = last_val(now, col)
        b = last_val(old, col).reindex(a.index).fillna(0)
        inc[col] = by_cls((a - b) * fx_of.reindex(a.index))   # (올해 누적 − 작년 말 누적) 로컬 × 기준일 환율

    out = pd.DataFrame({"약정": commit, "집행": -inc["FUNDED_AMT"], "회수": inc["DISTRB_AMT"]}).fillna(0)
    out["순증"] = out["집행"] - out["회수"]
    out.loc["합계"] = out.sum()

    m = now["WRK_DT"].max()
    print(Y, "| 약정", s.strftime("%Y%m%d"), "~", asof, len(c), "건, 환율 없음", int(c["KRW"].isna().sum()), "건",
          "| PCAP", m.strftime("%Y%m%d") if pd.notna(m) else "없음", "까지", now["FUND_CD"].nunique(), "펀드",
          "| CD 행 없는 펀드", len(nocd), "개")
    for y, (v, d) in sorted(fxr.items()):
        print("  환율 1 %s = %.4f 원 (%s)" % (y, v, d.strftime("%Y%m%d") if d is not None else "환율 없음"))
    print(out)
    print()
    return out


r2025 = check(2025, "20251231")
r2026 = check(2026, "20260731")

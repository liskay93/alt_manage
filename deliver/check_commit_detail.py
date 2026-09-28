# 약정 세부내역 (검증 셀 실행 뒤, 같은 노트북에서)
Y, asof = 2026, "20260731"
s, e = pd.Timestamp(str(Y) + "0101"), pd.Timestamp(asof)
pd.set_option("display.max_rows", 500)                    # 행이 많아도 다 보이게

c = cm[(cm["WRK_DT"] >= s) & (cm["WRK_DT"] <= e)].copy()
fxr = {}                                                   # 통화별 기준일 환율
for y in c["CCY"].unique():
    if y != "KRW":
        r = rate(y, e)
        fxr[y] = r[0] if isinstance(r, tuple) else r         # rate 가 (환율, 날짜) 든 환율 숫자든 받음
c["환율"] = [1.0 if y == "KRW" else fxr[y] for y in c["CCY"]]
c["원화"] = [a if y == "KRW" else l * r for a, l, y, r in zip(c["AMT_KRW"], c["AMT_LOCAL"], c["CCY"], c["환율"])]
c["펀드명"] = c["FUND_CD"].map(raw_fund.drop_duplicates("FUND_CD").set_index("FUND_CD")["FUND_NM"])
c["약정일"] = c["WRK_DT"].dt.strftime("%Y%m%d")

d = c[["CLS", "FUND_CD", "펀드명", "약정일", "CCY", "AMT_LOCAL", "환율", "원화"]]
d = d.sort_values(["CLS", "약정일"]).reset_index(drop=True)          # 자산군 → 약정일 오름차순
print(Y, "약정", len(d), "건, 원화 합계", "{:,.0f}".format(d["원화"].sum()))
d

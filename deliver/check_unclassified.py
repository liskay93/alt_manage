# 미분류 점검: 펀드코드 맨 앞 글자가 P·D·Z·H·R·I·S 가 아닌 펀드 (검증 셀 실행 뒤, 같은 노트북에서)
Y, s, e = 2026, pd.Timestamp("20260101"), pd.Timestamp("20260731")

nm = raw_fund.drop_duplicates("FUND_CD").set_index("FUND_CD")["FUND_NM"]
a = cm[(cm["WRK_DT"] >= s) & (cm["WRK_DT"] <= e)]
b = pc[(pc["WRK_DT"] >= s) & (pc["WRK_DT"] <= e)]
codes = pd.Series(sorted(set(a["FUND_CD"]) | set(b["FUND_CD"])))
t = pd.DataFrame({"FUND_CD": codes, "앞글자": codes.str[:1], "자산군": cls_of(codes)})
t["펀드명"] = t["FUND_CD"].map(nm)
print(Y, "펀드", len(t), "개 중 미분류", int((t["자산군"] == "미분류").sum()), "개")
print(t.groupby(["자산군", "앞글자"]).size())
print(t[t["자산군"] == "미분류"].head(30).to_string(index=False))

# 미분류 원인 점검 (검증 셀 실행 뒤, 같은 노트북에서)
Y, s, e = 2026, pd.Timestamp("20260101"), pd.Timestamp("20260731")

pg = fd.drop_duplicates("FUND_CD").set_index("FUND_CD")["PGM_CD"]
nm = fd.drop_duplicates("FUND_CD").set_index("FUND_CD")["FUND_NM"]


def why(code):
    if code not in cls_of.index:
        return "1 펀드 마스터(488NTA)에 코드 없음"
    p = pg.get(code)
    if pd.isna(p) or str(p).strip() == "":
        return "2 CW01 프로그램 코드 없음"
    return "3 프로그램 코드 " + str(p)


a = cm[(cm["WRK_DT"] >= s) & (cm["WRK_DT"] <= e) & (cm["CLS"] == "미분류")]
b = pc[(pc["WRK_DT"] >= s) & (pc["WRK_DT"] <= e)]
b = b[b["FUND_CD"].map(cls_of).fillna("미분류") == "미분류"]
codes = sorted(set(a["FUND_CD"]) | set(b["FUND_CD"]))
t = pd.DataFrame({"FUND_CD": codes})
t["원인"] = t["FUND_CD"].map(why)
t["펀드명"] = t["FUND_CD"].map(nm)
t["약정"] = t["FUND_CD"].isin(a["FUND_CD"])
t["PCAP"] = t["FUND_CD"].isin(b["FUND_CD"])
print(Y, "미분류 펀드", len(t), "개")
print(t["원인"].value_counts().sort_index())
print(t.sort_values(["원인", "FUND_CD"]).head(30).to_string(index=False))
print("PCAP 코드 예", sorted(set(pc["FUND_CD"]))[:5])
print("마스터 코드 예", sorted(cls_of.index)[:5])

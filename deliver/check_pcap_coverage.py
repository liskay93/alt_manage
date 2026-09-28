# 연도·자산군별 PCAP 펀드 수 점검 (검증 셀 실행 뒤): 2024·2025 집행·회수가 너무 작을 때
r = raw_pcap.copy()
r["WRK_DT"] = to_dt(r["WRK_DT"])
r = r[r["WRK_DT"].dt.year.between(2023, 2026)].copy()
r["연도"] = r["WRK_DT"].dt.year
r["CLS"] = cls_of(r["FUND_CD"])
r["구분"] = r["RPRT_NM"].astype(str).str.upper().str.contains("GCM").map({True: "GCM", False: "Fund"}) + "-" + r["CURR_TYP"]
print("제공일(PROV_DT):", sorted(r["PROV_DT"].astype(str).unique()))
print(r.pivot_table(index=["CLS", "연도"], columns="구분", values="FUND_CD", aggfunc="nunique", fill_value=0))   # 펀드 수
k = pc.assign(연도=pc["WRK_DT"].dt.year, CLS=cls_of(pc["FUND_CD"]))
k = k[k["연도"].between(2023, 2026)]
print(k.pivot_table(index="CLS", columns="연도", values="FUND_CD", aggfunc="nunique", fill_value=0))            # 검증 셀이 실제로 쓰는 펀드 수 (CD)
print(cm[cm["WRK_DT"] < pd.Timestamp("20260101")].pivot_table(index="CLS", values="FUND_CD", aggfunc="nunique"))  # 2025년 말까지 약정한 펀드 수

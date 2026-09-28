# PCAP 기준일 점검 (검증 셀 실행 뒤): 2026 집행·회수가 0 일 때
r = raw_pcap.copy()
r["WRK_DT"] = to_dt(r["WRK_DT"])
print("제공일(PROV_DT) 최신:", r["PROV_DT"].max(), "| 기준일 비어 있는 행(NaT):", int(r["WRK_DT"].isna().sum()))
print(pd.crosstab(r["WRK_DT"].dt.strftime("%Y%m%d"), r["CURR_TYP"]).tail(8))     # 기준일 × CD/CP 행 수 (최근 8개)
print("검증 셀 pc(CD 행) 마지막 기준일:", pc["WRK_DT"].max())
print("2026-07-31 USD 환율:", rate("USD", pd.Timestamp("20260731")))

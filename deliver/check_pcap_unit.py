# PCAP 금액 단위 점검 (검증 셀 실행 뒤)
# ① 지금 쓰는 SQL 파일이 금액을 나누는 옛 버전인지
t = open("sql/ALT_PCAP.sql", encoding="utf-8").read()
print("ALT_PCAP.sql:", "나누기 있음 (옛 파일)" if "100000000" in t or "1000000" in t else "나누기 없음")

# ② 같은 펀드의 PCAP 약정액(COMMIT_AMT) ÷ 약정 테이블 약정액(AGRT_AMT, 단위 1)
p = raw_pcap.copy()
p["WRK_DT"] = to_dt(p["WRK_DT"])
p = p.sort_values("WRK_DT").drop_duplicates(["FUND_CD", "CURR_TYP", "CURR_ID"], keep="last")   # 펀드·통화별 최신 기준일
m = p.merge(raw_commit[["FUND_CD", "CCY", "AMT_LOCAL"]], on="FUND_CD", how="inner")
m = m[m["CURR_ID"] == m["CCY"]].copy()                                         # 같은 통화끼리 비교
m["비율"] = m["COMMIT_AMT"] / m["AMT_LOCAL"]
print(m.groupby(["CURR_TYP", "CURR_ID"])["비율"].median().map(lambda x: "%.2e" % x))
print(m[["FUND_CD", "CURR_TYP", "CURR_ID", "COMMIT_AMT", "AMT_LOCAL"]].head(10).to_string(index=False))

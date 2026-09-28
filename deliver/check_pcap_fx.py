# 외화 펀드 한 개의 PCAP 원화 누적 ÷ 로컬 누적 (검증 셀 실행 뒤)
code = "P0001"                                            # 확인할 외화(USD 등) 펀드코드로 바꾸기
f = raw_pcap[raw_pcap["FUND_CD"] == code].copy()
f["WRK_DT"] = to_dt(f["WRK_DT"])
k = f[f["CURR_ID"] == "KRW"].drop_duplicates("WRK_DT", keep="last").set_index("WRK_DT")["FUNDED_AMT"]
l = f[f["CURR_TYP"] == "CD"].drop_duplicates("WRK_DT", keep="last").set_index("WRK_DT")["FUNDED_AMT"]
x = pd.DataFrame({"원화누적": k, "로컬누적": l})
x["원/로컬"] = x["원화누적"] / x["로컬누적"]
x.sort_index()

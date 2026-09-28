# 집행·회수 펀드별 내역 (검증 셀 실행 뒤, 같은 노트북에서)
Y, asof = 2025, "20251231"
col = "FUNDED_AMT"                                        # 회수는 "DISTRB_AMT"
s, e = pd.Timestamp(str(Y) + "0101"), pd.Timestamp(asof)

now = pc[(pc["WRK_DT"] >= s) & (pc["WRK_DT"] <= e)]      # 올해 PCAP
old = pc[pc["WRK_DT"] < s]                                # 작년 말까지 PCAP


def last_dt(d):
    """펀드별로 col 이 비어 있지 않은 마지막 기준일"""
    d = d.dropna(subset=[col]).sort_values(["FUND_CD", "WRK_DT"])
    return d.drop_duplicates("FUND_CD", keep="last").set_index("FUND_CD")["WRK_DT"]


a = last_val(now, col)
t = pd.DataFrame({"자산군": cls_of(pd.Series(a.index, index=a.index)),
                  "올해기준일": last_dt(now).reindex(a.index), "올해누적": a,
                  "작년기준일": last_dt(old).reindex(a.index), "작년누적": last_val(old, col).reindex(a.index)})
t["증분"] = t["올해누적"] - t["작년누적"].fillna(0)
if col == "FUNDED_AMT":
    t["증분"] = -t["증분"]                                 # 집행은 원천이 음수 → 양수로
t["이전없음"] = t["작년기준일"].isna()                      # 작년 말 이전 PCAP 이 없어 누적 전체가 올해 증분으로 잡힌 펀드
print(Y, col, "펀드", len(t), "개 | 증분 합", "{:,.0f}".format(t["증분"].sum()),
      "| 이전없음", int(t["이전없음"].sum()), "개, 증분", "{:,.0f}".format(t.loc[t["이전없음"], "증분"].sum()))
t.sort_values("증분", key=lambda x: x.abs(), ascending=False).head(20)

/* 집행·분배·NAV 분기 스냅샷(PCAP). ALT_Manage 탭이 사용
   원천: FEIAI0432NTA
     WRK_DT(데이터 제공일, 주 단위, YYYY-MM-DD 문자), PCAP_DATE(기준일, 분기말, YYYYMMDD), NPS_CD(펀드코드)
     COMMITMENT_AMT, FUNDED_AMT(음수 부호), DISTRB_AMT, PCAP_AMT(NAV). 모두 PCAP_DATE 기준 누적, 단위 1
     CURR_TYP  CD 투자 통화, CP 보고 통화(CURR_ID 가 USD 또는 KRW)
     RPRT_NM   AS Reported by Fund / AS Reported by GCM 중 GCM 만 사용
   최신 제공일(WRK_DT 최대) 한 벌만. CD/CP 는 long 으로 모두 돌려주고 processor 가 고른다
   단위: KRW 는 억원(나누기 1억), 그 외 통화는 백만(나누기 100만). FUNDED 는 양수로 뒤집는다
   돌려주는 열(대문자): PROV_DT, WRK_DT(=PCAP_DATE), FUND_CD, CURR_ID, CURR_TYP,
                       COMMIT_AMT, FUNDED_AMT, DISTRB_AMT, NAV_AMT */
SELECT TO_DATE(a.WRK_DT, 'YYYY-MM-DD')                                             AS prov_dt
     , TO_DATE(a.PCAP_DATE, 'YYYYMMDD')                                            AS wrk_dt
     , a.NPS_CD                                                                    AS fund_cd
     , UPPER(a.CURR_ID)                                                            AS curr_id
     , UPPER(a.CURR_TYP)                                                           AS curr_typ
     , a.COMMITMENT_AMT / DECODE(UPPER(a.CURR_ID), 'KRW', 100000000, 1000000)      AS commit_amt
     , -1 * a.FUNDED_AMT / DECODE(UPPER(a.CURR_ID), 'KRW', 100000000, 1000000)     AS funded_amt
     , a.DISTRB_AMT / DECODE(UPPER(a.CURR_ID), 'KRW', 100000000, 1000000)          AS distrb_amt
     , a.PCAP_AMT / DECODE(UPPER(a.CURR_ID), 'KRW', 100000000, 1000000)            AS nav_amt
  FROM FEIAI0432NTA a
 WHERE a.WRK_DT = (SELECT MAX(b.WRK_DT) FROM FEIAI0432NTA b)
   AND UPPER(a.RPRT_NM) LIKE '%GCM%'

/* 환율. ALT_Manage 탭이 사용
   원천: FMCBI0006NTA  WRK_DT(기준일, YYYYMMDD, 일별), CURR_CD(통화), MSCI_EXRT(1 USD 당 해당 통화 단위)
   용도: 외화 약정의 원화 환산(약정일 환율). PCAP 에 CD 행이 없는 펀드의 로컬 환산(보조)
   돌려주는 열(대문자): WRK_DT, CURR_ID, USD_RATE
   원/1단위 = USD_RATE(KRW) 나누기 USD_RATE(통화) 는 processor 가 계산. 그래서 KRW 행을 꼭 포함
   통화는 KRW 와 약정 테이블에 있는 펀드 통화만 */
SELECT TO_DATE(a.WRK_DT, 'YYYYMMDD')                                               AS wrk_dt
     , UPPER(a.CURR_CD)                                                            AS curr_id
     , a.MSCI_EXRT                                                                 AS usd_rate
  FROM FMCBI0006NTA a
 WHERE a.WRK_DT >= '20180101'
   AND (UPPER(a.CURR_CD) = 'KRW'
        OR UPPER(a.CURR_CD) IN (SELECT DISTINCT UPPER(f.CURR_CD) FROM FEIAI0488NTA f WHERE f.CURR_CD IS NOT NULL))

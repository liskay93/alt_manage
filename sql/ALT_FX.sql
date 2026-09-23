-- 환율 (체크리스트 #6). ALT_Manage 탭이 사용
-- 원천: FMCBI0006NTA — WRK_DT(기준일, YYYYMMDD 문자, 일별), CURR_CD(통화), MSCI_EXRT(환율: 1 USD 당 해당 통화 단위. 예 KRW 1350, EUR 0.92)
-- 용도: PCAP(FEIAI0432NTA)에 CD(투자 통화) 행이 빠진 펀드의 집행·분배 로컬 금액을 원화 ÷ 환율로 환산 (보조 경로)
-- 돌려주는 열(대문자): WRK_DT, CURR_ID, USD_RATE(1 USD 당 통화 단위)
--   1단위당 원화(KRW/통화) = USD_RATE(KRW) ÷ USD_RATE(통화) 는 processor 가 계산한다. 그래서 KRW 행을 꼭 포함한다
--   통화는 KRW 와 약정 테이블(FEIAI0488NTA)에 있는 펀드 통화만 가져온다 (일별이라 범위를 줄임)
SELECT TO_DATE(a.WRK_DT, 'YYYYMMDD')                                      AS wrk_dt
     , UPPER(a.CURR_CD)                                                   AS curr_id
     , a.MSCI_EXRT                                                        AS usd_rate
  FROM FMCBI0006NTA a
 WHERE a.WRK_DT >= '20180101'
   AND (UPPER(a.CURR_CD) = 'KRW'
        OR UPPER(a.CURR_CD) IN (SELECT DISTINCT UPPER(f.CURR_CD) FROM FEIAI0488NTA f WHERE f.CURR_CD IS NOT NULL))

-- 환율 (체크리스트 #6). ALT_Manage 탭이 사용
-- 원천: FMCBI0006NTA — WRK_DT(기준일), MSCI_EXRT(환율: 1 USD 당 해당 통화 단위. 예 KRW 1350, EUR 0.92)
-- 용도: PCAP(FEIAI0432NTA)에 CD(투자 통화) 행이 빠진 펀드의 집행·분배 로컬 금액을 원화 ÷ 환율로 환산 (보조 경로)
-- 돌려주는 열(대문자): WRK_DT, CURR_ID, USD_RATE(1 USD 당 통화 단위)
--   1단위당 원화(KRW/통화) = USD_RATE(KRW) ÷ USD_RATE(통화) 는 processor 가 계산한다. KRW 행이 꼭 포함돼야 한다
-- 확인 중: 통화 코드 컬럼 이름, WRK_DT 형식(YYYYMMDD 문자인지 DATE 인지), USD 행(=1) 존재 여부, 일별인지 월말인지
-- ※ <<...>> 는 확인 전 자리표시자이며 추측한 이름이 아니다
SELECT TO_DATE(a.WRK_DT, 'YYYYMMDD')                                      AS wrk_dt       -- DATE 형이면 a.WRK_DT, 'YYYY-MM-DD' 면 형식 변경
     , UPPER(a.<<통화코드>>)                                                AS curr_id
     , a.MSCI_EXRT                                                        AS usd_rate
  FROM FMCBI0006NTA a
 WHERE UPPER(a.<<통화코드>>) IN ('KRW', 'USD', 'EUR', 'JPY', 'GBP', 'AUD')
   AND a.WRK_DT >= '20180101'

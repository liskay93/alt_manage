-- 환율 (선택, 체크리스트 #6). ALT_Manage 탭이 사용
-- 용도: PCAP(FEIAI0432NTA)에 펀드 통화 행이 없는 펀드(예: EUR 펀드가 USD 로만 보고될 때)의
--       집행·분배 로컬 통화 금액을 원화 증분 ÷ 분기말 환율로 환산
-- 돌려주는 열(대문자): WRK_DT(일자), CURR_ID(통화), RATE(원/1단위)
-- ※ 테이블명·컬럼명은 확인 전 자리표시자. 환율 테이블이 없으면 이 파일을 쓰지 않고 raw_fx=None 으로 둔다
SELECT TO_DATE(a.<<기준일자>>, 'YYYYMMDD')                                 AS wrk_dt
     , UPPER(a.<<통화코드>>)                                                AS curr_id
     , a.<<환율_원_per_1단위>>                                              AS rate
  FROM <<환율_테이블>> a
 WHERE a.<<통화코드>> IN ('USD', 'EUR')

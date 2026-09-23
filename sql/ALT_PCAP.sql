-- 집행·분배·NAV 분기 스냅샷(PCAP). ALT_Manage 탭이 사용
-- 원천: FEIAI0432NTA
--   WRK_DT(데이터 제공일, 주 단위, 'YYYY-MM-DD'), PCAP_DATE(기준일, 분기말), NPS_CD(펀드코드)
--   COMMITMENT_AMT(약정), FUNDED_AMT(집행, 음수 부호), DISTRB_AMT(분배), PCAP_AMT(NAV) — 모두 PCAP_DATE 기준 누적 (확인 완료)
--   CURR_TYP: CD = 투자 통화(EUR/USD/JPY/KRW…), CP = 보고 통화(CURR_ID 가 USD 또는 KRW) — 확인 완료
--   RPRT_NM('AS Reported by Fund' / 'AS Reported by GCM')
-- 규칙
--   최신 제공일(WRK_DT 최대) 한 벌, GCM 보고 기준만 쓴다
--   통화 유형(CD/CP)은 SQL 에서 고르지 않고 long 으로 모두 돌려주며 processor 가 원화(CP-KRW)·펀드통화(CD)를 고른다
-- 돌려주는 열(대문자): PROV_DT, WRK_DT(=PCAP_DATE), FUND_CD, CURR_ID, CURR_TYP,
--                     COMMIT_AMT, FUNDED_AMT(양수로 뒤집음), DISTRB_AMT, NAV_AMT
-- 확인 중: 금액 단위(원/천/백만 → 억원·백만으로 나누는 값), PCAP_DATE 가 문자인지 DATE 인지, 이력 시작 시점, STATE_DATE 중복 여부
-- ※ <<...>> 는 확인 전 자리표시자이며 추측한 이름이 아니다
SELECT TO_DATE(a.WRK_DT, 'YYYY-MM-DD')                                    AS prov_dt      -- WRK_DT 가 DATE 형이면 a.WRK_DT
     , TO_DATE(a.PCAP_DATE, 'YYYY-MM-DD')                                 AS wrk_dt       -- 기준일(분기말). DATE 형이면 a.PCAP_DATE
     , a.NPS_CD                                                           AS fund_cd
     , UPPER(a.CURR_ID)                                                   AS curr_id
     , UPPER(a.CURR_TYP)                                                  AS curr_typ
     , a.COMMITMENT_AMT / <<단위 나누기>>                                   AS commit_amt
     , -1 * a.FUNDED_AMT / <<단위 나누기>>                                  AS funded_amt   -- 원천은 음수 부호
     , a.DISTRB_AMT / <<단위 나누기>>                                       AS distrb_amt
     , a.PCAP_AMT / <<단위 나누기>>                                         AS nav_amt
  FROM FEIAI0432NTA a
 WHERE a.WRK_DT = (SELECT MAX(b.WRK_DT) FROM FEIAI0432NTA b)
   AND UPPER(a.RPRT_NM) LIKE '%GCM%'                                                       -- 'AS Reported by GCM' 만

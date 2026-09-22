-- 대체투자 현금흐름(약정·집행·분배) long 추출. ALT_Manage 탭이 사용
-- 돌려주는 열(대문자): WRK_DT, FUND_CD, FUND_NM, ASSET_CLS, CCY, TX_TYPE, AMT_KRW, AMT_LOCAL
--   TX_TYPE  : 약정 | 집행 | 분배
--   AMT_KRW  : 원화 억원
--   AMT_LOCAL: 펀드 통화 금액 (KRW 펀드는 억원, 외화 펀드는 백만)
-- (1) 약정 — 확인된 원천: FEIAI0488NTA
--     확인 중: AGRT_AMT 가 원화인지 CURR_CD 기준인지, 단위(원/천원/백만/억), AGRT_DT 가 문자(YYYYMMDD)인지 DATE 인지
-- (2) 집행, (3) 분배 — 테이블 확인 전, 자리표시자
-- ※ <<...>> 는 확인 전 자리표시자이며 추측한 이름이 아니다
SELECT TO_DATE(a.AGRT_DT, 'YYYYMMDD')                                     AS wrk_dt       -- AGRT_DT 가 DATE 형이면 a.AGRT_DT
     , a.NPS_FUND_CD                                                      AS fund_cd
     , a.NPS_FUND_CD                                                      AS fund_nm      -- <<펀드명>> 확인 후 교체
     , '미분류'                                                            AS asset_cls    -- <<자산군 DECODE>> 확인 후 교체
     , NVL(a.CURR_CD, 'KRW')                                              AS ccy
     , '약정'                                                             AS tx_type
     , a.AGRT_AMT / <<원화 환산 나누기: 원이면 100000000>>                  AS amt_krw      -- AGRT_AMT 통화·단위 확인 후 교체
     , a.AGRT_AMT / <<로컬 단위 나누기: 외화 원단위면 1000000>>              AS amt_local    -- 〃
  FROM FEIAI0488NTA a
UNION ALL
SELECT TO_DATE(b.<<납입일자_YYYYMMDD>>, 'YYYYMMDD')                         AS wrk_dt
     , b.<<펀드코드>>                                                      AS fund_cd
     , b.<<펀드코드>>                                                      AS fund_nm
     , '미분류'                                                            AS asset_cls
     , NVL(b.<<통화코드>>, 'KRW')                                           AS ccy
     , '집행'                                                             AS tx_type
     , b.<<원화 집행금액>> / <<나누기>>                                      AS amt_krw
     , b.<<로컬 집행금액>> / <<나누기>>                                      AS amt_local
  FROM <<집행_테이블>> b
UNION ALL
SELECT TO_DATE(c.<<분배일자_YYYYMMDD>>, 'YYYYMMDD')                         AS wrk_dt
     , c.<<펀드코드>>                                                      AS fund_cd
     , c.<<펀드코드>>                                                      AS fund_nm
     , '미분류'                                                            AS asset_cls
     , NVL(c.<<통화코드>>, 'KRW')                                           AS ccy
     , '분배'                                                             AS tx_type
     , c.<<원화 분배금액>> / <<나누기>>                                      AS amt_krw
     , c.<<로컬 분배금액>> / <<나누기>>                                      AS amt_local
  FROM <<분배_테이블>> c

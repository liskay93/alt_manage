-- 약정 내역. ALT_Manage 탭이 사용
-- 원천: FEIAI0488NTA — NPS_FUND_CD(펀드코드), VNTG_YR(빈티지), CURR_CD(통화), AGRT_DT(약정일자), AGRT_AMT(약정금액)
-- 돌려주는 열(대문자): WRK_DT, FUND_CD, CCY, AMT_KRW(원화 억원), AMT_LOCAL(펀드 통화: KRW 는 억원, 외화는 백만)
-- 확인 중: AGRT_AMT 가 원화인지 CURR_CD 기준인지, 단위(원/천원/백만/억), AGRT_DT 가 문자(YYYYMMDD)인지 DATE 인지
-- ※ <<...>> 는 확인 전 자리표시자이며 추측한 이름이 아니다
SELECT TO_DATE(a.AGRT_DT, 'YYYYMMDD')                                     AS wrk_dt       -- AGRT_DT 가 DATE 형이면 a.AGRT_DT
     , a.NPS_FUND_CD                                                      AS fund_cd
     , NVL(a.CURR_CD, 'KRW')                                              AS ccy
     , a.AGRT_AMT / <<원화 환산 나누기: 원이면 100000000>>                  AS amt_krw      -- AGRT_AMT 통화·단위 확인 후 교체
     , a.AGRT_AMT / <<로컬 단위 나누기: 외화 원단위면 1000000>>              AS amt_local    -- 〃
  FROM FEIAI0488NTA a

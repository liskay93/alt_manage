-- 펀드 마스터. ALT_Manage 탭이 사용
-- 돌려주는 열(대문자): FUND_CD, FUND_NM, ASSET_CLS, PGM_CD, CCY, VINTAGE_YR
-- 확인된 원천: FEIAI0488NTA — NPS_FUND_CD(펀드코드), VNTG_YR(빈티지), CURR_CD(통화), AGRT_DT(약정일자), AGRT_AMT(약정금액)
-- 자산군: AVTV_PGM_CD(액티브 프로그램 코드) 앞 3자리 — XPV 사모(→사모벤처), XRE 부동산, XIF 인프라 (형님 엑셀, docs/AVTV_PGM_CD.csv)
--         세부 분류명(Buyout, Core RE Equity …)은 processor 의 PGM_NAMES 사전이 붙인다
-- 확인 중: AVTV_PGM_CD 가 FEIAI0488NTA 에 있는지(다른 테이블이면 JOIN), 펀드명 컬럼
SELECT a.NPS_FUND_CD                                                      AS fund_cd
     , a.NPS_FUND_CD                                                      AS fund_nm      -- <<펀드명 컬럼>> 확인 후 교체
     , DECODE(SUBSTR(a.AVTV_PGM_CD, 1, 3), 'XPV', '사모벤처'
                                        , 'XRE', '부동산'
                                        , 'XIF', '인프라'
                                        , '미분류')                          AS asset_cls    -- AVTV_PGM_CD 위치 확인 후 확정
     , a.AVTV_PGM_CD                                                      AS pgm_cd
     , NVL(a.CURR_CD, 'KRW')                                              AS ccy
     , MIN(a.VNTG_YR)                                                     AS vintage_yr
  FROM FEIAI0488NTA a
 GROUP BY a.NPS_FUND_CD, a.AVTV_PGM_CD, NVL(a.CURR_CD, 'KRW')

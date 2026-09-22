-- 펀드 마스터. ALT_Manage 탭이 사용
-- 돌려주는 열(대문자): FUND_CD, FUND_NM, ASSET_CLS, CCY, VINTAGE_YR
-- 확인된 원천: FEIAI0488NTA — NPS_FUND_CD(펀드코드), VNTG_YR(빈티지), CURR_CD(통화), AGRT_DT(약정일자), AGRT_AMT(약정금액)
-- 확인 전(자리표시자): 펀드명, 자산군 코드가 있는 테이블. 확인되면 JOIN 을 채운다
--   그때까지는 FUND_NM 에 펀드코드를 그대로 넣고, ASSET_CLS 는 '미분류' 로 둔다
SELECT a.NPS_FUND_CD                                                      AS fund_cd
     , a.NPS_FUND_CD                                                      AS fund_nm      -- <<펀드명 컬럼>> 확인 후 교체
     , '미분류'                                                            AS asset_cls    -- <<자산군 DECODE>> 확인 후 교체
     , NVL(a.CURR_CD, 'KRW')                                              AS ccy
     , MIN(a.VNTG_YR)                                                     AS vintage_yr
  FROM FEIAI0488NTA a
 GROUP BY a.NPS_FUND_CD, NVL(a.CURR_CD, 'KRW')

-- 펀드 마스터. ALT_Manage 탭이 사용
-- 돌려주는 열(대문자): FUND_CD, FUND_NM, ASSET_CLS, PGM_CD, CCY, VINTAGE_YR
-- 원천
--   FEIAI0488NTA — NPS_FUND_CD(펀드코드), VNTG_YR(빈티지), CURR_CD(통화), AVTV_PGM_CD(액티브 프로그램 코드)
--   FEIAI0432NTA — NPS_CD(펀드코드), DEAL_NM(펀드명). 펀드당 행이 많으므로 최신 제공일에서 코드당 하나만
-- 자산군: AVTV_PGM_CD 앞 3자리 — XPV 사모(→사모벤처), XRE 부동산, XIF 인프라 (형님 엑셀, docs/AVTV_PGM_CD.csv)
--         세부 분류명(Buyout, Core RE Equity …)은 processor 의 PGM_NAMES 사전이 붙인다
-- 확인 중: AVTV_PGM_CD 가 FEIAI0488NTA 에 있는지 (다른 테이블이면 JOIN 으로 바꾼다)
SELECT a.NPS_FUND_CD                                                      AS fund_cd
     , NVL(n.DEAL_NM, a.NPS_FUND_CD)                                      AS fund_nm      -- 이름이 없으면 코드
     , DECODE(SUBSTR(a.AVTV_PGM_CD, 1, 3), 'XPV', '사모벤처'
                                        , 'XRE', '부동산'
                                        , 'XIF', '인프라'
                                        , '미분류')                          AS asset_cls
     , a.AVTV_PGM_CD                                                      AS pgm_cd
     , NVL(a.CURR_CD, 'KRW')                                              AS ccy
     , MIN(a.VNTG_YR)                                                     AS vintage_yr
  FROM FEIAI0488NTA a
  LEFT JOIN (SELECT p.NPS_CD, MAX(p.DEAL_NM) AS DEAL_NM
               FROM FEIAI0432NTA p
              WHERE p.WRK_DT = (SELECT MAX(b.WRK_DT) FROM FEIAI0432NTA b)
              GROUP BY p.NPS_CD) n
    ON n.NPS_CD = a.NPS_FUND_CD
 GROUP BY a.NPS_FUND_CD, n.DEAL_NM, a.AVTV_PGM_CD, NVL(a.CURR_CD, 'KRW')

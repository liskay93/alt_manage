-- 펀드 마스터. ALT_Manage 탭이 사용
-- 돌려주는 열(대문자): FUND_CD, FUND_NM, ASSET_CLS, PGM_CD, CCY, VINTAGE_YR
-- 원천
--   FEIAI0488NTA — NPS_FUND_CD(펀드코드), VNTG_YR(빈티지), CURR_CD(통화)
--   FEIAI0432NTA — NPS_CD(펀드코드), DEAL_NM(펀드명). 펀드당 행이 많으므로 최신 제공일에서 코드당 하나만
--   MAAMC0101DTM — FUND_CD(펀드코드), AVTV_PGM_CD(액티브 프로그램 코드). 펀드코드로 조인
-- 자산군: AVTV_PGM_CD 앞 3자리 — XPV 사모(→사모벤처), XRE 부동산, XIF 인프라 (형님 엑셀, docs/AVTV_PGM_CD.csv)
--         세부 분류명(Buyout, Core RE Equity …)은 processor 의 PGM_NAMES 사전이 붙인다
-- 확인 사항: 펀드코드 컬럼을 'funcd_cd' 로 알려 주셔서 FUND_CD 로 적었다. 실제 이름이 다르면 아래 두 곳만 바꾼다
--           펀드당 행이 여러 개여도 MAX 로 하나만 쓴다 (코드가 바뀐 이력이 있으면 최신 행 기준으로 바꿔야 함)
SELECT a.NPS_FUND_CD                                                      AS fund_cd
     , NVL(n.DEAL_NM, a.NPS_FUND_CD)                                      AS fund_nm      -- 이름이 없으면 코드
     , DECODE(SUBSTR(m.AVTV_PGM_CD, 1, 3), 'XPV', '사모벤처'
                                        , 'XRE', '부동산'
                                        , 'XIF', '인프라'
                                        , '미분류')                          AS asset_cls
     , m.AVTV_PGM_CD                                                      AS pgm_cd
     , NVL(a.CURR_CD, 'KRW')                                              AS ccy
     , MIN(a.VNTG_YR)                                                     AS vintage_yr
  FROM FEIAI0488NTA a
  LEFT JOIN (SELECT p.NPS_CD, MAX(p.DEAL_NM) AS DEAL_NM
               FROM FEIAI0432NTA p
              WHERE p.WRK_DT = (SELECT MAX(b.WRK_DT) FROM FEIAI0432NTA b)
              GROUP BY p.NPS_CD) n
    ON n.NPS_CD = a.NPS_FUND_CD
  LEFT JOIN (SELECT q.FUND_CD, MAX(q.AVTV_PGM_CD) AS AVTV_PGM_CD
               FROM MAAMC0101DTM q
              GROUP BY q.FUND_CD) m
    ON m.FUND_CD = a.NPS_FUND_CD
 GROUP BY a.NPS_FUND_CD, n.DEAL_NM, m.AVTV_PGM_CD, NVL(a.CURR_CD, 'KRW')

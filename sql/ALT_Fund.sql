/* 펀드 마스터. ALT_Manage 탭이 사용
   돌려주는 열(대문자): FUND_CD, FUND_NM, ASSET_CLS, PGM_CD, CCY, VINTAGE_YR
   원천
     FEIAI0488NTA  NPS_FUND_CD(펀드코드), DEAL_NM(펀드명), VNTG_YR(빈티지), CURR_CD(통화). 펀드당 1행
     MAAMC0101DTM_CW01  FUND_CD(펀드코드), ATVT_PGM_FUND_CD(액티브 프로그램 코드)
   자산군: ATVT_PGM_FUND_CD 앞 3자리 XPV 사모벤처, XRE 부동산, XIF 인프라
   펀드명이 없으면 펀드코드, 프로그램 코드가 없으면 자산군은 미분류
   조인은 Oracle (+) 외부조인 */
SELECT a.NPS_FUND_CD                                             AS fund_cd
     , NVL(a.DEAL_NM, a.NPS_FUND_CD)                             AS fund_nm
     , DECODE(SUBSTR(m.ATVT_PGM_FUND_CD, 1, 3), 'XPV', '사모벤처'
                                             , 'XRE', '부동산'
                                             , 'XIF', '인프라'
                                             , '미분류')          AS asset_cls
     , m.ATVT_PGM_FUND_CD                                        AS pgm_cd
     , NVL(UPPER(a.CURR_CD), 'KRW')                              AS ccy
     , a.VNTG_YR                                                 AS vintage_yr
  FROM FEIAI0488NTA a
     , (SELECT q.FUND_CD, MAX(q.ATVT_PGM_FUND_CD) AS atvt_pgm_fund_cd
          FROM MAAMC0101DTM_CW01 q
         GROUP BY q.FUND_CD) m
 WHERE m.FUND_CD(+) = a.NPS_FUND_CD

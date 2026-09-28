/* 펀드 마스터. ALT_Manage 탭이 사용
   돌려주는 열(대문자): FUND_CD, FUND_NM, ASSET_CLS, PGM_CD, CCY, VINTAGE_YR
   원천
     FEIAI0488NTA  NPS_FUND_CD(펀드코드), DEAL_NM(펀드명), VNTG_YR(빈티지), CURR_CD(통화). 펀드당 1행
     MAAMC0101DTM_CW01  FUND_CD(펀드코드), ATVT_PGM_FUND_CD(액티브 프로그램 코드) — 세부 분류명에만 사용
   자산군: 펀드코드(NPS_FUND_CD) 맨 앞 글자 (대소문자·앞뒤 공백 무시)
     P, D, Z, H(헤지펀드) 사모벤처 / R 부동산 / I, S 인프라 / 그 외 미분류
   펀드명이 없으면 펀드코드
   펀드코드 보정: 원천(FEIAI0488NTA) 오류 R4214 → R4124. 다른 코드도 틀리면 DECODE 에 ('틀린코드', '맞는코드') 쌍을 추가
   조인은 Oracle (+) 외부조인 */
SELECT a.NPS_FUND_CD                                             AS fund_cd
     , NVL(a.DEAL_NM, a.NPS_FUND_CD)                             AS fund_nm
     , DECODE(UPPER(SUBSTR(TRIM(a.NPS_FUND_CD), 1, 1)), 'P', '사모벤처'
                                                     , 'D', '사모벤처'
                                                     , 'Z', '사모벤처'
                                                     , 'H', '사모벤처'
                                                     , 'R', '부동산'
                                                     , 'I', '인프라'
                                                     , 'S', '인프라'
                                                     , '미분류')      AS asset_cls
     , UPPER(TRIM(m.ATVT_PGM_FUND_CD))                           AS pgm_cd
     , NVL(UPPER(a.CURR_CD), 'KRW')                              AS ccy
     , a.VNTG_YR                                                 AS vintage_yr
  FROM (SELECT DECODE(f.NPS_FUND_CD, 'R4214', 'R4124', f.NPS_FUND_CD) AS nps_fund_cd
             , f.DEAL_NM, f.CURR_CD, f.VNTG_YR
          FROM FEIAI0488NTA f) a
     , (SELECT q.FUND_CD, MAX(q.ATVT_PGM_FUND_CD) AS atvt_pgm_fund_cd
          FROM MAAMC0101DTM_CW01 q
         GROUP BY q.FUND_CD) m
 WHERE m.FUND_CD(+) = a.NPS_FUND_CD

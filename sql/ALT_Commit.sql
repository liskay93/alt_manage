/* 약정 내역. ALT_Manage 탭이 사용
   원천: FEIAI0488NTA  NPS_FUND_CD(펀드코드), CURR_CD(통화), AGRT_DT(약정일자 YYYYMMDD), AGRT_AMT(약정금액). 펀드당 1행
   금액은 원본 그대로 (CURR_CD 통화 기준, 단위 1). 억원·백만 변환은 processor 가 한다
   날짜는 YYYYMMDD 문자열. 엑셀 날짜 숫자(예: 46239 = 20260805, 1899-12-30 기준 일수)로 들어간 5자리 값만 YYYYMMDD 로 바꾼다
   형식이 잘못된 값이 섞여 있어 TO_DATE 는 쓰지 않고 processor 가 변환한다
   펀드코드 보정: 원천(FEIAI0488NTA) 오류 R4214 → R4124. 다른 코드도 틀리면 DECODE 에 ('틀린코드', '맞는코드') 쌍을 추가
   돌려주는 열(대문자): WRK_DT, FUND_CD, CCY, AMT_LOCAL, AMT_KRW
     AMT_LOCAL  펀드 통화 금액 (원본)
     AMT_KRW    원화 금액. KRW 펀드만 채우고 외화는 NULL. processor 가 적용환율(약정 연도 12/31 과 기준일 중 이른 날)로 환산 */
SELECT CASE WHEN REGEXP_LIKE(TRIM(a.AGRT_DT), '^[0-9]{5}$')
            THEN TO_CHAR(DATE '1899-12-30' + TO_NUMBER(TRIM(a.AGRT_DT)), 'YYYYMMDD')
            ELSE TRIM(a.AGRT_DT) END                          AS wrk_dt
     , a.NPS_FUND_CD                                          AS fund_cd
     , NVL(UPPER(a.CURR_CD), 'KRW')                           AS ccy
     , a.AGRT_AMT                                             AS amt_local
     , CASE WHEN NVL(UPPER(a.CURR_CD), 'KRW') = 'KRW'
            THEN a.AGRT_AMT END                               AS amt_krw
  FROM (SELECT DECODE(f.NPS_FUND_CD, 'R4214', 'R4124', f.NPS_FUND_CD) AS nps_fund_cd
             , f.AGRT_DT, f.CURR_CD, f.AGRT_AMT
          FROM FEIAI0488NTA f) a
 WHERE a.AGRT_AMT IS NOT NULL

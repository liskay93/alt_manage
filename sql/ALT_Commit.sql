/* 약정 내역. ALT_Manage 탭이 사용
   원천: FEIAI0488NTA  NPS_FUND_CD(펀드코드), CURR_CD(통화), AGRT_DT(약정일자 YYYYMMDD), AGRT_AMT(약정금액). 펀드당 1행
   AGRT_AMT 는 CURR_CD 통화 기준, 단위 1
   돌려주는 열(대문자): WRK_DT, FUND_CD, CCY, AMT_LOCAL, AMT_KRW
     AMT_LOCAL  펀드 통화 금액. KRW 는 억원(나누기 1억), 외화는 백만(나누기 100만)
     AMT_KRW    원화 억원. KRW 펀드만 채우고 외화는 NULL. processor 가 약정일 환율로 환산 */
SELECT TO_DATE(a.AGRT_DT, 'YYYYMMDD')                                              AS wrk_dt
     , a.NPS_FUND_CD                                                               AS fund_cd
     , NVL(UPPER(a.CURR_CD), 'KRW')                                                AS ccy
     , a.AGRT_AMT / DECODE(NVL(UPPER(a.CURR_CD), 'KRW'), 'KRW', 100000000, 1000000) AS amt_local
     , CASE WHEN NVL(UPPER(a.CURR_CD), 'KRW') = 'KRW'
            THEN a.AGRT_AMT / 100000000 END                                        AS amt_krw
  FROM FEIAI0488NTA a
 WHERE a.AGRT_AMT IS NOT NULL

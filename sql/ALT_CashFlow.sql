-- 대체투자 현금흐름(약정·집행·분배) long 추출. ALT_Manage 탭이 사용
-- 돌려주는 열(대문자): WRK_DT, FUND_NM, ASSET_CLS, CCY, TX_TYPE, AMT_KRW, AMT_LOCAL
--   TX_TYPE  : 약정 | 집행 | 분배
--   AMT_KRW  : 원화 억원
--   AMT_LOCAL: 펀드 통화 금액 (KRW 펀드는 억원, 외화 펀드는 백만)
-- ※ 테이블명·컬럼명·코드값은 확인 전이라 <<...>> 자리표시자로 두었다. 추측하지 않았으며, 확인 후 교체한다.
--    약정·집행·분배가 서로 다른 테이블이면 아래 SELECT 를 UNION ALL 로 이어 붙인다.
SELECT TO_DATE(a.<<거래일자_YYYYMMDD>>, 'YYYYMMDD')                              AS wrk_dt
     , a.<<펀드명>>                                                              AS fund_nm
     , DECODE(a.<<자산군코드>>, '<<사모벤처코드>>', '사모벤처'
                             , '<<부동산코드>>',   '부동산'
                             , '<<인프라코드>>',   '인프라'
                             , a.<<자산군코드>>)                                 AS asset_cls
     , NVL(a.<<통화코드>>, 'KRW')                                                AS ccy
     , DECODE(a.<<거래유형코드>>, '<<약정코드>>', '약정'
                               , '<<집행코드>>', '집행'
                               , '<<분배코드>>', '분배')                         AS tx_type
     , a.<<원화금액_원>> / 100000000                                             AS amt_krw
     , CASE WHEN NVL(a.<<통화코드>>, 'KRW') = 'KRW'
            THEN a.<<원화금액_원>> / 100000000
            ELSE a.<<로컬금액>> / 1000000 END                                    AS amt_local
  FROM <<현금흐름_테이블>> a
 WHERE a.<<거래일자_YYYYMMDD>> >= '20180101'

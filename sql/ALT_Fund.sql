-- 펀드 마스터. ALT_Manage 탭이 사용 (선택: 없으면 processor 가 현금흐름에서 자산군·통화·약정연도를 유추)
-- 돌려주는 열(대문자): FUND_NM, ASSET_CLS, CCY, VINTAGE_YR
-- ※ 테이블명·컬럼명·코드값은 확인 전이라 <<...>> 자리표시자
SELECT a.<<펀드명>>                                                              AS fund_nm
     , DECODE(a.<<자산군코드>>, '<<사모벤처코드>>', '사모벤처'
                             , '<<부동산코드>>',   '부동산'
                             , '<<인프라코드>>',   '인프라'
                             , a.<<자산군코드>>)                                 AS asset_cls
     , NVL(a.<<통화코드>>, 'KRW')                                                AS ccy
     , a.<<약정연도>>                                                            AS vintage_yr
  FROM <<펀드마스터_테이블>> a

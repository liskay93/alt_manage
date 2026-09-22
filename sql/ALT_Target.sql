-- 연도·자산군별 목표(약정·집행·분배·순증). ALT_Manage 탭이 사용
-- 돌려주는 열(대문자): TARGET_YR, ASSET_CLS, COMMIT_KRW, DRAW_KRW, DIST_KRW, NET_KRW (모두 원화 억원)
--   NET_KRW 가 NULL 이면 processor 가 DRAW_KRW − DIST_KRW 로 채운다
-- ※ 테이블명·컬럼명·코드값은 확인 전이라 <<...>> 자리표시자. 목표가 DB 에 없으면 CSV/엑셀로 대체 가능
SELECT a.<<목표연도>>                                                            AS target_yr
     , DECODE(a.<<자산군코드>>, '<<사모벤처코드>>', '사모벤처'
                             , '<<부동산코드>>',   '부동산'
                             , '<<인프라코드>>',   '인프라'
                             , a.<<자산군코드>>)                                 AS asset_cls
     , a.<<약정목표_원>> / 100000000                                             AS commit_krw
     , a.<<집행목표_원>> / 100000000                                             AS draw_krw
     , a.<<분배목표_원>> / 100000000                                             AS dist_krw
     , a.<<순증목표_원>> / 100000000                                             AS net_krw
  FROM <<목표_테이블>> a

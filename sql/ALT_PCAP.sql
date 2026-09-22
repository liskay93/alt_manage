-- 집행·분배·NAV 분기 스냅샷(PCAP). ALT_Manage 탭이 사용
-- 원천: FEIAI0432NTA — WRK_DT(데이터 제공일, 주 단위), PCAP_DATE(기준일, 제공일 기준 과거 분기별),
--       NPS_CD(펀드코드), COMMITMENT_AMT(약정), FUNDED_AMT(집행, 음수 부호), DISTRB_AMT(분배), PCAP_AMT(NAV)
-- 최신 제공일(WRK_DT 최대) 한 벌만 쓴다. 기준일(PCAP_DATE)별 금액은 설립 이후 누적으로 가정하고
--   processor 가 분기 증분으로 바꾼다 (기간 증분이면 process_ALT_Manage(..., pcap_cumulative=False))
-- 돌려주는 열(대문자): PROV_DT, WRK_DT(=PCAP_DATE), FUND_CD, COMMIT_KRW,
--                     FUNDED_KRW, FUNDED_LOCAL, DISTRB_KRW, DISTRB_LOCAL, NAV_KRW
--   원화는 억원, 펀드 통화는 KRW 펀드면 억원·외화면 백만. FUNDED 는 양수로 뒤집어 돌려준다
-- 확인 중: 금액이 펀드 통화인지 원화인지, 단위, 누적인지 기간 증분인지, PCAP_DATE 형식
-- ※ <<...>> 는 확인 전 자리표시자이며 추측한 이름이 아니다
SELECT TO_DATE(a.WRK_DT, 'YYYYMMDD')                                      AS prov_dt      -- 데이터 제공일
     , TO_DATE(a.PCAP_DATE, 'YYYYMMDD')                                   AS wrk_dt       -- 기준일(분기말). DATE 형이면 a.PCAP_DATE
     , a.NPS_CD                                                           AS fund_cd
     , a.COMMITMENT_AMT / <<원화 나누기>>                                   AS commit_krw
     , -1 * a.FUNDED_AMT / <<원화 나누기>>                                  AS funded_krw   -- 원천은 음수 부호
     , -1 * a.FUNDED_AMT / <<로컬 나누기>>                                  AS funded_local
     , a.DISTRB_AMT / <<원화 나누기>>                                       AS distrb_krw
     , a.DISTRB_AMT / <<로컬 나누기>>                                       AS distrb_local
     , a.PCAP_AMT / <<원화 나누기>>                                         AS nav_krw
  FROM FEIAI0432NTA a
 WHERE a.WRK_DT = (SELECT MAX(b.WRK_DT) FROM FEIAI0432NTA b)

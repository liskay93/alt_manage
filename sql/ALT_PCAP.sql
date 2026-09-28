/* 집행·분배·NAV 분기 스냅샷(PCAP). ALT_Manage 탭이 사용
   원천: FEIAI0432NTA
     WRK_DT(데이터 제공일, 주 단위, YYYYMMDD), PCAP_DATE(기준일, 분기말, YYYYMMDD), NPS_CD(펀드코드)
     COMMITMENT_AMT, FUNDED_AMT(음수 부호), DISTRB_AMT, PCAP_AMT(NAV). 모두 PCAP_DATE 기준 누적, 단위 1
     CURR_TYP  CD 투자 통화, CP 보고 통화(CURR_ID 가 USD 또는 KRW)
     RPRT_NM   AS Reported by Fund / AS Reported by GCM
     STATE_DATE 근거 명세서 일자 (같은 기준일에 여러 개일 수 있음)
   최신 제공일(WRK_DT 최대) 한 벌을 그대로 뽑는다. 행 고르기는 파이썬에서:
     펀드·기준일·통화유형·통화마다 GCM 보고 우선, 없으면 STATE_DATE 가 가장 늦은 행
   금액은 원본 그대로 (단위 1, FUNDED_AMT 음수 부호 그대로). 억원·백만 변환과 부호 처리는 processor 가 한다
   날짜는 TO_DATE 없이 원본 그대로. 날짜 변환은 파이썬에서
   돌려주는 열(대문자): PROV_DT, WRK_DT(=PCAP_DATE), FUND_CD, CURR_ID, CURR_TYP, RPRT_NM, STATE_DT,
                       COMMIT_AMT, FUNDED_AMT, DISTRB_AMT, NAV_AMT */
SELECT a.WRK_DT                                              AS prov_dt
     , a.PCAP_DATE                                            AS wrk_dt
     , a.NPS_CD                                               AS fund_cd
     , UPPER(a.CURR_ID)                                       AS curr_id
     , UPPER(a.CURR_TYP)                                      AS curr_typ
     , a.RPRT_NM                                              AS rprt_nm
     , a.STATE_DATE                                           AS state_dt
     , a.COMMITMENT_AMT                                       AS commit_amt
     , a.FUNDED_AMT                                           AS funded_amt
     , a.DISTRB_AMT                                           AS distrb_amt
     , a.PCAP_AMT                                             AS nav_amt
  FROM FEIAI0432NTA a
 WHERE a.WRK_DT = (SELECT MAX(b.WRK_DT) FROM FEIAI0432NTA b)

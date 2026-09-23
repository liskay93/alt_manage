# 데이터 준비 체크리스트

대시보드를 실제 데이터로 채우는 데 필요한 테이블 목록입니다. 상태는 확인될 때마다 갱신합니다.

| # | 테이블 | 필수 | 용도 | 상태 |
|---|---|---|---|---|
| 1 | 펀드 마스터 | 필수 | 펀드 식별, 자산군·통화 분류, 펀드 기여도 카드 | 🟡 거의 완료 — FEIAI0488NTA (펀드코드·빈티지·통화) + AVTV_PGM_CD 자산군·세부 분류 ✔ + FEIAI0432NTA.DEAL_NM 펀드명 ✔. AVTV_PGM_CD 가 FEIAI0488NTA 에 있는지만 확인 |
| 2 | 약정 내역 | 필수 | 약정 현황·달성률, 연도별·연중 누적 약정, 펀드별 약정 | 🟡 부분 — FEIAI0488NTA (AGRT_DT, AGRT_AMT). 금액 통화·단위, 날짜 형식 확인 중 |
| 3 | 집행(캐피털콜) 내역 | 필수 | 집행 현황, 순증, 분기별 집행, 누적 집행률 | 🟡 부분 — FEIAI0432NTA (FUNDED_AMT, PCAP_DATE 기준 누적 ✔, GCM 기준 ✔, CD=투자통화·CP=보고통화 ✔). 단위·PCAP_DATE 형식·STATE_DATE 중복·이력 시작 확인 중 |
| 4 | 분배(회수) 내역 | 필수 | 분배 현황, 순증, 분기별 분배 | 🟡 부분 — FEIAI0432NTA (DISTRB_AMT). 3번과 같은 확인 사항 |
| 5 | 연도별 목표 | 필수 | 네 지표의 목표·달성률·잔여, 목표 점선 | ⬜ 미완료 |
| 6 | 환율 | 선택 | PCAP 에 CD(투자 통화) 행이 빠진 펀드가 있을 때만 로컬 환산에 사용 | ✅ 완료 — FMCBI0006NTA (WRK_DT YYYYMMDD 일별, CURR_CD, MSCI_EXRT = 1 USD 당 통화). sql/ALT_FX.sql 완성 |

공통 규칙
- 금액 기준은 **원화**. 지표·달성률·비중은 모두 원화로 계산하고, 로컬 통화는 펀드 카드에 병기만 합니다.
- 원화 단위는 억원, 외화 로컬 금액은 백만 단위. SQL 에서 그 단위로 나눠서 돌려줍니다 (processors/ALT_Manage.py 의 UNIT, LOCAL_UNIT 은 표기만).
- 자산군 이름은 모든 테이블에서 동일하게: 사모벤처 / 부동산 / 인프라.
- 거래는 건별이 가장 좋고, 최소 월 단위 집계까지 허용합니다(월말 일자로 기입).
- 기준일(as-of)은 테이블이 아니라 process_ALT_Manage 의 asof 인자입니다. 생략하면 마지막 거래일.

## 1. 펀드 마스터

펀드 하나가 한 행. 지금 구현은 거래 내역에서 펀드명·자산군·통화·약정연도를 유추하지만, 마스터가 있으면 이름 표기 통일과 검증에 씁니다.

| 열 | 필수 | 설명 |
|---|---|---|
| 펀드 ID 또는 펀드명 | 필수 | 모든 거래 테이블과 연결하는 키. 표기가 같아야 같은 펀드로 묶임 |
| 자산군 | 필수 | 사모벤처 / 부동산 / 인프라 |
| 통화 | 필수 | KRW, USD, EUR 등. 펀드 단위로 하나 |
| 약정연도(빈티지) | 선택 | 없으면 첫 약정일에서 계산 |
| 운용사, 전략, 지역, 상태 | 선택 | 현재 대시보드에서는 쓰지 않음 (추후 필터 후보) |

## 2. 약정 내역

약정(및 증액·감액) 한 건이 한 행.

| 열 | 필수 | 설명 |
|---|---|---|
| 펀드 | 필수 | 펀드 마스터의 키 |
| 약정일 | 필수 | YYYY-MM-DD. 연도별 집계의 기준 |
| 약정금액(원화) | 필수 | 억원. 외화 펀드는 약정 시점 환산액 |
| 약정금액(로컬) | 선택 | 외화 펀드의 펀드 통화 금액 (백만). KRW 펀드는 생략 가능 |
| 자산군 | 선택 | 마스터에 있으면 생략 가능 |

## 3. 집행(캐피털콜) 내역

납입 한 건이 한 행.

| 열 | 필수 | 설명 |
|---|---|---|
| 펀드 | 필수 | |
| 납입일 | 필수 | 실제 송금(납입)일 기준 |
| 집행금액(원화) | 필수 | 억원. 외화는 송금일 환산액 |
| 집행금액(로컬) | 선택 | 펀드 통화 금액 (백만) |
| 자산군 | 선택 | |

## 4. 분배(회수) 내역

분배 한 건이 한 행.

| 열 | 필수 | 설명 |
|---|---|---|
| 펀드 | 필수 | |
| 분배일 | 필수 | 실제 수령일 기준 |
| 분배금액(원화) | 필수 | 억원. 외화는 수령일 환산액 |
| 분배금액(로컬) | 선택 | 펀드 통화 금액 (백만) |
| 원금/수익 구분 | 선택 | 현재 대시보드에서는 합산해서 사용 |
| 자산군 | 선택 | |

## 5. 연도별 목표

연도 × 자산군 한 조합이 한 행. 순증 목표를 비우면 집행 − 분배로 계산합니다.

| 열 | 필수 | 설명 |
|---|---|---|
| 연도 | 필수 | |
| 자산군 | 필수 | 사모벤처 / 부동산 / 인프라 |
| 약정 목표(원화) | 필수 | 억원 |
| 집행 목표(원화) | 필수 | 억원 |
| 분배 목표(원화) | 필수 | 억원 |
| 순증 목표(원화) | 선택 | 비우면 집행 목표 − 분배 목표 |

## 6. 환율 (선택)

2~4번 테이블에 원화 환산액이 이미 있으면 필요 없습니다. 로컬 금액만 있을 때 원화로 바꾸는 데 씁니다.

| 열 | 필수 | 설명 |
|---|---|---|
| 일자 또는 월 | 필수 | 거래일과 맞출 단위 |
| 통화 | 필수 | USD, EUR 등 |
| 환율(원/1단위) | 필수 | |

## 확인된 원천 테이블

| 테이블 | 컬럼 | 쓰이는 곳 | 남은 확인 |
|---|---|---|---|
| FEIAI0488NTA | NPS_FUND_CD 펀드코드, VNTG_YR 빈티지, CURR_CD 통화, AGRT_DT 약정일자, AGRT_AMT 약정금액 | 1 펀드 마스터(코드·빈티지·통화), 2 약정 내역 | AGRT_AMT 통화·단위, AGRT_DT 형식, 펀드당 행 수, AVTV_PGM_CD 가 이 테이블에 있는지 |
| (엑셀) AVTV_PGM_CD 매핑 | 액티브 프로그램 코드 22개 → 구분(사모/부동산/인프라)·세부 분류명 | 자산군(코드 앞 3자리 XPV/XRE/XIF), 펀드 표의 세부 분류 꼬리표 | 없음 |
| FMCBI0006NTA | WRK_DT 기준일(YYYYMMDD, 일별), CURR_CD 통화, MSCI_EXRT 환율(1 USD 당 해당 통화 단위) | 6 환율: KRW 행 ÷ 통화 행 = 원/1단위 (processor 계산) | 없음 (USD 행이 없어도 KRW 행으로 만든다) |
| FEIAI0432NTA | WRK_DT 데이터 제공일(주간, 'YYYY-MM-DD'), PCAP_DATE 기준일(분기), NPS_CD 펀드코드, COMMITMENT_AMT·FUNDED_AMT(음수)·DISTRB_AMT·PCAP_AMT (PCAP_DATE 기준 누적), CURR_ID, CURR_TYP(CD=투자 통화 EUR/USD/JPY…, CP=보고 통화 USD/KRW), RPRT_NM(Fund/GCM), DEAL_NM 펀드명, STATE_DATE(확인 중) | 3 집행, 4 분배 (분기 증분): 원화는 CP-KRW 행, 로컬은 CD 행. NAV 는 추후 활용. GCM 보고 기준만 | 금액 단위, PCAP_DATE 형식, STATE_DATE 중복 여부, 이력 시작 시점 |

## SQL 파일과의 대응 (TPA Dashboard 형식)

| 체크리스트 | SQL 파일 | 돌려주는 열 (대문자) | 상태 |
|---|---|---|---|
| 1 펀드 마스터 | sql/ALT_Fund.sql | FUND_CD, FUND_NM, ASSET_CLS, PGM_CD, CCY, VINTAGE_YR | 🟡 FEIAI0488NTA + AVTV_PGM_CD + FEIAI0432NTA.DEAL_NM 반영. AVTV_PGM_CD 위치 확인만 남음 |
| 2 약정 | sql/ALT_Commit.sql | WRK_DT, FUND_CD, CCY, AMT_KRW, AMT_LOCAL | 🟡 FEIAI0488NTA 반영, 금액 단위 대기 |
| 3·4 집행·분배 | sql/ALT_PCAP.sql (최신 제공일, GCM, 통화 유형별 long, 누적 → processor 가 증분) | PROV_DT, WRK_DT, FUND_CD, CURR_ID, CURR_TYP, COMMIT_AMT, FUNDED_AMT, DISTRB_AMT, NAV_AMT | 🟡 FEIAI0432NTA 반영, 단위·CD/CP 대기 |
| 5 목표 | sql/ALT_Target.sql | TARGET_YR, ASSET_CLS, COMMIT_KRW, DRAW_KRW, DIST_KRW, NET_KRW | ⬜ 테이블 확인 전 |
| 6 환율 | sql/ALT_FX.sql (long: 날짜·통화·USD 기준 환율) | WRK_DT, CURR_ID, USD_RATE | ✅ FMCBI0006NTA 완성 |

SQL 의 `<<...>>` 는 확인 전 자리표시자이며 추측한 이름이 아닙니다. 아래 확인 쿼리로 찾은 실제 이름으로 교체합니다.

### 테이블별로 확인이 필요한 것

| # | 테이블 | 확인할 것 |
|---|---|---|
| 1 | 펀드 마스터 | 테이블명, 펀드명 컬럼, 자산군 코드 컬럼과 코드값(사모벤처/부동산/인프라), 통화 코드 컬럼, 약정연도 컬럼 |
| 2 | 약정 내역 | 테이블명, 거래일자 컬럼(형식), 펀드 키, 원화 금액 컬럼(단위: 원/천원/백만원), 로컬 금액 컬럼 |
| 3 | 집행 내역 | 위와 같음 + 거래유형 코드값(약정·집행·분배가 한 테이블이면) |
| 4 | 분배 내역 | 위와 같음. 원금/수익 구분 컬럼이 있으면 합산 여부 |
| 5 | 연도별 목표 | 테이블명(또는 엑셀), 연도·자산군·지표별 목표 컬럼, 단위 |
| 6 | 환율 | (2~4에 원화 금액이 없을 때만) 테이블명, 일자·통화·환율 컬럼 |

### 확인 쿼리 (Oracle, 세미콜론 없음)

```sql
-- 이름에 특정 단어가 들어간 테이블 찾기
SELECT owner, table_name, comments
  FROM all_tab_comments
 WHERE comments LIKE '%대체%' OR table_name LIKE '%FUND%' OR table_name LIKE '%ALT%'
 ORDER BY owner, table_name
```

```sql
-- 테이블의 컬럼과 주석 보기 (테이블명을 넣어서)
SELECT c.column_id, c.column_name, c.data_type, c.data_length, m.comments
  FROM all_tab_columns c
  LEFT JOIN all_col_comments m ON m.owner = c.owner AND m.table_name = c.table_name AND m.column_name = c.column_name
 WHERE c.table_name = '<<테이블명>>'
 ORDER BY c.column_id
```

```sql
-- 코드 컬럼의 값 분포 보기 (자산군 코드, 거래유형 코드)
SELECT <<코드컬럼>>, COUNT(*) AS cnt, MIN(<<거래일자>>) AS first_dt, MAX(<<거래일자>>) AS last_dt
  FROM <<테이블명>>
 GROUP BY <<코드컬럼>>
 ORDER BY cnt DESC
```

```sql
-- 금액 단위 확인 (한 펀드의 최근 거래 몇 건)
SELECT *
  FROM <<테이블명>>
 WHERE ROWNUM <= 20
 ORDER BY <<거래일자>> DESC
```

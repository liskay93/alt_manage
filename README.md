# 대체투자 약정 현황 (ALT_Manage)

약정·집행·분배·순증 네 지표를 목표 · 현황 · 달성률 관점으로 보는 TPA Dashboard 탭입니다.
코딩 규칙은 `CLAUDE.md` 를 따릅니다 (sql → loader → processors → global_data → tabs → Main).

## 구조

```
alt_manage/
├── CLAUDE.md                 코딩 규칙 (TPA Dashboard 공통)
├── sql/                      원재료 쿼리 — 확인된 테이블은 실명, 나머지는 <<...>> 자리표시자
│   ├── ALT_Commit.sql        약정 내역 (FEIAI0488NTA)
│   ├── ALT_PCAP.sql          집행·분배·NAV 분기 스냅샷 (FEIAI0432NTA, 최신 제공일 한 벌)
│   ├── ALT_Target.sql        연도·자산군별 목표 (확인 전)
│   └── ALT_Fund.sql          펀드 마스터 (FEIAI0488NTA 기반, 펀드명·자산군 확인 전)
├── processors/ALT_Manage.py  process_ALT_Manage(raw_commit, raw_pcap, raw_target, raw_fund=None, asof=None, pcap_cumulative=True) → 사전
├── tabs/ALT_Manage.py        render(data) — 자산군 내부 탭 4개, 콜백 없음
├── global_data.py            DF_ALT_Manage = None
├── loader.py                 create_connection(), load_data(conn, "파일.sql")  (사내 loader 와 같은 인터페이스)
├── ui/theme.py               TAB_STYLE, SELECTED_TAB_STYLE, CARD_STYLE  (로컬 확인용)
├── run_local.py              Main 노트북을 흉내 낸 로컬 실행기
├── demo_data.py              샘플 CSV → Oracle 결과 모양의 데모 원재료
├── docs/
│   ├── DATA_CHECKLIST.md     필요한 데이터 6개 테이블, SQL 대응, 확인 쿼리, 진행 상태
│   └── MAIN_연결.md          dash_board.ipynb 에 붙이는 코드
└── draft/                    HTML 가안 (순수 HTML/CSS/JS, 데모 데이터) — 화면 확정용
```

## 화면

기준연도는 기준일이 속한 연도이고, 자산군(전체 / 사모벤처 / 부동산 / 인프라)은 내부 탭으로 미리 렌더합니다.

| 단 | 내용 |
|---|---|
| 1 | 지표 카드 4개: 현황, 목표·잔여, 달성률 미터(진행 중 연도는 연간 진도 눈금), 전년 동기 대비 |
| 2 | 연도별 목표 대비 실적 4개: 목표(골드) vs 실적(지표색) 막대, 달성률 라벨 |
| 3 | 연중 누적 추이 4개: 당해 누적, 전년 누적(회색), 연간 목표(골드 점선) |
| 4 | 월별 집행·분배·순증 + 지표별 요약 표 |
| 5 | 누적 실적을 이끈 펀드 4개: 지표별 상위 5개, 로컬 통화 · 원화 · 비중(원화 기준) |
| 6 | 자산군별 목표·현황·달성률 표 (전체 탭에만) |

순증 = 집행 − 분배 (투자잔액 증가분). 금액은 원화 억원, 펀드 통화는 KRW 펀드면 억원·외화 펀드면 백만.
약정은 약정일 기준(일별), 집행·분배·순증은 PCAP 분기 기준일까지 집계하며 지표 카드에 기준월을 따로 표시합니다.

## 로컬에서 확인

```bash
pip install pandas plotly dash      # 사내 환경에는 이미 있음
python run_local.py                 # http://127.0.0.1:8050  (ORACLE_DSN 없으면 데모 원재료)
ALT_ASOF=2026-09-22 python run_local.py   # 기준일 지정
```

노트북에서 직접 호출해 확인하는 방법 (오류 traceback 이 한 화면에 나옵니다):

```python
import importlib, demo_data
import processors.ALT_Manage, tabs.ALT_Manage
importlib.reload(processors.ALT_Manage); importlib.reload(tabs.ALT_Manage)
raw_commit, raw_pcap, raw_target, raw_fund = demo_data.load_demo()   # 사내에서는 loader.load_data(conn, "ALT_Commit.sql") 등
d = processors.ALT_Manage.process_ALT_Manage(raw_commit, raw_pcap, raw_target, raw_fund)
tabs.ALT_Manage.render(d)
```

## 진행 순서

1. HTML 가안 (`draft/`) — 확정
2. SQL — 원천 테이블·컬럼명 확인 후 자리표시자 교체 (`docs/DATA_CHECKLIST.md` 의 확인 쿼리 사용)
3. processors / tabs — 데모 데이터로 실행 확인 완료
4. Main 연결 — `docs/MAIN_연결.md`
5. 최종 전달 — 코드모음 텍스트 파일 한 개 (SQL 확정 후 생성)

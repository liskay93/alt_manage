# Main 노트북(dash_board.ipynb) 연결

CLAUDE.md 8절 형식. 아래 조각을 각 셀에 추가합니다.

```python
# [1] Import
from processors import ALT_Manage as ALT_Manage_proc
from tabs import ALT_Manage as ALT_Manage_tab

# [2] 로드 (try 블록 안)
raw_alt_commit = loader.load_data(conn, "ALT_Commit.sql")   # FEIAI0488NTA 약정
raw_alt_pcap   = loader.load_data(conn, "ALT_PCAP.sql")     # FEIAI0432NTA 집행·분배 (최신 제공일, 분기별 누적)
raw_alt_target = loader.load_data(conn, "ALT_Target.sql")
raw_alt_fund   = loader.load_data(conn, "ALT_Fund.sql")     # 펀드 마스터가 없으면 None
raw_alt_fx     = loader.load_data(conn, "ALT_FX.sql")       # FMCBI0006NTA 환율 (외화 약정의 원화 환산에 필수)
global_data.DF_ALT_Manage = ALT_Manage_proc.process_ALT_Manage(raw_alt_commit, raw_alt_pcap, raw_alt_target, raw_alt_fund, raw_fx=raw_alt_fx)
logging.info(f"ALT_Manage 로드: 약정 {len(raw_alt_commit)}행, PCAP {len(raw_alt_pcap)}행, 목표 {len(raw_alt_target)}행")

# [4] 레이아웃 -- dcc.Tabs children
dcc.Tab(label='대체투자 약정', value='tab-ALT_Manage',
        style=TAB_STYLE, selected_style=SELECTED_TAB_STYLE),

# [5] 콜백 -- tab_renderers 사전
'tab-ALT_Manage': lambda: ALT_Manage_tab.render(global_data.DF_ALT_Manage),
```

```python
# global_data.py
DF_ALT_Manage = None
```

기준일을 지정하려면 `process_ALT_Manage(..., asof="2026-09-30")`. 생략하면 약정·PCAP 의 마지막 날짜.
PCAP 금액이 누적이 아니라 기간 증분이면 `pcap_cumulative=False`.

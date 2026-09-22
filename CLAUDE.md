# TPA Dashboard — 코딩 규칙

이 저장소의 새 화면(탭)은 아래 규칙대로 작성한다.
기준 예시는 SAA_Compare(sql/SAA_Policy.sql, processors/SAA_Compare.py, tabs/SAA_Compare.py)다.
새 탭을 만들기 전에 이 세 파일을 먼저 읽고 같은 모양으로 맞춘다.

## 1. 환경

- NPS 사내 JupyterLab, 커널 Python [p310]
- Oracle DB, cx_Oracle
- Dash + plotly + pandas
- 사내망이라 외부 패키지 설치와 CDN 사용 불가. 이미 있는 라이브러리만 쓴다

## 2. 구조와 데이터 흐름

```
TPA Dashboard/
├── (Main) dash_board.ipynb   [1]import [2]로드 [3]스타일 [4]레이아웃 [5]콜백 [6]실행
├── global_data.py            DF_XXX = None 선반
├── loader.py                 create_connection(), load_data(conn, "파일.sql")
├── sql/                      쿼리 파일
├── processors/               원재료 가공 (process_XXX)
├── tabs/                     화면 부품 (render 진입점)
└── ui/theme.py               TAB_STYLE, SELECTED_TAB_STYLE, CARD_STYLE 등
```

흐름: sql → loader.load_data → processors.process_XXX → global_data.DF_XXX → tabs.render → Main의 tab_renderers → 탭 클릭 콜백

## 3. 이름 규칙

- 탭 하나 = processor 파일 하나 + tab 파일 하나 + global_data 선반 하나, 이름 통일
  - processors/XXX.py 안에 process_XXX
  - tabs/XXX.py 안에 render
  - global_data.DF_XXX (가공이 끝난 결과를 담는다. 원재료가 아님)
  - 탭 value는 'tab-XXX'
- SQL 파일 이름은 원재료 기준으로 짓는다. 탭 이름과 달라도 된다
  (예: SAA_Policy.sql, SAA_IM.sql, SAA_Target.sql → SAA_Compare 탭 하나가 사용)
- 이미 있는 SQL로 충분하면 새 SQL을 만들지 않고 Main에서 로드한 raw 변수를 재사용한다
- 함수 이름은 형님이 정한 것을 따른다 (make_card, make_combo, make_gap_table, common_target 등). 임의로 바꾸지 않는다

## 4. SQL 규칙 (Oracle)

- 파일 안에 세미콜론(;) 금지
- 파이썬 삼중따옴표 문자열 금지 (파일로만 관리)
- 테이블 별명에 AS 금지 (FROM FPSPS0105NTA a). 컬럼 별명의 AS는 괜찮다
- Oracle은 별명을 대문자로 돌려준다 → 파이썬에서 대문자로 받는다
- 날짜: TO_DATE(STD_DT, 'YYYYMMDD') AS wrk_dt
- 0 나누기 방어: nullif(x, 0)
- 기본은 long으로 넓게 뽑고 피벗은 파이썬에서 한다
  단, 자산군처럼 열 구성이 고정이면 SQL에서 wide로 뽑아도 된다 (SAA_Policy.sql 방식)
- 자산군 코드 매핑은 DECODE(PE_ANLS_UNT_CD, '000007', ...) 방식
- 테이블명, 컬럼명, 코드값을 추측하지 않는다. 모르면 확인 쿼리를 먼저 제시하고 물어본다

## 5. processors 규칙

- 파일 첫머리에 주석 블록: 이 파일이 무엇인지, 입력, 출력(사전 키 목록), 단위
- 첫머리 표준화는 _prep 함수로:
  ```python
  def _prep(raw):
      df = raw.copy()
      df.columns = df.columns.str.upper()
      df["WRK_DT"] = pd.to_datetime(df["WRK_DT"], format="%Y%m%d")
      return df.set_index("WRK_DT")[ASSETS].sort_index()
  ```
- 다른 모듈의 밑줄 함수(_prep 등)를 import하지 않는다. 필요하면 자기 파일에 둔다
- 방어 코드는 자료형에 맞게
  - 입력 DataFrame: if df is None or df.empty: return {}
  - 여러 입력: if any(x is None or x.empty for x in [...]): return {}
- 실패 반환값도 정상 산출물과 같은 자료형 (사전이면 {})
- 0 나누기 방어: .replace(0, pd.NA)
- 두 시계열 비교는 index.intersection으로 겹치는 날짜만
- 원본 시계열은 자르지 않는다. 표시 기간 제한은 tabs에서 x축 range로만 한다
  (processors에서 자르면 이후 .loc[]에서 KeyError가 난다)
- 결과는 사전으로 반환, 기준일은 "asof" 키

## 6. tabs 규칙

- 파일 첫머리에 주석 블록: 화면 구성(몇 단, 몇 개 카드, 표 몇 개)
- import 형식
  ```python
  from dash import html, dcc
  import plotly.graph_objs as go
  from plotly.subplots import make_subplots
  import pandas as pd
  ```
- 상단에 색상 상수와 CARD 딕셔너리
  ```python
  NAVY = "#2C3E50"; BLUE = "#2E5FA3"; RED = "#C0504D"; GOLD = "#B0876A"
  CARD = {"background": "#fff", "border": "1px solid #E3E7EC",
          "borderRadius": "10px", "padding": "14px 16px"}
  ```
- 자산군 목록은 사전 리스트로: {"k": 컬럼키, "n": 표시이름, "c": 색}
  - 국내주식 #2C3E50 / 해외주식 #2E5FA3 / 국내채권 #4C9F70 / 해외채권 #8FA9D8
  - 대체투자 #E0A458 / 해외주식(+0.6 대체) #1F4E79 / 국내채권(+0.4 대체) #2F7D53
- 기타 색: 초록 #4C9F70, 주황 #E0A458, 목표SAA는 골드 #B0876A 전용
- 부품 함수로 쪼갠다: make_card, make_combo(차트), make_xxx_table(표), legend_bar
- 표 함수는 재사용 가능하게 범용 인자로 (raw1, raw2, gap, label1, label2, table_title 식)
- plotly 차트 공통
  ```python
  fig.update_layout(template="plotly_white", height=height,
                    margin=dict(l=48, r=15, t=10, b=25),
                    hovermode="x unified", showlegend=False)
  return dcc.Graph(figure=fig, config={"displayModeBar": False})
  ```
- 범례는 plotly 범례를 끄고 legend_bar로 직접 만든다 (선 아이콘 Span + 글자 Span)
- 차트 높이는 fig.update_layout(height=...) 한 곳에서만 준다. dcc.Graph style에 높이를 같이 주지 않는다
- 좌우로 나란히 놓는 카드는 높이를 상수 하나로 묶고, 제목과 범례는 height 고정 + whiteSpace nowrap
- 배치는 CSS grid: {"display": "grid", "gridTemplateColumns": "repeat(4,1fr)", "gap": "14px"}
- render 방어
  ```python
  def render(data):
      if not data:
          return html.Div("데이터를 로드할 수 없습니다.")
  ```
- 탭 안쪽 전환(정렬, 보기 전환)은 dcc.Tabs children에 화면을 미리 넣어 콜백 없이 처리한다

## 7. 자주 틀리는 것

- CSS 딕셔너리 키는 camelCase (fontSize, marginBottom). fontsize는 동작 안 함
- .min(), .max() 괄호 빠뜨리지 않기
  ("unsupported operand type(s) for -: 'method' and 'float'" 오류의 단골 원인)
- Oracle 컬럼은 대문자로 받는다
- SQL 파일에 세미콜론 넣지 않기

## 8. Main 노트북 연결 형식

```python
# [1] Import
from processors import XXX as XXX_proc
from tabs import XXX as XXX_tab

# [2] 로드 (try 블록 안)
raw_xxx = loader.load_data(conn, "원재료.sql")
global_data.DF_XXX = XXX_proc.process_XXX(raw_xxx)
logging.info(f"XXX 로드: {len(raw_xxx)}행")

# [4] 레이아웃 -- dcc.Tabs children
dcc.Tab(label='탭이름', value='tab-XXX',
        style=TAB_STYLE, selected_style=SELECTED_TAB_STYLE),

# [5] 콜백 -- tab_renderers 사전
'tab-XXX': lambda: XXX_tab.render(global_data.DF_XXX),

# global_data.py
DF_XXX = None
```

## 9. 작업 방식

- 새 화면 순서: HTML 가안(외부 라이브러리 없이 순수 HTML/CSS/JS) → 형님 확정 → SQL → processors → tabs → Main 연결
- 가안 단계에서는 데모 데이터로 그리고, 실제 데이터 구조는 확정 후 맞춘다
- 코드에는 한글 주석
- 수정 요청에는 전/후를 나란히 보여준다. 파일 전체가 필요하면 통째로 준다
- 최종 전달은 코드모음 텍스트 파일 한 개로:
  ```
  =====FILE: sql/XXX.sql=====
  (내용)

  =====FILE: processors/XXX.py=====
  (내용)

  =====FILE: tabs/XXX.py=====
  (내용)

  =====FILE: Main 노트북 연결 (dash_board.ipynb)=====
  (내용)
  ```
  마지막에 확인 사항(추측한 이름, 교체가 필요한 곳)을 적는다
- 전달 전에 가짜 데이터로 processor와 render를 실제 실행해서 확인한다
- 오류 디버깅은 브라우저 로그보다 노트북에서 직접 호출이 빠르다. 이 방법을 먼저 권한다
  ```python
  import importlib
  import processors.XXX, tabs.XXX
  importlib.reload(processors.XXX); importlib.reload(tabs.XXX)
  d = processors.XXX.process_XXX(raw_xxx)
  tabs.XXX.render(d)      # traceback 전체가 한 화면에 나옴
  ```
- 오류 캡처를 받으면 traceback 읽는 법과 함께 원인 줄을 지목한다
- 응답은 존댓말, 간결하게

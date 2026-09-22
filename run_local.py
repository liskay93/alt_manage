# 로컬 확인용 Main. 사내 dash_board.ipynb 의 [1]import [2]로드 [3]스타일 [4]레이아웃 [5]콜백 [6]실행 구조를 그대로 따른다.
# ORACLE_DSN 환경변수가 있으면 sql/ 을 실제로 실행하고, 없으면 draft/data 의 샘플로 데모 원재료를 만든다.
# 실행: python run_local.py  →  http://127.0.0.1:8050
import logging
import os

from dash import Dash, html, dcc, Input, Output

# [1] Import
import global_data
import loader
from processors import ALT_Manage as ALT_Manage_proc
from tabs import ALT_Manage as ALT_Manage_tab
from ui.theme import TAB_STYLE, SELECTED_TAB_STYLE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# [2] 로드
try:
    if os.environ.get("ORACLE_DSN"):
        conn = loader.create_connection()
        raw_alt_commit = loader.load_data(conn, "ALT_Commit.sql")     # FEIAI0488NTA 약정
        raw_alt_pcap = loader.load_data(conn, "ALT_PCAP.sql")         # FEIAI0432NTA 집행·분배(분기)
        raw_alt_target = loader.load_data(conn, "ALT_Target.sql")
        raw_alt_fund = loader.load_data(conn, "ALT_Fund.sql")
    else:
        import demo_data
        raw_alt_commit, raw_alt_pcap, raw_alt_target, raw_alt_fund = demo_data.load_demo()
        logging.info("ORACLE_DSN 없음 → 데모 원재료 사용")
    global_data.DF_ALT_Manage = ALT_Manage_proc.process_ALT_Manage(
        raw_alt_commit, raw_alt_pcap, raw_alt_target, raw_alt_fund, asof=os.environ.get("ALT_ASOF"))
    logging.info("ALT_Manage 로드: 약정 %d행, PCAP %d행, 목표 %d행", len(raw_alt_commit), len(raw_alt_pcap), len(raw_alt_target))
except Exception:
    logging.exception("ALT_Manage 로드 실패")

# [3] 스타일 — ui/theme.py

# [4] 레이아웃
app = Dash(__name__)
app.layout = html.Div([
    dcc.Tabs(id="tabs", value="tab-ALT_Manage", children=[
        dcc.Tab(label="대체투자 약정", value="tab-ALT_Manage", style=TAB_STYLE, selected_style=SELECTED_TAB_STYLE),
    ]),
    html.Div(id="tab-content", style={"padding": "12px 16px"}),
], style={"fontFamily": "'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif", "background": "#F3F5F8", "minHeight": "100vh"})

# [5] 콜백
tab_renderers = {
    "tab-ALT_Manage": lambda: ALT_Manage_tab.render(global_data.DF_ALT_Manage),
}


@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(value):
    fn = tab_renderers.get(value)
    return fn() if fn else html.Div("탭을 찾을 수 없습니다.")


# [6] 실행
if __name__ == "__main__":
    run = getattr(app, "run", None) or app.run_server
    run(host="127.0.0.1", port=int(os.environ.get("PORT", "8050")), debug=False)

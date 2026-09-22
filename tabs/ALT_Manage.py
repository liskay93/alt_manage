# ------------------------------------------------------------
# tabs/ALT_Manage.py
# 화면 구성: 대체투자 약정·집행·분배·순증 현황 (기준연도 = 기준일이 속한 연도)
#   약정은 약정일 기준(일별), 집행·분배·순증은 PCAP 분기 기준일까지 — 지표 카드에 기준월을 따로 적는다
#   자산군 내부 탭 4개 (전체 / 사모벤처 / 부동산 / 인프라) — dcc.Tabs children 에 미리 렌더, 콜백 없음
#   탭마다
#     1단  지표 카드 4개        현황 · 목표/잔여 · 달성률 미터(연간 진도 눈금) · 전년 동기 대비
#     2단  연도별 목표 대비 실적 4개   지표별 막대 (목표 골드, 실적 지표색), 달성률 라벨
#     3단  연중 누적 추이 4개    당해 누적(지표색) · 전년 누적(회색) · 연간 목표(골드 점선)
#     4단  월별(PCAP 이면 분기별) 집행·분배·순증 1개 + 지표별 요약 표 1개
#     5단  누적 실적을 이끈 펀드 4개   지표별 상위 5개 (로컬 통화 · 원화 · 비중)
#     6단  자산군별 목표·현황·달성률 표 1개   전체 탭에만
# 입력: processors.ALT_Manage.process_ALT_Manage 의 결과 사전 (global_data.DF_ALT_Manage)
# ------------------------------------------------------------
from dash import html, dcc
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd

from ui.theme import TAB_STYLE, SELECTED_TAB_STYLE

NAVY = "#2C3E50"; BLUE = "#2E5FA3"; RED = "#C0504D"; GOLD = "#B0876A"
GREEN = "#4C9F70"; ORANGE = "#E0A458"; GREY = "#B7BEC8"; INK = "#161B23"; MUTED = "#7A8494"; LINE = "#E3E7EC"
CARD = {"background": "#fff", "border": "1px solid #E3E7EC",
        "borderRadius": "10px", "padding": "14px 16px"}
GRID4 = {"display": "grid", "gridTemplateColumns": "repeat(4,1fr)", "gap": "14px"}
GRID2 = {"display": "grid", "gridTemplateColumns": "repeat(2,1fr)", "gap": "14px"}

# 지표 목록: k 데이터 키, n 표시 이름, c 색. 목표는 골드 전용
METRICS = [
    {"k": "약정", "n": "약정", "c": BLUE, "d": "신규 약정"},
    {"k": "집행", "n": "집행", "c": ORANGE, "d": "캐피털콜 납입"},
    {"k": "분배", "n": "분배", "c": GREEN, "d": "회수"},
    {"k": "순증", "n": "순증", "c": NAVY, "d": "집행 − 분배"},
]
ALL = "전체"
MONTH_LABELS = ["%d월" % m for m in range(1, 13)]
H_YEARLY = 230     # 2단 카드 높이 (가로로 나란히 → 상수 하나로 묶음)
H_CUM = 250        # 3단
H_FLOW = 300       # 4단
TOP_N = 5


# ---------- 서식 ----------
def fmt(v):
    """억원 정수 표기. 음수는 −, 결측은 –"""
    if v is None or pd.isna(v):
        return "–"
    v = round(float(v))
    return ("−" if v < 0 else "") + "{:,.0f}".format(abs(v))


def pct(v, digits=0):
    if v is None or pd.isna(v):
        return "–"
    p = float(v) * 100
    return ("−" if p < 0 else "") + ("{:.%df}%%" % digits).format(abs(p))


def fmt_local(v, ccy, unit, local_unit):
    """펀드 통화 금액: KRW 는 억원 정수, 외화는 백만 단위 소수 1자리"""
    if v is None or pd.isna(v):
        return "–"
    if ccy == "KRW":
        return "KRW " + fmt(v) + unit.replace("원", "")
    v = float(v)
    num = ("−" if v < 0 else "") + ("{:,.1f}".format(abs(v)) if abs(v) < 100 else "{:,.0f}".format(abs(v)))
    return "%s %s%s" % (ccy, num, local_unit)


def period_text(months):
    return "1~%d월" % months if months < 12 else "1~12월"


# ---------- 공통 부품 ----------
def make_card(title, body, sub=None, right=None, height=None):
    """제목(왼쪽) + 보조 문구(오른쪽) + 본문 카드. 나란히 놓는 카드는 height 로 묶는다"""
    style = dict(CARD)
    if height:
        style["height"] = "%dpx" % height
    head = html.Div([
        html.Div([html.Span(title, style={"fontSize": "14px", "fontWeight": "600", "color": INK}),
                  html.Span(sub or "", style={"fontSize": "12px", "color": MUTED, "marginLeft": "8px"})],
                 style={"whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}),
        html.Div(right or "", style={"fontSize": "12px", "color": MUTED, "whiteSpace": "nowrap"}),
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline",
              "height": "22px", "marginBottom": "6px"})
    return html.Div([head, body], style=style)


def legend_bar(items):
    """plotly 범례 대신 쓰는 범례 줄. items: [{"n": 이름, "c": 색, "t": line|bar|dash|dot}]"""
    spans = []
    for it in items:
        t = it.get("t", "line")
        if t == "bar":
            icon = {"display": "inline-block", "width": "12px", "height": "12px", "borderRadius": "3px", "background": it["c"]}
        elif t == "dot":
            icon = {"display": "inline-block", "width": "9px", "height": "9px", "borderRadius": "50%", "background": it["c"]}
        elif t == "dash":
            icon = {"display": "inline-block", "width": "14px", "height": "0", "borderTop": "2px dashed " + it["c"]}
        else:
            icon = {"display": "inline-block", "width": "14px", "height": "3px", "borderRadius": "2px", "background": it["c"]}
        icon.update({"marginRight": "6px", "verticalAlign": "middle"})
        spans.append(html.Span([html.Span(style=icon), html.Span(it["n"])],
                               style={"marginRight": "14px", "fontSize": "12px", "color": "#4B5563", "whiteSpace": "nowrap"}))
    return html.Div(spans, style={"height": "20px", "marginBottom": "4px", "whiteSpace": "nowrap", "overflow": "hidden"})


def make_meter(ratio, color, pace=None, width="100%"):
    """달성률 미터. pace(0~1) 가 있으면 연간 진도 눈금을 그린다"""
    fill = 0 if ratio is None or pd.isna(ratio) else max(0.0, min(1.0, float(ratio))) * 100
    children = [html.Div(style={"width": "%.1f%%" % fill, "height": "100%", "background": color, "borderRadius": "3px"})]
    if pace is not None and 0 < pace < 1:
        children.append(html.Div(style={"position": "absolute", "top": "0", "bottom": "0", "left": "%.1f%%" % (pace * 100),
                                        "width": "2px", "background": "#4B5563"}))
    return html.Div(children, style={"position": "relative", "height": "6px", "borderRadius": "3px",
                                     "background": "#EEF1F5", "overflow": "hidden", "width": width,
                                     "display": "inline-block", "verticalAlign": "middle"})


def delta_span(actual, prev, colored=True):
    """전년 동기 대비 증감률. 자료 없으면 문구"""
    if prev is None or pd.isna(prev):
        return html.Span("전년 동기 자료 없음", style={"color": MUTED})
    prev = float(prev)
    if prev == 0:
        return html.Span("전년 동기 0", style={"color": MUTED})
    r = float(actual) / abs(prev) - (1 if prev > 0 else -1)
    if abs(r) < 0.0005:
        return html.Span("■ 0.0%", style={"color": "#4B5563", "fontWeight": "600"})
    up = r > 0
    color = (GREEN if up else RED) if colored else "#4B5563"
    return html.Span(("▲ " if up else "▼ ") + "{:.1f}%".format(abs(r) * 100), style={"color": color, "fontWeight": "600"})


def num_td(text, bold=False, color=None, extra=None):
    """숫자 셀: 오른쪽 정렬"""
    st = {"textAlign": "right", "padding": "6px 8px", "borderBottom": "1px solid " + LINE, "whiteSpace": "nowrap",
          "fontVariantNumeric": "tabular-nums"}
    if bold:
        st["fontWeight"] = "600"
    if color:
        st["color"] = color
    if extra:
        st.update(extra)
    return html.Td(text, style=st)


def text_td(children, bold=False, extra=None):
    st = {"textAlign": "left", "padding": "6px 8px", "borderBottom": "1px solid " + LINE, "whiteSpace": "nowrap"}
    if bold:
        st["fontWeight"] = "600"
    if extra:
        st.update(extra)
    return html.Td(children, style=st)


def th(text, align="right", extra=None):
    st = {"textAlign": align, "padding": "6px 8px", "fontSize": "12px", "color": MUTED, "fontWeight": "600",
          "borderBottom": "1px solid #C9CFD8", "whiteSpace": "nowrap"}
    if extra:
        st.update(extra)
    return html.Th(text, style=st)


TABLE_STYLE = {"width": "100%", "borderCollapse": "collapse", "fontSize": "13px"}


def key_dot(color, size=9):
    return html.Span(style={"display": "inline-block", "width": "%dpx" % size, "height": "%dpx" % size,
                            "borderRadius": "2px", "background": color, "marginRight": "6px", "verticalAlign": "1px"})


# ---------- 1단: 지표 카드 ----------
def make_kpi_card(m, row, unit, months, in_progress, note=None):
    """m: METRICS 항목, row: kpi 한 행(dict), months: 이 지표의 집계 마지막 월, note: 기준월이 다를 때 덧붙일 문구"""
    target, actual, ratio, remain, prev = row["TARGET"], row["ACTUAL"], row["RATIO"], row["REMAIN"], row["PREV"]
    pace = months / 12.0 if in_progress else None
    unit_short = unit.replace("원", "")
    head = html.Div([key_dot(m["c"], 10), html.Span(m["n"] + " 현황", style={"fontSize": "12.5px", "fontWeight": "600", "color": "#4B5563"}),
                     html.Span(m["d"], style={"fontSize": "11.5px", "color": MUTED, "float": "right"})])
    value = html.Div([html.Span(fmt(actual), style={"fontSize": "26px", "fontWeight": "600", "color": RED if actual < 0 else INK}),
                      html.Span(unit_short, style={"fontSize": "14px", "color": "#4B5563", "marginLeft": "2px"})],
                     style={"lineHeight": "1.1", "margin": "6px 0 4px"})
    tline = html.Div(("목표 %s%s · 잔여 %s%s" % (fmt(target), unit_short, fmt(remain), unit_short)) if target else "목표 없음",
                     style={"fontSize": "12px", "color": MUTED, "marginBottom": "6px"})
    meter = html.Div([make_meter(ratio, m["c"], pace, width="calc(100% - 46px)"),
                      html.Span(pct(ratio), style={"display": "inline-block", "width": "40px", "textAlign": "right",
                                                   "fontWeight": "600", "fontSize": "12.5px", "verticalAlign": "middle"})],
                     style={"marginBottom": "6px"})
    foot = html.Div([delta_span(actual, prev), html.Span(" 전년 동기 대비", style={"color": "#4B5563"}),
                     html.Span(" · " + note if note else "", style={"color": MUTED})],
                    style={"fontSize": "12px", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"})
    return html.Div([head, value, tline, meter, foot], style=CARD)


# ---------- 2단: 연도별 목표 대비 실적 ----------
def make_yearly_chart(kpi_m, base_year, height):
    """kpi_m: 한 자산군·한 지표의 kpi 행들(연도별). 목표는 골드(연함), 실적은 지표색"""
    color = kpi_m["color"]
    df = kpi_m["df"].sort_values("YEAR")
    labels = ["%d<br>%s" % (y, period_text(mo)) if mo < 12 else str(y) for y, mo in zip(df["YEAR"], df["MONTHS"])]
    ratio_text = [pct(r) if not pd.isna(r) else "" for r in df["RATIO"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=df["TARGET"], name="목표", marker_color=GOLD, opacity=0.35, width=0.6,
                         hovertemplate="목표 %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=df["ACTUAL"], name="실적", marker_color=color, width=0.34,
                         text=ratio_text, textposition="outside", textfont=dict(size=11, color=INK),
                         constraintext="none", cliponaxis=False,
                         hovertemplate="실적 %{y:,.0f}<extra></extra>"))
    ymax = max(float(df["TARGET"].max()), float(df["ACTUAL"].max()), 1.0)
    ymin = min(float(df["TARGET"].min()), float(df["ACTUAL"].min()), 0.0)
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=48, r=15, t=10, b=25),
                      hovermode="x unified", showlegend=False, barmode="overlay", bargap=0.3,
                      yaxis=dict(range=[ymin * 1.15 if ymin < 0 else 0, ymax * 1.18], tickformat=",.0f"))
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


# ---------- 3단: 연중 누적 추이 ----------
def make_cum_chart(cur, prev, target, color, height):
    """cur/prev: 월별 누적 Series(index 1..12, 없으면 None). target: 연간 목표. 자료 없는 달(NaN)은 선을 그리지 않는다"""
    cur = cur.dropna() if cur is not None else None
    prev = prev.dropna() if prev is not None else None
    fig = go.Figure()
    if prev is not None and len(prev):
        fig.add_trace(go.Scatter(x=[MONTH_LABELS[i - 1] for i in prev.index], y=prev.values, mode="lines", name="전년 누적",
                                 line=dict(color=GREY, width=2), hovertemplate="전년 %{y:,.0f}<extra></extra>"))
    if cur is not None and len(cur):
        x = [MONTH_LABELS[i - 1] for i in cur.index]
        fig.add_trace(go.Scatter(x=x, y=cur.values, mode="lines", name="당해 누적",
                                 line=dict(color=color, width=2.5), hovertemplate="당해 %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[x[-1]], y=[cur.values[-1]], mode="markers+text", text=[fmt(cur.values[-1])],
                                 textposition="middle right", textfont=dict(size=11, color=INK),
                                 marker=dict(color=color, size=9, line=dict(color="#fff", width=2)), hoverinfo="skip"))
    if target:
        fig.add_shape(type="line", x0=0, x1=1, xref="paper", y0=target, y1=target, line=dict(color=GOLD, width=1.5, dash="dash"))
        fig.add_annotation(x=1, xref="paper", y=target, text="목표 " + fmt(target), showarrow=False, xanchor="right",
                           yanchor="bottom", font=dict(size=11, color=MUTED))
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=48, r=15, t=10, b=25),
                      hovermode="x unified", showlegend=False,
                      xaxis=dict(categoryorder="array", categoryarray=MONTH_LABELS, range=[-0.5, 11.9]),
                      yaxis=dict(tickformat=",.0f", rangemode="tozero"))
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


# ---------- 4단: 월별 집행·분배·순증 ----------
def make_flow_chart(mon, height, quarterly=False):
    """mon: 기준연도·자산군의 월별 DataFrame(MONTH, 집행, 분배, 순증). 집행 위, 분배 아래, 순증 점.
    quarterly 면 분기말(3·6·9·12월)만 그린다"""
    mon = mon.dropna(subset=["집행", "분배"])
    if quarterly:
        mon = mon[mon["MONTH"] % 3 == 0]
    x = [MONTH_LABELS[i - 1] for i in mon["MONTH"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=mon["집행"], name="집행", marker_color=ORANGE, hovertemplate="집행 +%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=x, y=-mon["분배"], name="분배", marker_color=GREEN, customdata=mon["분배"],
                         hovertemplate="분배 −%{customdata:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=x, y=mon["순증"], name="순증", mode="markers",
                             marker=dict(color=NAVY, size=9, line=dict(color="#fff", width=2)),
                             hovertemplate="순증 %{y:,.0f}<extra></extra>"))
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=48, r=15, t=10, b=25),
                      hovermode="x unified", showlegend=False, barmode="relative", bargap=0.45,
                      xaxis=dict(categoryorder="array", categoryarray=MONTH_LABELS, range=[-0.5, 11.5]),
                      yaxis=dict(tickformat=",.0f", zeroline=True, zerolinecolor="#C9CFD8"))
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


# ---------- 표 ----------
def make_summary_table(kpi_rows, unit):
    """지표별 요약 표: 목표 · 현황 · 달성률 · 잔여 · 전년 동기 · 전년비"""
    head = html.Thead(html.Tr([th("지표", "left"), th("목표"), th("현황"), th("달성률", extra={"minWidth": "110px"}),
                               th("잔여"), th("전년 동기"), th("전년비")]))
    body = []
    for m in METRICS:
        r = kpi_rows[m["k"]]
        body.append(html.Tr([
            text_td([key_dot(m["c"]), m["n"]], bold=True),
            num_td(fmt(r["TARGET"])), num_td(fmt(r["ACTUAL"]), bold=True),
            num_td([make_meter(r["RATIO"], m["c"], width="48px"), html.Span(" " + pct(r["RATIO"]), style={"marginLeft": "6px"})]),
            num_td(fmt(r["REMAIN"])), num_td(fmt(r["PREV"])),
            num_td(delta_span(r["ACTUAL"], r["PREV"])),
        ]))
    return html.Table([head, html.Tbody(body)], style=TABLE_STYLE)


def make_fund_table(funds, metric, total, unit, local_unit, show_cls):
    """지표별 상위 펀드 표: 펀드 · 막대 · 로컬 통화 · 원화 · 비중(원화 기준). 순증은 양/음을 좌우로"""
    k = metric["k"]
    df = funds[funds[k] != 0].copy()
    if df.empty:
        return html.Div("해당 기간 %s 실적이 있는 펀드가 없습니다" % metric["n"], style={"fontSize": "12.5px", "color": MUTED, "padding": "10px 6px"})
    df["ABS"] = df[k].abs()
    df = df.sort_values("ABS", ascending=False)
    top, rest = df.head(TOP_N), df.iloc[TOP_N:]
    rest_sum = float(rest[k].sum())
    max_abs = max(float(top["ABS"].max()), abs(rest_sum), 1.0)
    diverging = k == "순증" and (bool((df[k] < 0).any()) or rest_sum < 0)
    # 비중은 원화 합계 대비. 순증에 음수가 섞이면 비중의 뜻이 없어 표시하지 않는다
    share = (lambda v: pct(v / total)) if (total and total > 0 and not diverging) else (lambda v: "–")

    def bar_cell(v):
        w = abs(v) / max_abs * (50 if diverging else 100)
        inner = {"position": "absolute", "top": "0", "bottom": "0", "width": "%.1f%%" % w, "borderRadius": "4px",
                 "background": metric["c"] if v is not None else GREY}
        if diverging:
            inner["left" if v >= 0 else "right"] = "50%"
        else:
            inner["left"] = "0"
        kids = [html.Div(style=inner)]
        if diverging:
            kids.append(html.Div(style={"position": "absolute", "top": "0", "bottom": "0", "left": "50%", "width": "1px", "background": "#C9CFD8"}))
        return html.Td(html.Div(kids, style={"position": "relative", "height": "8px", "background": "#F3F5F8", "borderRadius": "4px"}),
                       style={"padding": "6px 8px", "borderBottom": "1px solid " + LINE, "minWidth": "70px"})

    rows = []
    for _, r in top.iterrows():
        name = [html.Span(r["FUND"])]
        if show_cls:
            name.append(html.Span(" " + r["CLS"], style={"color": MUTED, "fontSize": "11px"}))
        rows.append(html.Tr([
            text_td(name, extra={"maxWidth": "170px", "overflow": "hidden", "textOverflow": "ellipsis"}),
            bar_cell(float(r[k])),
            num_td(fmt_local(r[k + "_L"], r["CCY"], unit, local_unit), color="#4B5563"),
            num_td(fmt(r[k]), bold=True, color=RED if r[k] < 0 else None),
            num_td(share(float(r[k])), color=MUTED),
        ]))
    if len(rest):
        rows.append(html.Tr([
            text_td("기타 %d개 펀드" % len(rest), extra={"color": MUTED}),
            bar_cell(rest_sum),
            num_td("", color=MUTED), num_td(fmt(rest_sum), color=RED if rest_sum < 0 else "#4B5563"), num_td(share(rest_sum), color=MUTED),
        ]))
    head = html.Thead(html.Tr([th("펀드", "left"), th(""), th("로컬 통화"), th("원화"), th("비중(원화)")]))
    return html.Table([head, html.Tbody(rows)], style=TABLE_STYLE)


def make_class_table(kpi_year, classes, unit):
    """자산군 × 지표 × (목표 / 현황 / 달성률). 마지막 행은 전체(합계)"""
    group_row = [th("", "left")]
    col_row = [th("자산군", "left")]
    for i, m in enumerate(METRICS):
        sep = {"borderLeft": "1px solid " + LINE} if i >= 0 else {}
        group_row.append(html.Th([key_dot(m["c"]), m["n"]], colSpan=3,
                                 style={"textAlign": "center", "padding": "6px 8px", "fontSize": "12px", "color": "#4B5563",
                                        "fontWeight": "600", **sep}))
        col_row += [th("목표", extra=sep), th("현황"), th("달성률")]
    body = []
    for c in classes + [ALL]:
        cells = [text_td("합계" if c == ALL else c, bold=(c == ALL))]
        for m in METRICS:
            r = kpi_year[(kpi_year["CLS"] == c) & (kpi_year["METRIC"] == m["k"])]
            r = r.iloc[0] if len(r) else None
            sep = {"borderLeft": "1px solid " + LINE}
            if r is None:
                cells += [num_td("–", extra=sep), num_td("–"), num_td("–")]
                continue
            cells += [num_td(fmt(r["TARGET"]), extra=sep), num_td(fmt(r["ACTUAL"]), bold=(c == ALL)),
                      num_td([make_meter(r["RATIO"], m["c"], width="40px"), html.Span(" " + pct(r["RATIO"]), style={"marginLeft": "6px"})])]
        style = {"fontWeight": "600", "borderTop": "1px solid #C9CFD8"} if c == ALL else {}
        body.append(html.Tr(cells, style=style))
    return html.Table([html.Thead([html.Tr(group_row), html.Tr(col_row)]), html.Tbody(body)], style=TABLE_STYLE)


# ---------- 탭 한 장 ----------
def make_page(data, cls):
    """한 자산군(또는 전체)의 화면 전체"""
    year = data["base_year"]
    asof = data["asof"]
    unit, local_unit = data["unit"], data["local_unit"]
    kpi = data["kpi"]
    kpi_year = kpi[kpi["YEAR"] == year]
    kpi_rows = {r["METRIC"]: r for _, r in kpi_year[kpi_year["CLS"] == cls].iterrows()}
    months = int(kpi_rows["약정"]["MONTHS"]) if "약정" in kpi_rows else 12          # 약정 기준월
    flow_months = int(kpi_rows["집행"]["MONTHS"]) if "집행" in kpi_rows else months  # 집행·분배·순증 기준월 (PCAP)
    asof_flow = data.get("asof_flow", asof)
    quarterly = data.get("flow_freq", "M") == "Q"
    in_progress = year == asof.year and months < 12
    period = "%d년 %s 누적" % (year, period_text(months))
    if flow_months != months:
        period += " (집행·분배·순증은 %s, PCAP %s 기준)" % (period_text(flow_months), asof_flow.strftime("%m/%d"))
    pace_text = " · 연간 진도 %d%% (%d/12개월)" % (round(months / 12 * 100), months) if in_progress else ""

    # 1단 지표 카드 — 지표마다 자기 기준월로 진도 눈금을 그린다
    kpi_cards = html.Div([
        make_kpi_card(m, kpi_rows[m["k"]], unit, int(kpi_rows[m["k"]]["MONTHS"]), in_progress,
                      note=(period_text(int(kpi_rows[m["k"]]["MONTHS"])) + " 기준") if int(kpi_rows[m["k"]]["MONTHS"]) != months else None)
        for m in METRICS if m["k"] in kpi_rows], style=dict(GRID4, marginBottom="14px"))

    # 2단 연도별
    yearly_cards = []
    for m in METRICS:
        dfm = kpi[(kpi["CLS"] == cls) & (kpi["METRIC"] == m["k"])]
        cur = kpi_rows.get(m["k"])
        right = ("%d년 달성률 " % year) + pct(cur["RATIO"] if cur is not None else None)
        yearly_cards.append(make_card([key_dot(m["c"], 10), m["n"]], make_yearly_chart({"df": dfm, "color": m["c"]}, year, H_YEARLY),
                                      right=right, height=H_YEARLY + 50))
    yearly = make_card("연도별 목표 대비 실적", html.Div(yearly_cards, style=GRID4),
                       sub="연한 막대는 목표, 진한 막대는 실적(현황), 라벨은 달성률")

    # 3단 연중 누적
    cum = data["cum"]
    cum_cards = []
    legend = legend_bar([{"n": "%d년 누적 실적 (지표 색)" % year, "c": INK, "t": "line"},
                         {"n": "%d년 누적 실적" % (year - 1), "c": GREY, "t": "line"},
                         {"n": "연간 목표", "c": GOLD, "t": "dash"}])
    for m in METRICS:
        cur = cum[(cum["YEAR"] == year) & (cum["CLS"] == cls)].set_index("MONTH")[m["k"]]
        prev = cum[(cum["YEAR"] == year - 1) & (cum["CLS"] == cls)].set_index("MONTH")[m["k"]]
        target = float(kpi_rows[m["k"]]["TARGET"]) if m["k"] in kpi_rows else 0.0
        ratio = kpi_rows[m["k"]]["RATIO"] if m["k"] in kpi_rows else None
        cum_cards.append(make_card([key_dot(m["c"], 10), m["n"] + " 누적"], make_cum_chart(cur, prev if len(prev) else None, target, m["c"], H_CUM),
                                   right="목표 대비 " + pct(ratio), height=H_CUM + 50))
    cum_section = make_card("연중 누적 추이", html.Div([legend, html.Div(cum_cards, style=GRID2)]),
                            sub="1월부터 누적한 실적과 연간 목표, 전년 누적")

    # 4단 월별 + 요약 표
    mon = data["monthly"]
    mon = mon[(mon["YEAR"] == year) & (mon["CLS"] == cls)].sort_values("MONTH")
    flow_legend = legend_bar([{"n": "집행 (잔액 증가)", "c": ORANGE, "t": "bar"}, {"n": "분배 (잔액 감소)", "c": GREEN, "t": "bar"},
                              {"n": "순증", "c": NAVY, "t": "dot"}])
    flow = make_card(("분기별" if quarterly else "월별") + " 집행·분배·순증", html.Div([flow_legend, make_flow_chart(mon, H_FLOW, quarterly)]),
                     sub=("PCAP 분기말 기준 · " if quarterly else "") + "위는 집행, 아래는 분배, 점은 순증", height=H_FLOW + 70)
    summary = make_card("지표별 요약", make_summary_table(kpi_rows, unit), sub=period + " · 단위 " + unit, height=H_FLOW + 70)
    row4 = html.Div([summary, flow], style=dict(GRID2, marginBottom="14px"))

    # 5단 펀드
    funds = data["funds"]
    fy = funds[(funds["YEAR"] == year) & ((funds["CLS"] == cls) if cls != ALL else True)]
    fund_cards = []
    for m in METRICS:
        total = float(kpi_rows[m["k"]]["ACTUAL"]) if m["k"] in kpi_rows else 0.0
        top_idx = fy[m["k"]].abs().nlargest(TOP_N).index
        top_sum = float(fy.loc[top_idx, m["k"]].sum()) if len(fy) else 0.0
        mixed = m["k"] == "순증" and bool((fy[m["k"]] < 0).any())   # 순증에 음수 펀드가 있으면 비중 생략
        right = "상위 비중 " + (pct(top_sum / total) if (total > 0 and not mixed) else "–")
        fund_cards.append(make_card([key_dot(m["c"], 10), m["n"] + " 상위 %d개" % TOP_N],
                                    make_fund_table(fy, m, total, unit, local_unit, show_cls=(cls == ALL)), right=right))
    fund_section = make_card("누적 실적을 이끈 펀드", html.Div(fund_cards, style=GRID2),
                             sub=period + " 기준 · 막대와 비중은 원화, 펀드 통화 병기 · 순증은 잔액을 늘린 펀드 오른쪽, 줄인 펀드 왼쪽")

    parts = [
        html.Div([html.Span(period + " · " + ("전체 자산군" if cls == ALL else cls), style={"fontWeight": "600", "color": "#4B5563"}),
                  html.Span(pace_text, style={"color": MUTED})], style={"fontSize": "13px", "margin": "12px 0 10px"}),
        kpi_cards,
        html.Div(yearly, style={"marginBottom": "14px"}),
        html.Div(cum_section, style={"marginBottom": "14px"}),
        row4,
        html.Div(fund_section, style={"marginBottom": "14px"}),
    ]
    if cls == ALL:
        parts.append(make_card("자산군별 목표·현황·달성률", make_class_table(kpi_year, data["classes"], unit), sub=period + " · 단위 " + unit))
    return html.Div(parts)


# ---------- 진입점 ----------
def render(data):
    if not data:
        return html.Div("데이터를 로드할 수 없습니다.")
    asof = data["asof"]
    header = html.Div([
        html.Span("대체투자 약정 현황", style={"fontSize": "18px", "fontWeight": "700", "color": INK}),
        html.Span("약정 기준일 %s · 집행·분배 기준일 %s(PCAP) · 단위 %s · 순증 = 집행 − 분배"
                  % (asof.strftime("%Y-%m-%d"), data.get("asof_flow", asof).strftime("%Y-%m-%d"), data["unit"]),
                  style={"fontSize": "12.5px", "color": MUTED, "marginLeft": "12px"}),
    ], style={"margin": "4px 0 10px"})
    tabs = dcc.Tabs(value="tab-ALT_Manage-" + ALL, children=[
        dcc.Tab(label=c, value="tab-ALT_Manage-" + c, style=TAB_STYLE, selected_style=SELECTED_TAB_STYLE,
                children=html.Div(make_page(data, c), style={"padding": "4px 0"}))
        for c in [ALL] + list(data["classes"])
    ])
    return html.Div([header, tabs], style={"fontFamily": "inherit"})

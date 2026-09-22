#!/usr/bin/env python3
"""CSV 입력을 대시보드용 데이터로 변환한다.

입력
  data/targets.csv       year, asset_class, target
  data/transactions.csv  date(YYYY-MM-DD), fund, asset_class, type(약정|집행|분배), amount

출력
  data/data.js           index.html 이 읽는 월별 집계 (window.ALT_DATA)
  dist/dashboard.html    데이터를 내장한 단일 파일 (메일 첨부·공유용)

사용법
  python3 scripts/build.py [--as-of YYYY-MM-DD] [--unit 억원] [--note "메모"]
  --as-of 를 생략하면 거래 내역의 마지막 날짜를 기준일로 쓴다.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DIST = ROOT / "dist"

TYPE_KEY = {
    "약정": "commitment", "commitment": "commitment", "commit": "commitment",
    "집행": "drawdown", "출자": "drawdown", "drawdown": "drawdown", "call": "drawdown", "capital call": "drawdown",
    "분배": "distribution", "회수": "distribution", "distribution": "distribution", "dist": "distribution",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def to_number(s: str) -> float:
    s = s.replace(",", "").replace(" ", "")
    return float(s) if s else 0.0


def build(as_of: dt.date | None, unit: str, note: str | None) -> dict:
    targets_raw = read_csv(DATA / "targets.csv")
    tx_raw = read_csv(DATA / "transactions.csv")

    classes: list[str] = []
    for row in targets_raw + tx_raw:
        c = row.get("asset_class", "")
        if c and c not in classes:
            classes.append(c)

    targets = [
        {"year": int(r["year"]), "assetClass": r["asset_class"], "target": to_number(r["target"])}
        for r in targets_raw if r.get("year")
    ]

    flows: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"commitment": 0.0, "drawdown": 0.0, "distribution": 0.0, "commitCount": 0})
    last_date: dt.date | None = None
    skipped = 0
    for r in tx_raw:
        key = TYPE_KEY.get(r.get("type", "").lower()) or TYPE_KEY.get(r.get("type", ""))
        if not key or not r.get("date"):
            skipped += 1
            continue
        d = dt.date.fromisoformat(r["date"][:10])
        if as_of and d > as_of:
            continue
        last_date = d if last_date is None or d > last_date else last_date
        cell = flows[(d.strftime("%Y-%m"), r["asset_class"])]
        cell[key] += to_number(r["amount"])
        if key == "commitment":
            cell["commitCount"] += 1

    if skipped:
        print(f"warning: {skipped} transaction rows skipped (unknown type or empty date)")

    effective_as_of = as_of or last_date or dt.date.today()
    flow_rows = [
        {"month": month, "assetClass": cls, **{k: round(v, 2) if isinstance(v, float) else v for k, v in cell.items()}}
        for (month, cls), cell in sorted(flows.items())
    ]
    data = {
        "unit": unit,
        "asOf": effective_as_of.isoformat(),
        "assetClasses": classes,
        "targets": targets,
        "flows": flow_rows,
    }
    if note:
        data["note"] = note
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--as-of", help="기준일 (YYYY-MM-DD). 생략 시 마지막 거래일")
    ap.add_argument("--unit", default="억원", help="금액 단위 표기 (기본: 억원)")
    ap.add_argument("--note", help="대시보드 하단에 표시할 메모 (예: 샘플 데이터 안내)")
    args = ap.parse_args()

    as_of = dt.date.fromisoformat(args.as_of) if args.as_of else None
    data = build(as_of, args.unit, args.note)
    payload = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")

    DATA.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    (DATA / "data.js").write_text(
        "// scripts/build.py 가 생성한 파일입니다. 직접 수정하지 말고 CSV를 고친 뒤 다시 빌드하세요.\n"
        f"window.ALT_DATA = {payload};\n", encoding="utf-8")

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    marker = '<script src="data/data.js"></script>'
    if marker not in html:
        raise SystemExit("index.html 에서 data.js 로드 태그를 찾지 못했습니다.")
    single = html.replace(marker, f"<script>\nwindow.ALT_DATA = {payload};\n</script>")
    (DIST / "dashboard.html").write_text(single, encoding="utf-8")

    print(f"as of {data['asOf']}: {len(data['targets'])} target rows, {len(data['flows'])} monthly cells, "
          f"{len(data['assetClasses'])} asset classes")
    print(f"wrote {DATA / 'data.js'} and {DIST / 'dashboard.html'}")


if __name__ == "__main__":
    main()

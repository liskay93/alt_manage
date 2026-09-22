#!/usr/bin/env python3
"""대시보드 시연용 샘플 데이터를 생성한다.

생성 파일
  data/targets.csv       연도·자산군별 목표 약정
  data/transactions.csv  약정·집행·분배 거래 내역 (펀드 단위)

실제 데이터를 쓸 때는 이 스크립트를 실행하지 말고, 두 CSV를 같은 형식으로
채운 뒤 scripts/build.py 를 실행한다. 모든 금액 단위는 억원.
"""
from __future__ import annotations

import csv
import datetime as dt
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AS_OF = dt.date(2026, 9, 22)          # 기준일: 이 날짜 이후 거래는 생성하지 않는다
random.seed(20260922)

CLASSES = ["PE", "PD", "부동산", "인프라"]

# 연도·자산군별 목표 약정 (억원). 목표는 2021년부터 관리.
TARGETS = {
    2021: {"PE": 800,  "PD": 500,  "부동산": 500, "인프라": 400},
    2022: {"PE": 900,  "PD": 600,  "부동산": 500, "인프라": 500},
    2023: {"PE": 1000, "PD": 800,  "부동산": 600, "인프라": 600},
    2024: {"PE": 1100, "PD": 900,  "부동산": 500, "인프라": 700},
    2025: {"PE": 1200, "PD": 1000, "부동산": 500, "인프라": 800},
    2026: {"PE": 1400, "PD": 1200, "부동산": 500, "인프라": 900},
}
# 목표가 없던 과거 빈티지: 집행·분배 이력이 있어야 하므로 약정 규모만 둔다.
LEGACY = {
    2018: {"PE": 500, "PD": 300, "부동산": 400, "인프라": 300},
    2019: {"PE": 600, "PD": 400, "부동산": 400, "인프라": 300},
    2020: {"PE": 700, "PD": 450, "부동산": 450, "인프라": 350},
}
# 연도별 목표 대비 실제 약정 비율 (연도 분위기)
ACHIEVE = {2018: 1.0, 2019: 1.0, 2020: 1.0, 2021: 1.05, 2022: 0.97,
           2023: 0.91, 2024: 1.06, 2025: 0.89, 2026: 0.70}

# 가상의 펀드 이름 (실존 운용사와 무관)
NAMES = {
    "PE":   ["한강 그로스", "설악 바이아웃", "태백 세컨더리", "지리 미드캡", "북한산 벤처"],
    "PD":   ["백두 다이렉트렌딩", "한라 메자닌", "오대 스페셜시츄에이션", "속리 시니어론"],
    "부동산": ["남산 오피스", "해운대 물류", "판교 코어플러스", "송도 리츠"],
    "인프라": ["동해 신재생", "서해 에너지", "영남 교통", "호남 데이터센터"],
}

# 자산군별 집행 페이스: 약정 후 n년차 말 누적 집행률
PACE = {
    "PE":   [0.25, 0.55, 0.80, 0.95, 1.00],
    "PD":   [0.45, 0.85, 1.00],
    "부동산": [0.55, 0.90, 1.00],
    "인프라": [0.30, 0.60, 0.85, 1.00],
}
# 자산군별 분배 특성: (분배 시작 개월, 월별 분배 발생 확률, 집행액 대비 월 분배 비율 범위)
DIST = {
    "PE":   (30, 0.30, (0.03, 0.12)),
    "PD":   (9,  0.70, (0.012, 0.03)),
    "부동산": (12, 0.60, (0.010, 0.025)),
    "인프라": (24, 0.40, (0.02, 0.06)),
}


def add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    return dt.date(d.year + y, m + 1, min(d.day, 28))


def cum_fraction(cls: str, month_idx: int) -> float:
    """약정 후 month_idx개월 시점의 누적 집행률 (선형 보간)."""
    pace = PACE[cls]
    years = month_idx / 12
    if years >= len(pace):
        return 1.0
    lo = int(years)
    prev = pace[lo - 1] if lo > 0 else 0.0
    return prev + (pace[lo] - prev) * (years - lo)


def round10(x: float) -> int:
    return int(round(x / 10.0)) * 10


def main() -> None:
    DATA.mkdir(exist_ok=True)
    counters = {c: 0 for c in CLASSES}
    tx: list[tuple[dt.date, str, str, str, int]] = []

    vintages = sorted(set(LEGACY) | set(TARGETS))
    for year in vintages:
        base = LEGACY.get(year) or TARGETS[year]
        for cls in CLASSES:
            total = base[cls] * ACHIEVE[year]
            n_funds = random.choice([2, 3, 3, 4]) if cls == "PE" else random.choice([2, 2, 3])
            weights = [random.uniform(0.7, 1.3) for _ in range(n_funds)]
            wsum = sum(weights)
            amounts = [round10(total * w / wsum) for w in weights]
            last_month = AS_OF.month if year == AS_OF.year else 12
            months = sorted(random.sample(range(1, last_month + 1), n_funds))
            for amt, mon in zip(amounts, months):
                if amt <= 0:
                    continue
                day = random.randint(3, 27)
                commit_date = dt.date(year, mon, day)
                if commit_date > AS_OF:
                    continue
                counters[cls] += 1
                name = f"{NAMES[cls][counters[cls] % len(NAMES[cls])]} {counters[cls]}호"
                tx.append((commit_date, name, cls, "약정", amt))

                # 집행: 페이스 곡선을 따라 월별 캐피털콜, 일부 달은 건너뛰고 다음 달에 몰림
                called = 0
                carry = 0.0
                for k in range(1, 12 * len(PACE[cls]) + 2):
                    d = add_months(commit_date, k)
                    if d > AS_OF:
                        break
                    step = amt * (cum_fraction(cls, k) - cum_fraction(cls, k - 1))
                    carry += step * random.uniform(0.7, 1.3)
                    if random.random() < 0.35 and k < 12 * len(PACE[cls]):
                        continue
                    call = min(int(round(carry)), amt - called)
                    carry = 0.0
                    call_date = dt.date(d.year, d.month, random.randint(3, 27))
                    if call >= 5 and call_date <= AS_OF:
                        called += call
                        tx.append((call_date, name, cls, "집행", call))

                # 분배: 자산군별 시작 시점 이후 확률적으로 발생, 규모는 그 시점 누적 집행액에 비례
                start, prob, (lo, hi) = DIST[cls]
                called_by: dict[int, int] = {}
                run = 0
                for date, fname, _c, typ, a in tx:
                    if fname == name and typ == "집행":
                        run += a
                        called_by[(date.year - commit_date.year) * 12 + date.month - commit_date.month] = run
                cum_called = 0
                for k in range(start, 12 * 10):
                    d = add_months(commit_date, k)
                    if d > AS_OF:
                        break
                    cum_called = max([v for kk, v in called_by.items() if kk <= k] or [0])
                    if cum_called <= 0 or random.random() > prob:
                        continue
                    growth = 1.0 + 0.6 * min(k - start, 48) / 48   # 후반부로 갈수록 회수 규모 증가
                    dist = int(round(cum_called * random.uniform(lo, hi) * growth))
                    dist_date = dt.date(d.year, d.month, random.randint(3, 27))
                    if dist >= 3 and dist_date <= AS_OF:
                        tx.append((dist_date, name, cls, "분배", dist))

    tx.sort(key=lambda r: (r[0], r[3], r[1]))

    with (DATA / "targets.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["year", "asset_class", "target"])
        for year in sorted(TARGETS):
            for cls in CLASSES:
                w.writerow([year, cls, TARGETS[year][cls]])

    with (DATA / "transactions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["date", "fund", "asset_class", "type", "amount"])
        for date, name, cls, typ, amt in tx:
            w.writerow([date.isoformat(), name, cls, typ, amt])

    n_commit = sum(1 for r in tx if r[3] == "약정")
    print(f"targets.csv: {len(TARGETS) * len(CLASSES)} rows")
    print(f"transactions.csv: {len(tx)} rows ({n_commit} funds, through {AS_OF})")


if __name__ == "__main__":
    main()

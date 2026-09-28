# sql/*.sql 을 모아 전달용 코드모음 deliver/01_SQL.txt 를 만든다 (워드는 deliver/make_sql_docx.js 가 이 파일로 만든다)
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["ALT_Fund.sql", "ALT_Commit.sql", "ALT_PCAP.sql", "ALT_FX.sql"]

NOTEBOOK = '''# 네 파일을 sql/ 에 넣은 뒤 순서대로 실행. 각 셀 결과(출력 그대로)를 보내 주시면 됩니다
# 00) 폴더 맞추기: loader.py 가 있는 TPA Dashboard 폴더로 이동 (dash_board.ipynb 안에서 돌리면 필요 없음)
import os, sys
BASE = r"여기에_TPA_Dashboard_폴더_경로"          # 예: r"C:\\Users\\...\\TPA Dashboard"  또는  "/home/.../TPA Dashboard"
if os.path.isdir(BASE):
    os.chdir(BASE)
sys.path.insert(0, os.getcwd())
print("현재 폴더:", os.getcwd())
print("loader.py:", os.path.exists("loader.py"), "| sql 폴더:", os.path.isdir("sql"), "| data/ALT_Target.xlsx:", os.path.exists("data/ALT_Target.xlsx"))

import loader
import pandas as pd
conn = loader.create_connection()

# 0) 오류가 나면: 오류 코드와 위치를 찍는다 (파일 이름만 바꿔서 실행)
import cx_Oracle
sql = open("sql/ALT_Fund.sql", encoding="utf-8").read()
cur = conn.cursor()
try:
    cur.execute(sql)
    print("실행 OK", len(cur.fetchmany(5)), "행 미리보기")
except cx_Oracle.DatabaseError as e:
    err, = e.args
    print(err.message)
    off = err.offset
    print("offset", off)
    print("[문자 기준]", repr(sql[max(0, off - 60):off + 30]))
    b = sql.encode("utf-8")
    print("[바이트 기준]", repr(b[max(0, off - 60):off + 30].decode("utf-8", "replace")))

# 0-1) 원천 테이블·컬럼 이름 확인 (둘 다 떠야 정상)
print(pd.read_sql("SELECT NPS_FUND_CD, DEAL_NM, CURR_CD, VNTG_YR FROM FEIAI0488NTA WHERE ROWNUM <= 3", conn))
print(pd.read_sql("SELECT FUND_CD, ATVT_PGM_FUND_CD FROM MAAMC0101DTM_CW01 WHERE ROWNUM <= 3", conn))
# 프로그램 코드 앞 3자리 분포: XPV(사모벤처)·XRE(부동산)·XIF(인프라) 외의 값이 있으면 알려 주세요
print(pd.read_sql("SELECT UPPER(SUBSTR(TRIM(ATVT_PGM_FUND_CD), 1, 3)) AS prefix, COUNT(*) AS cnt FROM MAAMC0101DTM_CW01 GROUP BY UPPER(SUBSTR(TRIM(ATVT_PGM_FUND_CD), 1, 3)) ORDER BY 2 DESC", conn))
# 조인 확인: 약정 테이블 펀드 중 MAAMC0101DTM_CW01 에서 찾아지는 펀드 수 (TOTAL 과 비슷해야 정상)
print(pd.read_sql("SELECT COUNT(*) AS total, SUM(CASE WHEN EXISTS (SELECT 1 FROM MAAMC0101DTM_CW01 q WHERE q.FUND_CD = a.NPS_FUND_CD) THEN 1 ELSE 0 END) AS matched FROM FEIAI0488NTA a", conn))

# 0-2) 날짜 형식이 잘못된 값 찾기 (ORA-01840 원인). 세 결과 모두 비어 있으면 깨끗한 것
print(pd.read_sql("SELECT AGRT_DT, COUNT(*) AS cnt FROM FEIAI0488NTA WHERE NOT REGEXP_LIKE(NVL(AGRT_DT, 'x'), '^[0-9]{8}$') GROUP BY AGRT_DT", conn))
print(pd.read_sql("SELECT PCAP_DATE, COUNT(*) AS cnt FROM FEIAI0432NTA WHERE NOT REGEXP_LIKE(NVL(PCAP_DATE, 'x'), '^[0-9]{8}$') GROUP BY PCAP_DATE", conn))
print(pd.read_sql("SELECT WRK_DT, COUNT(*) AS cnt FROM FMCBI0006NTA WHERE NOT REGEXP_LIKE(NVL(WRK_DT, 'x'), '^[0-9]{8}$') GROUP BY WRK_DT", conn))

# 1) 펀드 마스터: 펀드 수, 자산군 분포(미분류가 많으면 MAAMC0101DTM_CW01 조인 문제), 이름 없는 펀드 수
raw_fund = loader.load_data(conn, "ALT_Fund.sql")
print(len(raw_fund), "펀드")
print(raw_fund["ASSET_CLS"].value_counts(dropna=False))
print("이름=코드인 펀드:", (raw_fund["FUND_NM"] == raw_fund["FUND_CD"]).sum())
print(raw_fund.head())

# 2) 약정: 건수, 통화별 건수와 로컬 합계, 날짜 범위. 금액은 원본(원, 달러 …). AMT_KRW 는 KRW 펀드만 값이 있어야 정상
raw_commit = loader.load_data(conn, "ALT_Commit.sql")
print(len(raw_commit), "건", raw_commit["WRK_DT"].min(), "~", raw_commit["WRK_DT"].max())
print(raw_commit.groupby("CCY")[["AMT_LOCAL", "AMT_KRW"]].agg(["count", "sum"]).round(0))
print(raw_commit.head())

# 3) PCAP: 최신 제공일, 기준일 범위, 통화유형x통화 분포. 금액은 원본, FUNDED_AMT 는 음수(원본 부호)여야 정상
raw_pcap = loader.load_data(conn, "ALT_PCAP.sql")
print(len(raw_pcap), "행 | 제공일", raw_pcap["PROV_DT"].max(), "| 기준일", raw_pcap["WRK_DT"].min(), "~", raw_pcap["WRK_DT"].max())
print(raw_pcap.groupby(["CURR_TYP", "CURR_ID"]).size())
print(raw_pcap[["FUNDED_AMT", "DISTRB_AMT", "NAV_AMT"]].describe().round(0))
print(raw_pcap.sort_values(["FUND_CD", "WRK_DT"]).head(8))

# 4) 환율: 통화별 행 수와 최근 값. KRW 가 꼭 있어야 하고, 값은 1 USD 당 통화 단위
raw_fx = loader.load_data(conn, "ALT_FX.sql")
print(len(raw_fx), "행", raw_fx["WRK_DT"].min(), "~", raw_fx["WRK_DT"].max())
print(raw_fx.sort_values("WRK_DT").groupby("CURR_ID").tail(1))'''

CHECKS = """- MAAMC0101DTM_CW01 의 펀드코드 컬럼을 'funcd_cd' 로 받아 FUND_CD 로 적었습니다. 0-1) 둘째 줄에서 ORA-00904 가 나거나 조인 확인의 MATCHED 가 0 에 가까우면 조인 키가 다른 것이니 알려 주세요
- 프로그램 코드 컬럼은 ATVT_PGM_FUND_CD, 테이블은 MAAMC0101DTM_CW01 입니다
- 조인은 LEFT JOIN 대신 Oracle (+) 외부조인, 주석은 -- 대신 맨 위 /* */ 한 곳으로 바꿨습니다 (missing keyword 대응)
- 펀드명은 FEIAI0488NTA.DEAL_NM 에서 바로 가져옵니다 (FEIAI0432NTA 조인 제거)
- FEIAI0432NTA 의 RPRT_NM 은 UPPER(...) LIKE '%GCM%' 로 골랐습니다. GCM 이 들어간 다른 값이 있으면 알려 주세요
- ALT_Commit.sql 의 원화(AMT_KRW)는 KRW 펀드만 채워지고, 외화 약정은 processor 가 약정일 환율로 원화 환산합니다
- SQL 은 금액을 나누지 않고 원본 그대로 돌려줍니다 (원, 달러 …, 집행은 음수 부호 그대로). 억원·백만 변환과 부호 처리는 processor 가 합니다
- 날짜도 원본 문자열로 돌려줍니다 (TO_DATE 안 씀). 형식이 잘못된 값이 섞여 있어 ORA-01840 이 났기 때문입니다. 변환은 processor 가 하고, 잘못된 행은 빼면서 건수를 화면 경고로 알립니다
- SQL 파일에는 ORDER BY 를 넣지 않아도 됩니다. 정렬은 processor 가 하고, 눈으로 볼 때는 df.sort_values("WRK_DT", ascending=False) 로 봅니다
- ALT_FX.sql 은 KRW 와 약정 테이블에 있는 통화만, 2018-01-01 이후 일별로 가져옵니다
- 오류가 나면 0) 셀 출력을 그대로 보내 주세요. 오류 위치 앞뒤 글자가 찍혀서 원인 줄을 바로 짚을 수 있습니다
- No module named 'loader' 가 나면 00) 의 BASE 를 loader.py 가 있는 폴더로 바꾸세요. 세 개가 모두 True 로 찍혀야 합니다"""


def main():
    parts = []
    for f in FILES:
        body = (ROOT / "sql" / f).read_text(encoding="utf-8").rstrip("\n")
        assert ";" not in body, f
        parts.append("=====FILE: sql/%s=====\n%s\n" % (f, body))
    out = "\n".join(parts) + "\n=====FILE: 노트북 확인 코드 (dash_board.ipynb 또는 새 셀)=====\n" + NOTEBOOK + "\n\n=====확인 사항=====\n" + CHECKS + "\n"
    (ROOT / "deliver" / "01_SQL.txt").write_text(out, encoding="utf-8")
    print("written deliver/01_SQL.txt", len(out), "chars")


if __name__ == "__main__":
    main()

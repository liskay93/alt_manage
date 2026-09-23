# sql/*.sql 을 모아 전달용 코드모음 deliver/01_SQL.txt 를 만든다 (워드는 deliver/make_sql_docx.js 가 이 파일로 만든다)
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["ALT_Fund.sql", "ALT_Commit.sql", "ALT_PCAP.sql", "ALT_FX.sql"]

NOTEBOOK = '''# 네 파일을 sql/ 에 넣은 뒤 순서대로 실행. 각 셀 결과(출력 그대로)를 보내 주시면 됩니다
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
print(pd.read_sql("SELECT FUND_CD, AVTV_PGM_CD FROM MAAMC0101DTM WHERE ROWNUM <= 3", conn))

# 1) 펀드 마스터: 펀드 수, 자산군 분포(미분류가 많으면 MAAMC0101DTM 조인 문제), 이름 없는 펀드 수
raw_fund = loader.load_data(conn, "ALT_Fund.sql")
print(len(raw_fund), "펀드")
print(raw_fund["ASSET_CLS"].value_counts(dropna=False))
print("이름=코드인 펀드:", (raw_fund["FUND_NM"] == raw_fund["FUND_CD"]).sum())
print(raw_fund.head())

# 2) 약정: 건수, 통화별 건수와 로컬 합계, 날짜 범위. AMT_KRW 는 KRW 펀드만 값이 있어야 정상
raw_commit = loader.load_data(conn, "ALT_Commit.sql")
print(len(raw_commit), "건", raw_commit["WRK_DT"].min(), "~", raw_commit["WRK_DT"].max())
print(raw_commit.groupby("CCY")[["AMT_LOCAL", "AMT_KRW"]].agg(["count", "sum"]).round(1))
print(raw_commit.head())

# 3) PCAP: 최신 제공일, 기준일 범위, 통화유형x통화 분포. FUNDED_AMT 는 양수여야 정상
raw_pcap = loader.load_data(conn, "ALT_PCAP.sql")
print(len(raw_pcap), "행 | 제공일", raw_pcap["PROV_DT"].max(), "| 기준일", raw_pcap["WRK_DT"].min(), "~", raw_pcap["WRK_DT"].max())
print(raw_pcap.groupby(["CURR_TYP", "CURR_ID"]).size())
print(raw_pcap[["FUNDED_AMT", "DISTRB_AMT", "NAV_AMT"]].describe().round(1))
print(raw_pcap.sort_values(["FUND_CD", "WRK_DT"]).head(8))

# 4) 환율: 통화별 행 수와 최근 값. KRW 가 꼭 있어야 하고, 값은 1 USD 당 통화 단위
raw_fx = loader.load_data(conn, "ALT_FX.sql")
print(len(raw_fx), "행", raw_fx["WRK_DT"].min(), "~", raw_fx["WRK_DT"].max())
print(raw_fx.sort_values("WRK_DT").groupby("CURR_ID").tail(1))'''

CHECKS = """- MAAMC0101DTM 의 펀드코드 컬럼을 'funcd_cd' 로 받아 FUND_CD 로 적었습니다. 0-1) 둘째 줄에서 ORA-00904 가 나면 이름이 다른 것이니 알려 주세요
- 조인은 LEFT JOIN 대신 Oracle (+) 외부조인, 주석은 -- 대신 맨 위 /* */ 한 곳으로 바꿨습니다 (missing keyword 대응)
- 펀드명은 FEIAI0488NTA.DEAL_NM 에서 바로 가져옵니다 (FEIAI0432NTA 조인 제거)
- FEIAI0432NTA 의 RPRT_NM 은 UPPER(...) LIKE '%GCM%' 로 골랐습니다. GCM 이 들어간 다른 값이 있으면 알려 주세요
- ALT_Commit.sql 의 원화(AMT_KRW)는 KRW 펀드만 채워지고, 외화 약정은 processor 가 약정일 환율로 환산합니다
- 단위 변환: 통화가 KRW 면 1억으로 나눠 억원, 그 외는 100만으로 나눠 백만 (원천 단위 1 기준)
- ALT_FX.sql 은 KRW 와 약정 테이블에 있는 통화만, 2018-01-01 이후 일별로 가져옵니다
- 오류가 나면 0) 셀 출력을 그대로 보내 주세요. 오류 위치 앞뒤 글자가 찍혀서 원인 줄을 바로 짚을 수 있습니다"""


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

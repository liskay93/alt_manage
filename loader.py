# DB 연결과 SQL 파일 로드.
# 실제 프로젝트(TPA Dashboard)의 loader.py 와 같은 인터페이스: create_connection(), load_data(conn, "파일.sql")
# 이 저장소에서는 로컬 확인용으로만 쓰며, 사내 환경에서는 기존 loader.py 를 그대로 쓴다.
import os
from pathlib import Path

import pandas as pd

SQL_DIR = Path(__file__).resolve().parent / "sql"


def create_connection():
    """cx_Oracle 연결. 접속 정보는 환경변수 ORACLE_USER / ORACLE_PASSWORD / ORACLE_DSN 에서 읽는다."""
    import cx_Oracle  # 사내 환경에만 있음

    return cx_Oracle.connect(os.environ["ORACLE_USER"], os.environ["ORACLE_PASSWORD"], os.environ["ORACLE_DSN"])


def load_data(conn, sql_file):
    """sql/ 아래 파일을 읽어 실행하고 DataFrame 으로 돌려준다. Oracle 은 열 이름을 대문자로 돌려준다."""
    sql = (SQL_DIR / sql_file).read_text(encoding="utf-8")
    return pd.read_sql(sql, conn)

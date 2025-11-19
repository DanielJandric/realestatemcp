"""
Utility script to execute raw SQL against Supabase via the exec_sql RPC.
Usage: python exec_sql.py query.sql
"""
import json
import sys
from pathlib import Path

from supabase import create_client

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRt"
    "dGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoy"
    "MDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def run_query(sql_text: str) -> None:
    response = supabase.rpc("exec_sql", {"query": sql_text}).execute()
    print(json.dumps(response.data, indent=2, ensure_ascii=False))


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python exec_sql.py <sql_file>")
        sys.exit(1)

    sql_path = Path(sys.argv[1])
    if not sql_path.exists():
        print(f"SQL file not found: {sql_path}")
        sys.exit(1)

    sql_text = sql_path.read_text(encoding="utf-8").strip().rstrip(";")
    run_query(sql_text)


if __name__ == "__main__":
    main()


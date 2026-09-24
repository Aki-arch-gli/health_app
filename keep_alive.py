import os
import os
from supabase import create_client


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing.")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


try:
    # 軽い読み取り処理を行ってSupabaseへアクセス
    response = (
        supabase
        .table("app_users")
        .select("username")
        .limit(1)
        .execute()
    )

    print("Supabase keep-alive succeeded.")
    print(f"Fetched {len(response.data or [])} row(s).")

except Exception as e:
    print(f"Supabase keep-alive failed: {e}")
    raise
"""Daily records for the authenticated account and its approved viewers."""

import hashlib
import hmac
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from modules.database import connect

TOKYO = ZoneInfo("Asia/Tokyo")
MOODS = ("元気", "ふつう", "ゆっくり休みたい")
APPETITES = ("いつもどおり", "少なめ", "多め")
STEPS = (
    "冷蔵庫にある食材を一つ確かめる",
    "食べたいものを一つ思い浮かべる",
    "食事の前に少しひと息つく",
    "最近おいしかった料理を思い出す",
    "用意しやすそうな献立を一つ選ぶ",
    "お気に入りの器で食事を楽しむ",
    "次に食べたい料理を一つ考える",
)
INVITE_HOURS = 24
PASSWORD_ITERATIONS = 600_000
MEASURE_COLUMNS = {"水分": ("water",), "体重": ("weight",), "血圧": ("high", "low")}


def today_in_japan():
    return datetime.now(TOKYO).date()


def init_wellbeing():
    with closing(connect()) as db, db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS local_accounts (
                id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, salt BLOB NOT NULL, password BLOB NOT NULL,
                role TEXT NOT NULL, age INTEGER NOT NULL, gender TEXT NOT NULL,
                height REAL NOT NULL, weight REAL NOT NULL, disease TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wellbeing_days (
                owner TEXT NOT NULL, day TEXT NOT NULL, mood TEXT, appetite TEXT, step INTEGER NOT NULL,
                PRIMARY KEY (owner, day)
            );
            CREATE TABLE IF NOT EXISTS wellbeing_invites (
                token_hash TEXT PRIMARY KEY, owner TEXT NOT NULL UNIQUE, owner_name TEXT NOT NULL,
                details INTEGER NOT NULL, expires_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wellbeing_shares (
                owner TEXT NOT NULL, viewer TEXT NOT NULL, owner_name TEXT NOT NULL, viewer_name TEXT NOT NULL,
                details INTEGER NOT NULL, since TEXT NOT NULL,
                PRIMARY KEY (owner, viewer)
            );
            CREATE INDEX IF NOT EXISTS wellbeing_shares_viewer ON wellbeing_shares(viewer);
            CREATE TABLE IF NOT EXISTS wellbeing_messages (
                id INTEGER PRIMARY KEY, owner TEXT NOT NULL, viewer TEXT NOT NULL,
                sent_at TEXT NOT NULL, sender TEXT NOT NULL, body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wellbeing_measures (
                owner TEXT NOT NULL, day TEXT NOT NULL, water INTEGER CHECK (water >= 0),
                weight REAL, high INTEGER, low INTEGER, PRIMARY KEY (owner, day)
            );
            CREATE TABLE IF NOT EXISTS dinner_favorites (
                owner TEXT NOT NULL, staple TEXT NOT NULL, main TEXT NOT NULL, side TEXT NOT NULL,
                people INTEGER NOT NULL CHECK (people BETWEEN 1 AND 6),
                PRIMARY KEY (owner, staple, main, side, people)
            );
        """)


def dinner_favorite_keys(owner):
    with closing(connect()) as db:
        return db.execute(
            "SELECT staple, main, side, people FROM dinner_favorites WHERE owner=? ORDER BY rowid DESC",
            (owner,),
        ).fetchall()


def set_dinner_favorite(owner, key, saved):
    with closing(connect()) as db, db:
        if saved:
            db.execute(
                "INSERT INTO dinner_favorites VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                (owner, *key),
            )
        else:
            db.execute(
                "DELETE FROM dinner_favorites WHERE owner=? AND staple=? AND main=? AND side=? AND people=?",
                (owner, *key),
            )


def _password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)


def register_local(username, password, role, age, gender, height, weight, disease):
    username = username.strip()
    if not re.fullmatch(r"[\w .-]{1,48}", username):
        return False, "ユーザーIDは文字・数字・空白・ハイフン・ピリオドで48文字以内にしてください。"
    if not 10 <= len(password) <= 128:
        return False, "パスワードは10〜128文字で入力してください。"
    salt = secrets.token_bytes(16)
    try:
        with closing(connect()) as db, db:
            db.execute(
                "INSERT INTO local_accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (secrets.token_hex(16), username, salt, _password_hash(password, salt),
                 role, age, gender, height, weight, disease),
            )
    except sqlite3.IntegrityError:
        return False, "このユーザーIDはすでに使われています。"
    return True, ""


def authenticate_local(username, password):
    if not 1 <= len(password) <= 128 or len(username) > 48:
        return None
    with closing(connect()) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM local_accounts WHERE username=?", (username.strip(),)).fetchone()
    salt = row["salt"] if row else bytes(16)
    expected = row["password"] if row else bytes(32)
    if not hmac.compare_digest(_password_hash(password, salt), expected) or row is None:
        return None
    return {key: row[key] for key in ("id", "username", "role", "age", "gender", "height", "weight", "disease")}


def save_day(owner, day, mood, appetite, step):
    if mood not in (*MOODS, None) or appetite not in (*APPETITES, None):
        raise ValueError("Unknown check-in option")
    with closing(connect()) as db, db:
        db.execute(
            """INSERT INTO wellbeing_days (owner, day, mood, appetite, step) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (owner, day) DO UPDATE SET mood=excluded.mood, appetite=excluded.appetite, step=excluded.step""",
            (owner, day.isoformat(), mood, appetite, bool(step)),
        )


def own_days(owner, through):
    with closing(connect()) as db:
        return db.execute(
            "SELECT day, mood, appetite, step FROM wellbeing_days WHERE owner=? AND day<=? ORDER BY day DESC",
            (owner, through.isoformat()),
        ).fetchall()


def week_summary(days, today):
    recorded = {date.fromisoformat(day) for day, *_ in days}
    week = [(today - timedelta(days=offset)) for offset in range(6, -1, -1)]
    return [(day, day in recorded) for day in week]


def _digest(code):
    return hashlib.sha256(code.encode()).hexdigest()


def create_invite(owner, owner_name, details, now):
    code = secrets.token_urlsafe(18)
    with closing(connect()) as db, db:
        db.execute("DELETE FROM wellbeing_invites WHERE owner=?", (owner,))
        db.execute(
            "INSERT INTO wellbeing_invites VALUES (?, ?, ?, ?, ?)",
            (_digest(code), owner, owner_name, bool(details),
             int((now + timedelta(hours=INVITE_HOURS)).timestamp())),
        )
    return code


def cancel_invite(owner):
    with closing(connect()) as db, db:
        db.execute("DELETE FROM wellbeing_invites WHERE owner=?", (owner,))


def invite_pending(owner, now, code=None):
    with closing(connect()) as db:
        saved = db.execute(
            "SELECT token_hash FROM wellbeing_invites WHERE owner=? AND expires_at>?",
            (owner, int(now.timestamp())),
        ).fetchone()
    return bool(saved and (code is None or hmac.compare_digest(saved[0], _digest(code))))


def redeem_invite(code, viewer, viewer_name, now):
    code = code.strip()
    if len(code) != 24:
        return False
    with closing(connect()) as db, db:
        db.execute("BEGIN IMMEDIATE")
        invite = db.execute(
            "SELECT owner, owner_name, details FROM wellbeing_invites WHERE token_hash=? AND expires_at>?",
            (_digest(code), int(now.timestamp())),
        ).fetchone()
        if not invite or invite[0] == viewer:
            return False
        owner, owner_name, details = invite
        db.execute("DELETE FROM wellbeing_invites WHERE token_hash=?", (_digest(code),))
        db.execute(
            """INSERT INTO wellbeing_shares VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT (owner, viewer) DO UPDATE SET owner_name=excluded.owner_name,
                 viewer_name=excluded.viewer_name, details=excluded.details, since=excluded.since""",
            (owner, viewer, owner_name, viewer_name, details, now.astimezone(TOKYO).date().isoformat()),
        )
    return True


def outgoing_shares(owner):
    with closing(connect()) as db:
        return db.execute(
            "SELECT viewer, viewer_name, details FROM wellbeing_shares WHERE owner=? ORDER BY viewer_name, viewer",
            (owner,),
        ).fetchall()


def revoke_share(owner, viewer):
    with closing(connect()) as db, db:
        db.execute("DELETE FROM wellbeing_shares WHERE owner=? AND viewer=?", (owner, viewer))


def shared_weeks(viewer, today):
    first = (today - timedelta(days=6)).isoformat()
    with closing(connect()) as db, db:
        rows = db.execute(
            """SELECT s.owner, s.owner_name, s.details, d.day,
                      CASE WHEN s.details THEN d.mood END, CASE WHEN s.details THEN d.appetite END
               FROM wellbeing_shares s LEFT JOIN wellbeing_days d ON s.owner=d.owner
                 AND d.day>=? AND d.day>=s.since AND d.day<=?
               WHERE s.viewer=? ORDER BY s.owner_name, s.owner, d.day DESC""",
            (first, today.isoformat(), viewer),
        ).fetchall()
    result = {}
    for owner, name, details, day, mood, appetite in rows:
        entry = result.setdefault(owner, {"name": name, "details": bool(details), "days": []})
        if day:
            entry["days"].append((day, mood, appetite))
    return result


def send_message(viewer, owner, body):
    body = body.strip()
    if not 1 <= len(body) <= 250:
        return False
    with closing(connect()) as db, db:
        saved = db.execute(
            """INSERT INTO wellbeing_messages (owner, viewer, sent_at, sender, body)
               SELECT owner, viewer, ?, viewer_name, ? FROM wellbeing_shares WHERE viewer=? AND owner=?""",
            (datetime.now(timezone.utc).isoformat(), body, viewer, owner),
        )
        return saved.rowcount == 1


def recent_messages(owner):
    with closing(connect()) as db:
        return db.execute(
            """SELECT m.sent_at, m.sender, m.body FROM wellbeing_messages m JOIN wellbeing_shares s
                 ON s.owner=m.owner AND s.viewer=m.viewer
               WHERE m.owner=? ORDER BY m.id DESC LIMIT 5""",
            (owner,),
        ).fetchall()


def record_water(owner, day, amount):
    with closing(connect()) as db, db:
        saved = db.execute(
            """INSERT INTO wellbeing_measures (owner, day, water) VALUES (?, ?, ?)
               ON CONFLICT (owner, day) DO UPDATE SET water=COALESCE(water, 0)+excluded.water
               RETURNING water""",
            (owner, day.isoformat(), amount),
        ).fetchone()
        return saved[0]


def save_measures(owner, day, water, weight, high, low):
    with closing(connect()) as db, db:
        if high is not None or low is not None:
            db.execute("BEGIN IMMEDIATE")
            saved = db.execute(
                "SELECT high, low FROM wellbeing_measures WHERE owner=? AND day=?",
                (owner, day.isoformat()),
            ).fetchone()
            saved_high, saved_low = saved if saved else (None, None)
            result_high = high if high is not None else saved_high
            result_low = low if low is not None else saved_low
            if result_high is not None and result_low is not None and result_high < result_low:
                raise ValueError("上の血圧と下の血圧の入力を確認してください。")
        db.execute(
            """INSERT INTO wellbeing_measures VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT (owner, day) DO UPDATE SET
                 water=COALESCE(excluded.water, water), weight=COALESCE(excluded.weight, weight),
                 high=COALESCE(excluded.high, high), low=COALESCE(excluded.low, low)""",
            (owner, day.isoformat(), water, weight, high, low),
        )


def clear_measure(owner, day, kind):
    columns = MEASURE_COLUMNS[kind]
    reset_columns = ", ".join(f"{column}=NULL" for column in columns)
    identity = (owner, day.isoformat())
    with closing(connect()) as db, db:
        db.execute(f"UPDATE wellbeing_measures SET {reset_columns} WHERE owner=? AND day=?", identity)
        db.execute(
            """DELETE FROM wellbeing_measures WHERE owner=? AND day=?
               AND water IS NULL AND weight IS NULL AND high IS NULL AND low IS NULL""",
            identity,
        )


def measure_rows(owner, through, length):
    first = through - timedelta(days=length - 1)
    with closing(connect()) as db:
        return db.execute(
            """SELECT day, water, weight, high, low FROM wellbeing_measures
               WHERE owner=? AND day BETWEEN ? AND ? ORDER BY day""",
            (owner, first.isoformat(), through.isoformat()),
        ).fetchall()

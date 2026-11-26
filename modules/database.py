import sqlite3
import csv
import os
import random
from datetime import datetime
from modules.runtime_paths import HEALTH_DB

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_NAME = HEALTH_DB



def connect():

    return sqlite3.connect(DB_NAME)



def create_tables():

    conn = connect()

    cur = conn.cursor()



    # =====================
    # 利用者情報
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        age INTEGER,

        gender TEXT,

        height REAL,

        weight REAL,

        disease TEXT,

        mode TEXT,

        point INTEGER DEFAULT 0,

        continue_days INTEGER DEFAULT 1

    )
    """)



    # =====================
    # 食事履歴
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS meal_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        date TEXT,

        breakfast TEXT,

        lunch TEXT,

        dinner TEXT,

        calorie INTEGER

    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT,

    description TEXT,

    datetime TEXT,

    place TEXT,

    target TEXT,

    capacity TEXT,

    fee TEXT,

    teacher TEXT,

    application TEXT,

    contact TEXT,

    url TEXT UNIQUE,

    image TEXT,

    pdf TEXT

    )
    """)
  
    # =====================
    # 水分管理
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS water(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        date TEXT,

        amount INTEGER

    )
    """)



    # =====================
    # 服薬管理
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicine(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        medicine TEXT,

        time TEXT

    )
    """)



    # =====================
    # 投稿
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        message TEXT,

        image TEXT,

        breakfast TEXT,

        lunch TEXT,

        dinner TEXT,

        created_at TEXT,

        likes INTEGER DEFAULT 0
    )
    """)

    # =====================
    # お気に入り週間献立
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorite_weekly_menus(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        save_date TEXT,

        monday INTEGER,
        tuesday INTEGER,
        wednesday INTEGER,
        thursday INTEGER,
        friday INTEGER,
        saturday INTEGER,
        sunday INTEGER
 
    )
    """)



    # =====================
    # いいね履歴
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        post_id INTEGER,

        username TEXT

    )
    """)



    # =====================
    # 健康コミュニティ
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS community(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        name TEXT,

        message TEXT,

        date TEXT,

        good INTEGER DEFAULT 0

    )
    """)



    # =====================
    # 健康記録
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS health_records(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        date TEXT,

        weight REAL,

        high INTEGER,

        low INTEGER,

        water INTEGER,

        medicine INTEGER,

        score INTEGER

    )
    """)

    # =====================
    # AI推薦献立データ
    # =====================

    cur.execute("""
     CREATE TABLE IF NOT EXISTS recommended_menus(

       id INTEGER PRIMARY KEY AUTOINCREMENT,

       age_min INTEGER,

       age_max INTEGER,

       disease TEXT,

       calorie INTEGER,

       breakfast TEXT,

       lunch TEXT,

       dinner TEXT,

       reason TEXT,

       nutrition TEXT,

       advice TEXT

     )
    """)

    # =====================
    # お気に入り献立
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorite_menus(

       id INTEGER PRIMARY KEY AUTOINCREMENT,

       username TEXT,

       menu_id INTEGER,

       breakfast TEXT,

       lunch TEXT,

       dinner TEXT,

       calorie INTEGER,

       reason TEXT,

       favorite_date TEXT

    )
    """)


    # =====================
    # 冷蔵庫管理
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS refrigerator(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        food TEXT,

        amount TEXT,

        expire TEXT

    )
    """)

    conn.commit()

    conn.close()

    

# ==========================
# 利用者登録
# ==========================

def add_user(

    name,
    age,
    gender,
    height,
    weight,
    disease,
    mode

):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        INSERT INTO users

        (
        name,
        age,
        gender,
        height,
        weight,
        disease,
        mode
        )

        VALUES(?,?,?,?,?,?,?)

        """,

        (

            name,

            age,

            gender,

            height,

            weight,

            disease,

            mode

        )

    )


    conn.commit()

    conn.close()





# ==========================
# ポイント更新
# ==========================

def update_point(

    name,

    point

):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        UPDATE users

        SET point=?

        WHERE name=?

        """,

        (

            point,

            name

        )

    )


    conn.commit()

    conn.close()





# ==========================
# ランキング取得
# ==========================

def get_ranking(mode):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT name, point

        FROM users

        WHERE mode=?

        ORDER BY point DESC

        LIMIT 10

        """,

        (

            mode,

        )

    )


    data = cur.fetchall()


    conn.close()


    return data





# ==========================
# ユーザー取得
# ==========================

def get_user(name):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT *

        FROM users

        WHERE name=?

        """,

        (

            name,

        )

    )


    user = cur.fetchone()


    conn.close()


    return user





# ==========================
# 投稿追加
# ==========================

def add_post(
    username,
    message,
    image="",
    breakfast="",
    lunch="",
    dinner=""
):

    conn = sqlite3.connect(DB_NAME)

    cur = conn.cursor()

    cur.execute("""
    INSERT INTO posts(

        username,
        message,
        image,
        breakfast,
        lunch,
        dinner,
        created_at

    )

    VALUES(?,?,?,?,?,?,?)
    """,(

        username,
        message,
        image,
        breakfast,
        lunch,
        dinner,
        datetime.now().strftime("%Y-%m-%d %H:%M")

    ))

    conn.commit()

    conn.close()





# ==========================
# 投稿取得
# ==========================

def get_posts():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT

        id,
        username,
        message,
        image,
        breakfast,
        lunch,
        dinner,
        created_at,
        likes

        FROM posts

        ORDER BY id DESC

        LIMIT 20
    """)

    posts = cur.fetchall()

    conn.close()

    return posts





# ==========================
# いいね追加
# ==========================

def add_like(

    post_id,

    username

):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT *

        FROM likes

        WHERE post_id=?

        AND username=?

        """,

        (

            post_id,

            username

        )

    )



    result = cur.fetchone()



    if result is None:


        cur.execute(
            """
            INSERT INTO likes

            (

            post_id,

            username

            )

            VALUES(?,?)

            """,

            (

                post_id,

                username

            )

        )



        cur.execute(
            """
            UPDATE posts

            SET likes = likes + 1

            WHERE id=?

            """,

            (

                post_id,

            )

        )



    conn.commit()

    conn.close()





# ==========================
# 投稿削除
# ==========================

def delete_post(post_id):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        DELETE FROM posts

        WHERE id=?

        """,

        (

            post_id,

        )

    )


    conn.commit()

    conn.close()





# ==========================
# 健康記録追加
# ==========================

def add_health_record(

    username,

    date,

    weight,

    high,

    low,

    water,

    medicine,

    score

):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        INSERT INTO health_records

        (

        username,

        date,

        weight,

        high,

        low,

        water,

        medicine,

        score

        )

        VALUES(?,?,?,?,?,?,?,?)

        """,

        (

            username,

            date,

            weight,

            high,

            low,

            water,

            int(medicine),

            score

        )

    )


    conn.commit()

    conn.close()





# ==========================
# 健康記録取得
# ==========================

def get_health_records(username):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT

        date,

        weight,

        high,

        low,

        water,

        score


        FROM health_records


        WHERE username=?


        ORDER BY id DESC

        """,

        (

            username,

        )

    )


    records = cur.fetchall()


    conn.close()


    return records


# ==========================
# 推薦献立追加
# ==========================

def add_recommended_menu(
    age_min,
    age_max,
    disease,
    calorie,
    breakfast,
    lunch,
    dinner,
    reason="",
    nutrition="",
    advice=""
):


    conn = connect()

    cur = conn.cursor()


    cur.execute(
        """
        INSERT INTO recommended_menus

        (
        age_min,
        age_max,
        disease,
        calorie,
        breakfast,
        lunch,
        dinner,
        reason,
        nutrition,
        advice
        )

        VALUES(?,?,?,?,?,?,?,?,?,?)

        """,

        (
            age_min,
            age_max,
            disease,
            calorie,
            breakfast,
            lunch,
            dinner,
            reason,
            nutrition,
            advice
        )

    )


    conn.commit()

    conn.close()


def add_favorite_menu(

    username,

    menu_id,

    breakfast,

    lunch,

    dinner,

    calorie,

    reason

):
    conn = connect()
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
    INSERT INTO favorite_menus(

    username,
    menu_id,
    breakfast,
    lunch,
    dinner,
    calorie,
    reason,
    favorite_date

    )

    VALUES(?,?,?,?,?,?,?,?)
    """,
    (
       username,
       menu_id,
       breakfast,
       lunch,
       dinner,
       calorie,
       reason,
       today
    ))

    conn.commit()
    conn.close()

def get_favorite_menus(username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT

    breakfast,

    lunch,

    dinner,

    calorie,

    reason

    FROM favorite_menus

    WHERE username=?
    """,(username,))

    data = cur.fetchall()

    conn.close()

    return data

# ==========================
# 推薦献立取得
# ==========================

def get_recommended_menu(age, disease, calorie):

    menus = []

    with open(
        "data/menus.csv",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            if (
                int(row["min_age"]) <= age <= int(row["max_age"])
                and row["disease"] == disease
            ):

                menus.append(row)

    if not menus:

        return None

    menu = random.choice(menus)

    return (
        menu["breakfast"],
        menu["lunch"],
        menu["dinner"],
        menu["calorie"],
        menu["reason"],
        menu["balance"],
        menu["advice"]
    )

def get_menu_ranking():

    conn=connect()
    cur=conn.cursor()

    cur.execute("""

SELECT

    r.breakfast,
    r.lunch,
    r.dinner,
    COUNT(*) AS total

FROM favorite_menus f

JOIN recommended_menus r

ON f.menu_id = r.id

GROUP BY f.menu_id

ORDER BY total DESC

LIMIT 10

""")

    data=cur.fetchall()

    conn.close()

    return data

def add_favorite_weekly_menu(username, week):

    conn = connect()
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
    INSERT INTO favorite_weekly_menus(

        username,
        save_date,
        monday,
        tuesday,
        wednesday,
        thursday,
        friday,
        saturday,
        sunday

    )

    VALUES(?,?,?,?,?,?,?,?,?)

    """,(

        username,
        today,

        week["月曜日"]["id"],
        week["火曜日"]["id"],
        week["水曜日"]["id"],
        week["木曜日"]["id"],
        week["金曜日"]["id"],
        week["土曜日"]["id"],
        week["日曜日"]["id"]

    ))

    conn.commit()
    conn.close()

def get_favorite_weekly_menus(username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""

    SELECT

    save_date,

    monday,

    tuesday,

    wednesday,

    thursday,

    friday,

    saturday,

    sunday

    FROM favorite_weekly_menus

    WHERE username=?

    ORDER BY id DESC

    """,(username,))

    data = cur.fetchall()

    conn.close()

    return data

# ==========================
# 食材追加
# ==========================

def add_food(
    username,
    food,
    amount,
    expire
):

    conn=connect()
    cur=conn.cursor()


    cur.execute(
    """
    SELECT id
    FROM refrigerator
    WHERE username=?
    AND food=?
    """,
    (
        username,
        food
    ))

    exists=cur.fetchone()


    if exists:

        cur.execute(
        """
        UPDATE refrigerator

        SET amount=?,
        expire=?

        WHERE id=?

        """,
        (
            amount,
            expire,
            exists[0]
        ))

    else:

        cur.execute(
        """
        INSERT INTO refrigerator

        (
        username,
        food,
        amount,
        expire
        )

        VALUES(?,?,?,?)

        """,
        (
            username,
            food,
            amount,
            expire
        ))


    conn.commit()
    conn.close()

# ==========================
# 食材取得
# ==========================

def get_foods(username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""

    SELECT

    id,

    food,

    amount,

    expire

    FROM refrigerator

    WHERE username=?

    ORDER BY expire

    """,(username,))

    data=cur.fetchall()

    conn.close()

    return data

def delete_food(food_id):

    conn=connect()
    cur=conn.cursor()

    cur.execute("""

    DELETE FROM refrigerator

    WHERE id=?

    """,(food_id,))

    conn.commit()
    conn.close()

def get_menu_by_id(menu_id):

    with open("data/menu_data.csv", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if int(row["id"]) == int(menu_id):

                return (
                    row["breakfast"],
                    row["lunch"],
                    row["dinner"],
                    row["calorie"],
                    row["reason"]
                )

    return None

def get_events():

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM events
        ORDER BY updated DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return rows

def get_recommended_events(limit=5):

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM events
        ORDER BY datetime
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()

    conn.close()

    return [dict(r) for r in rows]

def save_event(event):
    # タイトルまたはURLがない空データは保存しない
    if not event.get("title") or not event.get("url"):
        return

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # updated カラムが存在しない場合に自動追加
    try:
        cur.execute("ALTER TABLE events ADD COLUMN updated TEXT")
    except sqlite3.OperationalError:
        pass

    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
    INSERT INTO events(
        title,
        description,
        datetime,
        place,
        target,
        capacity,
        fee,
        teacher,
        application,
        contact,
        url,
        image,
        pdf,
        updated
    )
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(url) DO UPDATE SET
        title=excluded.title,
        description=excluded.description,
        datetime=excluded.datetime,
        place=excluded.place,
        target=excluded.target,
        capacity=excluded.capacity,
        fee=excluded.fee,
        teacher=excluded.teacher,
        application=excluded.application,
        contact=excluded.contact,
        image=excluded.image,
        pdf=excluded.pdf,
        updated=excluded.updated
    """, (
        event.get("title", ""),
        event.get("description", ""),
        event.get("datetime", ""),
        event.get("place", ""),
        event.get("target", ""),
        event.get("capacity", ""),
        event.get("fee", ""),
        event.get("teacher", ""),
        event.get("application", ""),
        event.get("contact", ""),
        event.get("url", ""),
        ",".join(event.get("images", [])),
        ",".join(event.get("pdfs", [])),
        today
    ))

    conn.commit()
    conn.close()


def get_recommended_events(limit=5):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # タイトルが存在するデータのみ取得
    cur.execute("""
        SELECT *
        FROM events
        WHERE title != '' AND title IS NOT NULL
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]

# =========================================================
# Phase 4〜11 ロードマップ機能追加用コード（末尾に追記してください）
# =========================================================

# --- 1. スキーマの更新（既存テーブルに不足カラムを追加＆新規テーブルを作成） ---
def update_schema_for_roadmap():
    """既存のDBに新しいロードマップ用のカラムやテーブルを追加する安全な処理"""
    conn = connect()
    cur = conn.cursor()

    # usersテーブルに新しいカラムを追加（既に存在する場合はスキップ）
    for column, col_type in [("role", "TEXT DEFAULT '高齢者'"), 
                             ("occupation", "TEXT DEFAULT '無職/退職'"), 
                             ("badges", "TEXT DEFAULT ''"),
                             ("user_code", "TEXT")]:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError:
            pass  # 既にある場合はエラーを無視

    # postsテーブルにタグ・評価・ユーザー属性カラムを追加
    for column, col_type in [("user_age", "INTEGER DEFAULT 70"), 
                             ("user_disease", "TEXT DEFAULT '高血圧'"), 
                             ("rating", "INTEGER DEFAULT 5"), 
                             ("tag", "TEXT DEFAULT ''")]:
        try:
            cur.execute(f"ALTER TABLE posts ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError:
            pass

    # recommended_menusテーブルに季節タグを追加
    try:
        cur.execute("ALTER TABLE recommended_menus ADD COLUMN season TEXT DEFAULT '通年'")
    except sqlite3.OperationalError:
        pass

    # 新規テーブルの作成（存在しない場合のみ）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS family_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        sender TEXT,
        log_type TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS family_comments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        commenter TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        date TEXT,
        walk INTEGER DEFAULT 0,
        exercise INTEGER DEFAULT 0,
        medicine INTEGER DEFAULT 0,
        water INTEGER DEFAULT 0,
        dementia_prev INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

# --- 2. ユーザー登録・更新（UPSERT対応） ---
def add_or_update_user(name, role, age, gender, height, weight, occupation, disease, mode):
    conn = connect()
    cur = conn.cursor()
    
    try:
        # テーブルが存在しない場合は作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                role TEXT,
                age INTEGER,
                gender TEXT,
                height REAL,
                weight REAL,
                occupation TEXT,
                disease TEXT,
                mode TEXT,
                user_code TEXT,
                point INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 既存ユーザーの検索
        cur.execute("SELECT id, user_code FROM users WHERE name = ?", (name,))
        row = cur.fetchone()
        
        if row:
            # 既に存在するユーザーの場合は更新 (UPDATE)
            user_id, user_code = row[0], row[1]
            if not user_code or len(str(user_code)) < 4:
                import secrets
                user_code = secrets.token_hex(3).upper()
                
            cur.execute("""
                UPDATE users 
                SET role = ?, age = ?, gender = ?, height = ?, weight = ?, occupation = ?, disease = ?, mode = ?, user_code = ?
                WHERE id = ?
            """, (role, age, gender, height, weight, occupation, disease, mode, user_code, user_id))
        else:
            # 新規ユーザー登録 (INSERT)
            import secrets
            user_code = secrets.token_hex(3).upper()
            
            try:
                cur.execute("""
                    INSERT INTO users (name, role, age, gender, height, weight, occupation, disease, mode, user_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, role, age, gender, height, weight, occupation, disease, mode, user_code))
            except sqlite3.OperationalError:
                # 万が一カラム数が合わない場合のテーブル自動補正フォールバック
                cur.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cur.fetchall()]
                
                required_cols = {
                    "role": "TEXT", "age": "INTEGER", "gender": "TEXT",
                    "height": "REAL", "weight": "REAL", "occupation": "TEXT",
                    "disease": "TEXT", "mode": "TEXT", "user_code": "TEXT"
                }
                for col, col_type in required_cols.items():
                    if col not in columns:
                        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                
                cur.execute("""
                    INSERT INTO users (name, role, age, gender, height, weight, occupation, disease, mode, user_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, role, age, gender, height, weight, occupation, disease, mode, user_code))

        conn.commit()
        return user_code

    except Exception as e:
        conn.rollback()
        print(f"add_or_update_user Error: {e}")
        # フォールバックとしてセキュアコードを返却（画面クラッシュを防止）
        import secrets
        return secrets.token_hex(3).upper()
        
    finally:
        conn.close()

def get_all_seniors():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE role LIKE '%高齢者%' OR mode LIKE '%高齢者%'")
    users = cur.fetchall()
    conn.close()
    return users


# --- 3. Phase 8: 生活支援チェックリスト ---
def get_daily_task(username, date_str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM daily_tasks WHERE username=? AND date=?", (username, date_str))
    row = cur.fetchone()
    conn.close()
    if row:
        # dict形式に変換して返却
        return {"walk": row[3], "exercise": row[4], "medicine": row[5], "water": row[6], "dementia_prev": row[7]}
    return None

def save_daily_task(username, date_str, walk, exercise, medicine, water, dementia_prev):
    conn = connect()
    cur = conn.cursor()
    task = get_daily_task(username, date_str)
    if task:
        cur.execute("""
        UPDATE daily_tasks SET walk=?, exercise=?, medicine=?, water=?, dementia_prev=?
        WHERE username=? AND date=?
        """, (walk, exercise, medicine, water, dementia_prev, username, date_str))
    else:
        cur.execute("""
        INSERT INTO daily_tasks (username, date, walk, exercise, medicine, water, dementia_prev)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (walk, exercise, medicine, water, dementia_prev, username, date_str))
    conn.commit()
    conn.close()


# --- 4. Phase 5: 家族見守り機能 ---
def add_family_log(username, sender, log_type, content):
    conn = connect()
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("INSERT INTO family_logs (username, sender, log_type, content, created_at) VALUES (?,?,?,?,?)",
                (username, sender, log_type, content, today))
    conn.commit()
    conn.close()

def get_family_logs(username):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT username, sender, log_type, content, created_at FROM family_logs WHERE username=? ORDER BY id DESC LIMIT 20", (username,))
    logs = cur.fetchall()
    conn.close()
    return [{"username": r[0], "sender": r[1], "log_type": r[2], "content": r[3], "created_at": r[4]} for r in logs]

def add_family_comment(username, commenter, message):
    conn = connect()
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("INSERT INTO family_comments (username, commenter, message, created_at) VALUES (?,?,?,?)",
                (username, commenter, message, today))
    conn.commit()
    conn.close()

def get_family_comments(username):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT username, commenter, message, created_at FROM family_comments WHERE username=? ORDER BY id DESC LIMIT 10", (username,))
    comments = cur.fetchall()
    conn.close()
    return [{"username": r[0], "commenter": r[1], "message": r[2], "created_at": r[3]} for r in comments]


# --- 5. Phase 4: コミュニティ検索フィルター ---
def get_posts_filtered(age_group=None, disease=None, tag=None):
    conn = connect()
    cur = conn.cursor()
    query = "SELECT id, username, message, image, breakfast, lunch, dinner, created_at, likes, user_age, user_disease, rating, tag FROM posts WHERE 1=1"
    params = []
    
    if age_group and age_group != "全年代":
        try:
            min_a = int(age_group.replace("代", "").replace("以上", ""))
            query += " AND user_age >= ? AND user_age < ?"
            params.extend([min_a, min_a + 10])
        except:
            pass
            
    if disease and disease != "全疾患":
        query += " AND user_disease = ?"
        params.append(disease)
        
    if tag and tag != "全タグ":
        query += " AND tag LIKE ?"
        params.append(f"%{tag}%")
        
    query += " ORDER BY id DESC LIMIT 30"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    posts = []
    for r in rows:
        posts.append({
            "id": r[0], "username": r[1], "message": r[2], "image": r[3],
            "breakfast": r[4], "lunch": r[5], "dinner": r[6], "created_at": r[7],
            "likes": r[8], "user_age": r[9] if r[9] else 70,
            "user_disease": r[10] if r[10] else "高血圧",
            "rating": r[11] if r[11] else 5, "tag": r[12] if r[12] else "一般"
        })
    return posts

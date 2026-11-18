import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")

CSV_FILES = [
    "erea.csv",
]

# حذف قاعدة البيانات القديمة
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)

for csv_file in CSV_FILES:
    csv_path = os.path.join(BASE_DIR, csv_file)

    if not os.path.exists(csv_path):
        print(f"[WARNING] الملف غير موجود: {csv_file}")
        continue

    try:
        # قراءة CSV
        df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")

        # تنظيف أسماء الأعمدة
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # تحويل أعمدة التاريخ
        for col in df.columns:
            if "date" in col or "sent_att" in col:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        table_name = os.path.splitext(csv_file)[0]

        # حفظ البيانات في SQLite
        df.to_sql(table_name, conn, if_exists="replace", index=False)

        print(f"[OK] تم إنشاء جدول: {table_name}")

    except Exception as e:
        print(f"[ERROR] خطأ في الملف {csv_file}: {e}")

conn.close()
print("[INFO] تم إنشاء قاعدة البيانات بنجاح")
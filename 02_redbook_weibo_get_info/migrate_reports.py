from server.database import get_db, BASE_DIR
from sqlite_utils import Database

def migrate_reports():
    db = Database(BASE_DIR / "rednote.db")
    
    if "reports" not in db.table_names():
        print("Creating 'reports' table...")
        db["reports"].create({
            "id": int, # 自增主键
            "title": str,
            "content_json": str, # AggregatedInsight JSON
            "source_post_ids": str, # JSON list of IDs
            "created_at": str
        }, pk="id")
        print("Reports table created.")
    else:
        print("Reports table already exists.")

if __name__ == "__main__":
    migrate_reports()

from sqlite_utils import Database
from pathlib import Path

# 定义数据库路径
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "rednote.db"

def get_db():
    return Database(DB_PATH)

def init_db():
    db = get_db()
    
    # 创建 posts 表 (存储原始数据)
    # 使用 sqlite-utils 的特性，我们其实可以直接 insert，它会自动建表。
    # 但为了明确 Schema 和索引，我们手动配置一下
    if "posts" not in db.table_names():
        db["posts"].create({
            "id": str, # source_id
            "platform": str,
            "title": str,
            "content": str,
            "author_name": str,
            "raw_json": str, # 存储完整的 JSON 字符串以便恢复
            "created_at": str,
            "status": str, # pending, processing, completed, failed
            "error_msg": str
        }, pk="id")
        # 创建全文搜索索引
        db["posts"].enable_fts(["title", "content"])
    
    # 创建 insights 表 (存储分析结果)
    if "insights" not in db.table_names():
        db["insights"].create({
            "id": int, # 自增主键
            "post_id": str,
            "summary_text": str,
            "analysis_json": str,
            "expansion_json": str,
            "full_json": str, # 存储完整的 JSON 字符串方便前端渲染
            "created_at": str,
            "version": int,
            "is_latest": int
        }, pk="id", foreign_keys=[("post_id", "posts", "id")])
    else:
        insights_table = db["insights"]
        insights_columns = [column.name for column in insights_table.columns]
        if "version" not in insights_columns:
            insights_table.add_column("version", int)
        if "is_latest" not in insights_columns:
            insights_table.add_column("is_latest", int)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_insights_post_latest ON insights(post_id, is_latest)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_insights_post_created ON insights(post_id, created_at DESC)")

    # 创建 reports 表 (存储整合分析报告)
    if "reports" not in db.table_names():
        db["reports"].create({
            "id": int, # 自增主键
            "title": str,
            "content_json": str, # AggregatedInsight JSON
            "source_post_ids": str, # JSON list of IDs
            "created_at": str
        }, pk="id")

    if "aggregation_jobs" not in db.table_names():
        db["aggregation_jobs"].create({
            "id": int,
            "status": str,
            "phase": str,
            "progress": int,
            "message": str,
            "source_post_ids": str,
            "report_id": int,
            "error_msg": str,
            "created_at": str,
            "updated_at": str
        }, pk="id")

    db.execute("CREATE INDEX IF NOT EXISTS idx_aggregation_jobs_created ON aggregation_jobs(created_at DESC)")

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")

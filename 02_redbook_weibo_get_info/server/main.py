from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import json
from datetime import datetime

from .schemas import RawPost, ReportRequest
from .database import get_db, init_db
from .llm_service import analyze_post, analyze_multiple_posts
from .downloader import download_images_for_posts
from .ocr_service import ocr_service  # Import OCR service

app = FastAPI(title="RedNote Insight Collector")

# 挂载静态文件和模板
# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="server/static"), name="static")
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# 允许跨域，方便浏览器插件调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境应该限制为具体域或插件 ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时初始化数据库
@app.on_event("startup")
def on_startup():
    init_db()

def get_next_insight_version(db, post_id: str) -> int:
    row = db.execute(
        "SELECT COALESCE(MAX(version), 0) FROM insights WHERE post_id = ?",
        [post_id]
    ).fetchone()
    current = row[0] if row and row[0] is not None else 0
    return int(current) + 1

def update_aggregation_job(db, job_id: int, status: str = None, phase: str = None, progress: int = None, message: str = None, report_id: int = None, error_msg: str = None):
    payload = {"updated_at": datetime.now().isoformat()}
    if status is not None:
        payload["status"] = status
    if phase is not None:
        payload["phase"] = phase
    if progress is not None:
        payload["progress"] = progress
    if message is not None:
        payload["message"] = message
    if report_id is not None:
        payload["report_id"] = report_id
    if error_msg is not None:
        payload["error_msg"] = error_msg
    db["aggregation_jobs"].update(job_id, payload, alter=True)

def process_batch_analysis(limit: int):
    """
    后台任务：批量处理未分析的帖子
    """
    db = get_db()
    # 查找未分析的帖子 (在 posts 中但不在 insights 中)
    # 使用 SQL 子查询
    # 排除掉状态为 processing 的，避免重复处理 (虽然目前是单线程 worker，但为了逻辑严谨)
    # 也可以重试 failed 的任务
    query = f"""
    SELECT * FROM posts 
    WHERE id NOT IN (SELECT post_id FROM insights) 
    AND (status IS NULL OR status != 'processing')
    ORDER BY created_at DESC 
    LIMIT {limit}
    """
    pending_posts = list(db.query(query))
    
    if not pending_posts:
        print("No pending posts found.")
        return

    print(f"Starting batch analysis for {len(pending_posts)} posts...")
    
    # 先将所有选中的任务标记为 processing
    for row in pending_posts:
        db["posts"].update(row["id"], {"status": "processing", "error_msg": None}, alter=True)

    for row in pending_posts:
        try:
            # 还原 RawPost 对象
            raw_data = json.loads(row["raw_json"])
            post = RawPost(**raw_data)
            
            # 调用 LLM
            insight = analyze_post(post)
            
            if insight:
                next_version = get_next_insight_version(db, post.source_id)
                db.execute("UPDATE insights SET is_latest = 0 WHERE post_id = ?", [post.source_id])
                # 存入 insights 表
                db["insights"].insert({
                    "post_id": post.source_id,
                    "summary_text": insight.summary.one_liner if insight.summary else "",
                    "analysis_json": insight.analysis.model_dump_json() if insight.analysis else None,
                    "expansion_json": insight.creative_expansion.model_dump_json() if insight.creative_expansion else None,
                    "full_json": insight.model_dump_json(), # 存储完整结果方便前端渲染
                    "created_at": datetime.now().isoformat(),
                    "version": next_version,
                    "is_latest": 1
                }, alter=True)
                # 更新状态为 completed
                db["posts"].update(post.source_id, {"status": "completed"})
                print(f"Processed post: {post.source_id}")
            else:
                # LLM 返回 None (可能是 API 错误)
                db["posts"].update(post.source_id, {"status": "failed", "error_msg": "LLM returned no result"})
                print(f"Failed to analyze post: {post.source_id}")
                
        except Exception as e:
            print(f"Error processing post {row['id']}: {e}")
            db["posts"].update(row["id"], {"status": "failed", "error_msg": str(e)})

@app.post("/api/analyze/batch")
async def trigger_batch_analysis(background_tasks: BackgroundTasks, limit: int = 5):
    """
    触发批量分析任务 (异步)
    """
    background_tasks.add_task(process_batch_analysis, limit)
    return {"status": "queued", "message": f"Batch analysis started for up to {limit} posts"}

from pydantic import BaseModel

class DeleteRequest(BaseModel):
    ids: List[str]

@app.post("/api/posts/delete")
def delete_posts(request: DeleteRequest):
    """
    批量删除帖子及其对应的 insights
    """
    db = get_db()
    ids = request.ids
    
    if not ids:
        return {"status": "success", "deleted": 0}
        
    placeholders = ",".join(["?"] * len(ids))
    
    try:
        # 删除 insights
        db.execute(f"DELETE FROM insights WHERE post_id IN ({placeholders})", ids)
        
        # 删除 posts
        db.execute(f"DELETE FROM posts WHERE id IN ({placeholders})", ids)
        
        # Ensure changes are committed (sqlite-utils usually does this, but being explicit helps)
        try:
            db.conn.commit()
        except:
            pass
            
        return {"status": "success", "deleted": len(ids)}
    except Exception as e:
        print(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

import traceback

def process_single_analysis(post_id: str):
    """
    后台任务：分析单个帖子
    """
    db = get_db()
    try:
        row = db["posts"].get(post_id)
        # 更新状态为 processing
        db["posts"].update(post_id, {"status": "processing", "error_msg": None}, alter=True)
        
        # 还原 RawPost 对象
        raw_data = json.loads(row["raw_json"])
        post = RawPost(**raw_data)
        
        # 调用 LLM
        insight = analyze_post(post)
        
        if insight:
            next_version = get_next_insight_version(db, post.source_id)
            db.execute("UPDATE insights SET is_latest = 0 WHERE post_id = ?", [post.source_id])
            # 存入 insights 表
            db["insights"].insert({
                "post_id": post.source_id,
                "summary_text": insight.summary.one_liner if insight.summary else "",
                "analysis_json": insight.analysis.model_dump_json() if insight.analysis else None,
                "expansion_json": insight.creative_expansion.model_dump_json() if insight.creative_expansion else None,
                "full_json": insight.model_dump_json(),
                "created_at": datetime.now().isoformat(),
                "version": next_version,
                "is_latest": 1
            }, alter=True)
            
            # 更新状态为 completed
            db["posts"].update(post.source_id, {"status": "completed"})
            print(f"Processed single post: {post.source_id}")
        else:
            db["posts"].update(post.source_id, {"status": "failed", "error_msg": "LLM returned no result"})
            print(f"Failed to analyze post: {post.source_id}")
            
    except Exception as e:
        print(f"Error processing post {post_id}: {e}")
        traceback.print_exc()
        try:
            db["posts"].update(post_id, {"status": "failed", "error_msg": str(e)})
        except:
            pass

@app.post("/api/analyze/{post_id}")
async def trigger_single_analysis(post_id: str, background_tasks: BackgroundTasks):
    """
    触发单篇分析任务 (异步)
    """
    background_tasks.add_task(process_single_analysis, post_id)
    return {"status": "queued", "message": f"Analysis started for post {post_id}"}

@app.get("/")
def read_root():
    return FileResponse("server/templates/index.html")

@app.get("/api/posts")
def list_posts(limit: int = 50, offset: int = 0):
    """
    获取已采集的帖子列表 (聚合了 insight 信息以便前端渲染)
    """
    db = get_db()
    
    # 获取帖子
    posts_rows = list(db.query(f"SELECT * FROM posts ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"))
    
    # 将 sqlite3.Row 转换为 dict
    posts = [dict(row) for row in posts_rows]
    
    # 获取对应的 insights
    post_ids = [p['id'] for p in posts]
    if not post_ids:
        return []
        
    placeholders = ",".join(["?"] * len(post_ids))
    insights = list(db.query(
        f"""
        SELECT * FROM insights
        WHERE id IN (
            SELECT MAX(id) FROM insights WHERE post_id IN ({placeholders}) GROUP BY post_id
        )
        """,
        post_ids
    ))
    
    # 建立映射
    insights_map = {i['post_id']: json.loads(i['full_json']) for i in insights}
    
    # 合并
    result = []
    for p in posts:
        # p 已经是 dict 了
        p['insight'] = insights_map.get(p['id'])
        # 默认状态处理
        if 'status' not in p or p['status'] is None:
            p['status'] = 'completed' if p['insight'] else 'pending'
        result.append(p)
        
    return result

@app.post("/api/collect")
async def collect_post(post: RawPost, background_tasks: BackgroundTasks):
    """
    接收浏览器插件发送的帖子数据
    """
    try:
        db = get_db()
        # 检查是否已存在
        if db["posts"].get(post.source_id):
            return {"status": "skipped", "message": "Post already exists"}
    except:
        pass # 如果不存在会报错，忽略之

    # 存入数据库
    # 这里我们把复杂结构转为 JSON 存入 raw_json 字段
    db = get_db()
    db["posts"].insert({
        "id": post.source_id,
        "platform": post.platform,
        "title": post.title,
        "content": post.content,
        "author_name": post.author.name,
        "raw_json": post.model_dump_json(),
        "created_at": datetime.now().isoformat(),
        "status": "pending" # 初始状态
    }, pk="id", replace=True, alter=True) # alter=True 自动增加新字段

    # Add background tasks:
    # 1. OCR (High Priority, before analysis)
    # 2. Analysis (triggered after OCR or independently)
    # background_tasks.add_task(process_post_pipeline, post.source_id)
    
    return {"status": "success", "id": post.source_id}

def process_post_pipeline(post_id: str):
    """
    Complete pipeline: OCR -> Analysis
    """
    db = get_db()
    try:
        print(f"Starting pipeline for {post_id}...")
        row = db["posts"].get(post_id)
        if not row:
            return

        raw_data = json.loads(row["raw_json"])
        post = RawPost(**raw_data)
        
        # Step 1: OCR
        # Only run if no ocr_content yet and images exist
        if not post.ocr_content and post.media.images:
            print(f"Running OCR for {post_id}...")
            ocr_text = ocr_service.process_images(post.media.images)
            if ocr_text:
                post.ocr_content = ocr_text
                # Update DB
                raw_data['ocr_content'] = ocr_text
                db["posts"].update(post_id, {
                    "raw_json": json.dumps(raw_data, ensure_ascii=False, default=str)
                })
                print(f"OCR completed for {post_id}")
            else:
                print(f"OCR returned empty for {post_id}")
        
        # Step 2: Analysis
        # Call the existing analysis logic (which now reads ocr_content)
        process_single_analysis(post_id)
        
    except Exception as e:
        print(f"Pipeline failed for {post_id}: {e}")
        traceback.print_exc()

@app.get("/api/posts/{post_id}")
def get_post(post_id: str):
    db = get_db()
    try:
        post = db["posts"].get(post_id)
        return post
    except:
        raise HTTPException(status_code=404, detail="Post not found")

# --- Aggregation & Download Endpoints ---

def process_aggregation(job_id: int, post_ids: List[str]):
    """
    后台任务：整合分析
    """
    try:
        db = get_db()
        update_aggregation_job(db, job_id, status="processing", phase="loading_posts", progress=10, message="正在读取并整理选中笔记…")

        placeholders = ",".join(["?"] * len(post_ids))
        rows = list(db.query(f"SELECT * FROM posts WHERE id IN ({placeholders})", post_ids))
        
        posts = []
        for row in rows:
            try:
                posts.append(RawPost(**json.loads(row["raw_json"])))
            except:
                pass
                
        if not posts:
            raise ValueError("未找到可用于聚合的帖子内容")

        update_aggregation_job(db, job_id, phase="llm_analyzing", progress=55, message=f"正在整合 {len(posts)} 篇笔记，提炼学习重点…")
        print(f"Aggregating {len(posts)} posts...")
        aggregated_insight = analyze_multiple_posts(posts)

        update_aggregation_job(db, job_id, phase="saving_report", progress=90, message="正在写入学习报告…")
        title_seed = ""
        if aggregated_insight.summary and aggregated_insight.summary.one_liner:
            title_seed = aggregated_insight.summary.one_liner
        elif aggregated_insight.topic_overview:
            title_seed = aggregated_insight.topic_overview
        else:
            title_seed = "跨帖学习总结"
        topic = title_seed[:24] + ("..." if len(title_seed) > 24 else "")
        title = f"整合报告：{topic}"

        db["reports"].insert({
            "title": title,
            "content_json": aggregated_insight.model_dump_json(),
            "source_post_ids": json.dumps(post_ids),
            "created_at": datetime.now().isoformat()
        }, alter=True)
        report_row = db.execute("SELECT last_insert_rowid()").fetchone()
        report_id = int(report_row[0]) if report_row else None
        update_aggregation_job(db, job_id, status="completed", phase="done", progress=100, message="学习报告已生成", report_id=report_id)
        print(f"Generated report: {title}")
    except Exception as e:
        try:
            db = get_db()
            update_aggregation_job(db, job_id, status="failed", phase="failed", progress=100, message="聚合分析失败", error_msg=str(e))
        except:
            pass
        print(f"Aggregation failed: {e}")

def process_image_download(post_ids: List[str]):
    """
    后台任务：下载图片
    """
    db = get_db()
    placeholders = ",".join(["?"] * len(post_ids))
    rows = list(db.query(f"SELECT * FROM posts WHERE id IN ({placeholders})", post_ids))
    
    posts = []
    for row in rows:
        try:
            posts.append(RawPost(**json.loads(row["raw_json"])))
        except:
            pass
            
    if not posts:
        return
        
    print(f"Downloading images for {len(posts)} posts...")
    results = download_images_for_posts(posts)
    for res in results:
        print(res)

@app.post("/api/aggregate")
async def trigger_aggregation(request: ReportRequest, background_tasks: BackgroundTasks):
    if len(request.post_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 posts are required")
    db = get_db()
    now = datetime.now().isoformat()
    db["aggregation_jobs"].insert({
        "status": "queued",
        "phase": "queued",
        "progress": 0,
        "message": f"已加入队列，待整合 {len(request.post_ids)} 篇笔记",
        "source_post_ids": json.dumps(request.post_ids),
        "report_id": None,
        "error_msg": None,
        "created_at": now,
        "updated_at": now
    }, alter=True)
    row = db.execute("SELECT last_insert_rowid()").fetchone()
    job_id = int(row[0]) if row else None
    background_tasks.add_task(process_aggregation, job_id, request.post_ids)
    return {"status": "queued", "message": "Aggregation started", "job_id": job_id}

@app.get("/api/aggregate/jobs/latest")
def get_latest_aggregation_job():
    db = get_db()
    row = db.execute("SELECT * FROM aggregation_jobs ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return None
    return dict(row)

@app.get("/api/aggregate/jobs/{job_id}")
def get_aggregation_job(job_id: int):
    db = get_db()
    try:
        row = db["aggregation_jobs"].get(job_id)
        return row
    except:
        raise HTTPException(status_code=404, detail="Aggregation job not found")

@app.get("/api/reports")
def list_reports():
    db = get_db()
    if "reports" not in db.table_names():
        return []
    return list(db.query("SELECT * FROM reports ORDER BY created_at DESC"))

@app.delete("/api/reports/{report_id}")
def delete_report(report_id: int):
    db = get_db()
    db["reports"].delete(report_id)
    return {"status": "success"}

@app.post("/api/download/images")
async def trigger_download_images(request: ReportRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_image_download, request.post_ids)
    return {"status": "queued", "message": "Download started"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=True)

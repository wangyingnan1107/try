from server.database import get_db
import json

def check_errors():
    db = get_db()
    # 查询状态为 failed 的帖子
    failed_posts = list(db.query("SELECT id, title, error_msg FROM posts WHERE status = 'failed' ORDER BY created_at DESC LIMIT 5"))
    
    if not failed_posts:
        print("No failed posts found.")
        return

    print(f"Found {len(failed_posts)} failed posts:")
    for post in failed_posts:
        print(f"ID: {post['id']}")
        print(f"Title: {post['title']}")
        print(f"Error: {post['error_msg']}")
        print("-" * 50)

if __name__ == "__main__":
    check_errors()

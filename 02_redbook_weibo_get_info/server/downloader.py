import os
import requests
from pathlib import Path
from typing import List
from .schemas import RawPost

# Base download directory
BASE_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def sanitize_filename(name: str) -> str:
    # Replace invalid chars for windows filename
    return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()

def download_images_for_posts(posts: List[RawPost]) -> List[str]:
    """
    Downloads images for a list of posts.
    Returns a list of messages describing what happened.
    """
    results = []
    ensure_dir(DOWNLOAD_DIR)
    
    for post in posts:
        safe_title = sanitize_filename(post.title)
        # Fallback to ID if title is empty or too short
        if len(safe_title) < 2:
            safe_title = post.source_id
            
        post_dir = DOWNLOAD_DIR / safe_title
        ensure_dir(post_dir)
        
        if not post.media.images:
             results.append(f"No images found for: {post.title}")
             continue

        for idx, img_url in enumerate(post.media.images):
            try:
                # Basic check for URL validity
                if not img_url.startswith("http"):
                    continue
                    
                # Attempt to get higher quality if possible (heuristic)
                # XHS often has patterns, but for now we download what we have.
                # Common headers to avoid basic anti-bot (though CDN usually open)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                response = requests.get(img_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    # Guess extension
                    ext = "jpg"
                    if "png" in img_url: ext = "png"
                    if "webp" in img_url: ext = "webp"
                    
                    file_path = post_dir / f"{idx + 1}.{ext}"
                    with open(file_path, "wb") as f:
                        f.write(response.content)
            except Exception as e:
                print(f"Failed to download {img_url}: {e}")
        
        results.append(f"Downloaded images for: {post.title}")
        
    return results

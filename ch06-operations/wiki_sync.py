"""
第六章：Wiki 增量同步脚本
将 Obsidian Wiki 目录中新增/修改的文件同步到 Milvus 向量库
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

WIKI_PATH = os.getenv("WIKI_PATH", "/data/wiki")
SYNC_STATE_FILE = os.getenv("SYNC_STATE_FILE", "/tmp/.last_sync")
KNOWLEDGE_API = os.getenv("KNOWLEDGE_API", "http://localhost:8000")


def get_modified_files(since: datetime) -> list[Path]:
    result = []
    for f in Path(WIKI_PATH).rglob("*.md"):
        # 跳过 Mac 隐藏文件（见第五章坑7）
        if f.name.startswith("._"):
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime > since:
            result.append(f)
    return result


def extract_title(content: str) -> str:
    """从 Markdown frontmatter 或第一个 # 标题提取标题"""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip().strip('"')
        if line.startswith("# "):
            return line[2:].strip()
    return "未命名"


def sync_file(path: Path):
    import urllib.request
    content = path.read_text(encoding="utf-8")
    title = extract_title(content)
    doc_id = str(path.relative_to(WIKI_PATH))

    payload = json.dumps({
        "id": doc_id,
        "title": title,
        "content": content,
        "category": path.parent.name,
    }).encode()

    req = urllib.request.Request(
        f"{KNOWLEDGE_API}/api/knowledge/upsert",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                print(f"✅ 同步完成: {path.name}")
            else:
                print(f"❌ 同步失败: {path.name} (HTTP {resp.status})")
    except Exception as e:
        print(f"❌ 同步失败: {path.name} - {e}")


def main():
    full = "--full" in sys.argv

    if full or not Path(SYNC_STATE_FILE).exists():
        since = datetime.now() - timedelta(days=3650)
        print("执行全量同步...")
    else:
        since = datetime.fromisoformat(Path(SYNC_STATE_FILE).read_text().strip())
        print(f"增量同步，上次同步时间: {since}")

    modified = get_modified_files(since)
    print(f"发现 {len(modified)} 个文件需要同步")

    for f in modified:
        sync_file(f)

    Path(SYNC_STATE_FILE).write_text(datetime.now().isoformat())
    print("同步完成")


if __name__ == "__main__":
    main()

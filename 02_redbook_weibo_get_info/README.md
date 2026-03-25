# RedNote Insight Collector（小红书学习助理采集器）

## 1. 项目简介

这是一个“本地优先”的小红书内容采集与学习辅助系统，核心目标是：

- 把碎片内容沉淀为结构化知识
- 从帖子中提取可执行的方法与任务
- 生成单篇学习卡片与多篇学习路线图

当前版本已从“话题/热度分析”转向“学习助理模式”，重点输出知识提炼、步骤化方法、练习任务与证据片段。

---

## 2. 整体架构

项目采用 Capture → Transform → Load 流程：

1. **Capture（采集）**  
   浏览器脚本在小红书页面提取标题、正文、图片、评论、互动数据，提交到本地 API。

2. **Transform（分析）**  
   FastAPI 后端调用 LLM 进行：
   - 单篇学习提炼（学习助理结构）
   - 多篇聚合学习报告（学习路线图）

3. **Load（展示）**  
   Web 页面展示笔记列表、单篇结果、聚合报告，并支持批量操作。

---

## 3. 数据保存在哪里

### 3.1 数据库位置

- 主数据库文件：`rednote.db`
- 路径来源：`server/database.py` 中 `DB_PATH = BASE_DIR / "rednote.db"`

### 3.2 主要数据表

1. **posts**（原始帖子）
   - `id`（source_id）
   - `title/content/author_name`
   - `raw_json`（完整原始结构）
   - `status`（pending/processing/completed/failed）
   - `error_msg`

2. **insights**（单篇分析结果）
   - `post_id`
   - `full_json`（完整分析 JSON）
   - `summary_text`
   - `version`、`is_latest`（支持重复分析版本化）

3. **reports**（聚合分析报告）
   - `title`
   - `content_json`（聚合报告 JSON）
   - `source_post_ids`

### 3.3 图片下载目录

- 批量下载图片后存储在 `downloads/`，并通过后端静态路由 `/downloads` 暴露。

---

## 4. 重点文件说明（建议先读）

### 4.1 采集端

- `plugin/rednote_collector.user.js`
  - 注入“✨ 采集灵感”按钮
  - 解析页面 DOM 提取帖子数据
  - 调用 `POST /api/collect`

### 4.2 后端入口与任务编排

- `server/main.py`
  - API 路由入口
  - 后台任务调度（单篇分析、批量分析、聚合分析、下载图片）
  - 数据入库与状态流转

### 4.3 分析核心

- `server/llm_service.py`
  - 单篇分析 `analyze_post`
  - 多篇聚合 `analyze_multiple_posts`
  - 学习助理 Prompt
  - Moonshot 温度兼容处理

- `server/structured_extractor.py`
  - 结构化抽取输入（标题/正文/OCR/评论）
  - 复杂格式保留（代码块、话题、@、链接、emoji）
  - 证据片段抽取与诊断指标

### 4.4 数据模型与存储

- `server/schemas.py`：Pydantic 输入输出模型（含学习助理字段）
- `server/database.py`：SQLite 初始化、表结构、索引

### 4.5 前端页面

- `server/templates/index.html`
  - 笔记列表与筛选
  - 批量勾选工具条（全选、反选、快选）
  - 单篇学习助理展示
  - 聚合学习路线图展示

---

## 5. 怎么触发（最常用流程）

## 5.1 采集帖子

1. 打开小红书帖子页  
2. 点击页面右下角“✨ 采集灵感”  
3. 插件请求 `POST /api/collect`，帖子进入 `posts` 表

## 5.2 触发单篇分析

- 在页面右侧详情点击“✨ AI 分析 / 🔁 重新分析”  
- 或直接调用 `POST /api/analyze/{post_id}`
- 分析完成后写入 `insights`，并将该帖状态置为 `completed`

## 5.3 触发批量分析

- 前端点击“🚀 批量分析”  
- 后端执行 `POST /api/analyze/batch?limit=5`

## 5.4 触发聚合分析（多篇学习报告）

1. 左侧勾选至少 2 篇帖子  
2. 点击“🧩 聚合分析”  
3. 后端执行 `POST /api/aggregate`，结果写入 `reports`

## 5.5 批量下载图片

- 勾选帖子后点击“📥 下载图片”  
- 触发 `POST /api/download/images`

---

## 6. API 一览（核心）

- `POST /api/collect`：采集入库  
- `POST /api/analyze/{post_id}`：单篇分析（支持重复分析）  
- `POST /api/analyze/batch?limit=5`：批量分析  
- `GET /api/posts`：获取帖子+最新分析结果  
- `POST /api/aggregate`：聚合学习报告  
- `GET /api/reports`：查询报告  
- `DELETE /api/reports/{report_id}`：删除报告  
- `POST /api/posts/delete`：删除帖子及其分析  
- `POST /api/download/images`：批量下载图片

---

## 7. 安装与运行

### 7.1 依赖安装

```bash
pip install -r server/requirements.txt
```

### 7.2 环境变量

在项目根目录配置 `.env`（参考 `.env.example`）：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

### 7.3 启动后端

```bash
uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

- `http://localhost:8000`

---

## 8. 常见问题

### 8.1 为什么终端看到“Attempting Vision analysis”？

这是正常日志，表示单篇分析在尝试图文联合理解，不是报错。

### 8.2 为什么提示温度参数 400 错误？

若使用 Moonshot 某些模型，只允许固定温度。项目已在 `llm_service.py` 做兼容映射。

### 8.3 刷新后右侧详情空白

近期已修复空字段渲染与默认选中逻辑。若仍遇到，先点击左侧任一帖子再看控制台报错。

---

## 9. 当前测试与验证

项目包含 `tests/` 自动化测试，覆盖：

- 结构化抽取
- 聚合证据保留
- 重分析流程
- 学习助理输出字段

执行命令：

```bash
python -m unittest discover -s tests -v
```

---

## 10. 安全提醒

- 请不要把真实 API Key 提交到代码仓库。
- 若密钥曾出现在明文文件中，请立即轮换并改用环境变量注入。

# 数据结构定义 (Data Schema)

为了实现“灵感库”的目标，我们需要定义两层数据结构：
1.  **RawPost (原始素材)**: 从浏览器端“原样”抓取的数据。
2.  **InsightBrief (灵感简报)**: 经过 LLM 清洗、分析、扩展后的结构化数据。

## 1. RawPost (输入层 - 浏览器插件采集)

```json
{
  "source_id": "String, 平台唯一ID (如 64e5f...)",
  "platform": "String, 固定为 'xiaohongshu'",
  "url": "String, 原始链接",
  "title": "String, 笔记标题",
  "content": "String, 笔记正文 (包含 emoji)",
  "author": {
    "name": "String, 作者昵称",
    "uid": "String, 作者ID"
  },
  "media": {
    "images": ["String, 图片URL列表"],
    "video_cover": "String, 视频封面 (如果是视频笔记)"
  },
  "stats": {
    "likes": "Number, 点赞数",
    "collects": "Number, 收藏数",
    "comments_count": "Number, 评论数"
  },
  "top_comments": [
    "String, 抓取前3-5条高赞评论 (用于分析用户痛点/槽点)"
  ],
  "tags": ["String, 原始标签"],
  "captured_at": "ISO8601 Timestamp, 采集时间"
}
```

## 2. InsightBrief (输出层 - AI 分析简报)

这是网页端展示的核心对象，旨在辅助“二创”和“灵感激发”。

```json
{
  "meta": {
    "original_id": "String, 关联 RawPost",
    "processed_at": "ISO8601 Timestamp"
  },
  
  // 1. 核心提炼 (快速获取信息)
  "summary": {
    "one_liner": "String, 一句话总结核心价值",
    "keywords": ["String, 提取的3-5个核心关键词"]
  },

  // 2. 爆款拆解 (分析为什么火)
  "analysis": {
    "hook_point": "String, 吸引注意力的钩子是什么？(如：标题党、反差图、痛点直击)",
    "emotional_value": "String, 提供了什么情绪价值？(如：焦虑缓解、爽感、共鸣)",
    "target_audience": "String, 目标受众是谁？"
  },

  // 3. 内容二创 (扩展灵感)
  "creative_expansion": {
    "viewpoints": ["String, 提取出的独特观点/金句"],
    "counter_intuition": "String, 有无反直觉/打破认知的信息？",
    "writing_angle": "String, 建议的改写/切入角度 (如：把'教程'改为'避坑指南')"
  },

  // 4. 素材复用
  "assets": {
    "quotes": ["String, 值得引用的原句"],
    "image_prompts": ["String, 根据内容生成的 AI 绘图提示词 (可选)"]
  }
}
```

## 数据库设计 (SQLite)

### Table: `posts`
存储原始数据。
- id (PK)
- raw_json (JSON Column)
- created_at

### Table: `insights`
存储分析结果。
- id (PK)
- post_id (FK -> posts.id)
- summary_text
- analysis_json (JSON Column)
- expansion_json (JSON Column)
- created_at

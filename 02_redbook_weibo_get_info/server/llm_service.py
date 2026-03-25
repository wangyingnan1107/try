from typing import List
import json
import requests
import base64
from .schemas import RawPost, InsightBrief, AggregatedInsight, Summary, AiAnalysis
from .config import settings
from .structured_extractor import extract_structured_post, build_weighted_context

# client = OpenAI(
#     api_key=settings.openai_api_key,
#     base_url=settings.openai_base_url
# )

def encode_image_from_url(url: str) -> str:
    """
    Downloads an image from a URL and converts it to a base64 string.
    Returns None if download fails.
    """
    try:
        # Xiaohongshu requires headers to avoid 403 Forbidden
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"Error downloading/encoding image {url}: {e}")
        return None

AI_SYSTEM_PROMPT = """
你是一位“学习助理”，目标是帮助用户从帖子中高效学习并落地实践，而不是做热度点评。

执行原则：
1) 只输出可学习、可执行、可验证的信息。
2) 必须引用原文证据（短句）支撑关键结论。
3) 禁止输出“标题吸引力/情绪价值/受众画像”这类运营分析。
4) 任务与建议要具体到可在24小时内执行。

请严格只输出 JSON，不要Markdown代码块。
JSON结构：
{
  "summary": {
    "one_liner": "一句话学习结论",
    "keywords": ["关键词1","关键词2","关键词3"]
  },
  "learning_insight": {
    "core_takeaways": ["3-7条核心收获"],
    "key_concepts": [
      {"term":"术语","explanation":"解释","application":"适用场景"}
    ],
    "method_playbook": ["按步骤描述可执行方法"],
    "evidence_snippets": ["必须来自原文的证据片段"],
    "pitfalls": ["常见误区或失败点"],
    "prerequisites": ["前置知识或工具"],
    "practice_tasks": [
      {"task":"练习任务","difficulty":"入门|中级|进阶","expected_outcome":"完成标准"}
    ],
    "reflection_questions": ["复盘问题"],
    "next_actions_24h": ["24小时内可执行动作"]
  }
}
"""

SYSTEM_PROMPT = """
你是一位“学习教练型助理”。请从帖子中提取高价值知识，并转化为可执行学习方案。

输出要求：
1) 先提炼知识，再给方法，再给任务。
2) 每个关键结论都尽量给原文证据短句。
3) 内容面向学习与实践，不做传播热度分析。
4) 建议必须可执行、可验证、可复盘。

请严格只输出 JSON，不要Markdown代码块。
JSON结构：
{
  "summary": {
    "one_liner": "一句话学习结论",
    "keywords": ["关键词1","关键词2","关键词3"]
  },
  "learning_insight": {
    "core_takeaways": ["3-7条核心收获"],
    "key_concepts": [
      {"term":"术语","explanation":"解释","application":"适用场景"}
    ],
    "method_playbook": ["按步骤描述可执行方法"],
    "evidence_snippets": ["必须来自原文的证据片段"],
    "pitfalls": ["常见误区或失败点"],
    "prerequisites": ["前置知识或工具"],
    "practice_tasks": [
      {"task":"练习任务","difficulty":"入门|中级|进阶","expected_outcome":"完成标准"}
    ],
    "reflection_questions": ["复盘问题"],
    "next_actions_24h": ["24小时内可执行动作"]
  }
}
"""

AGGREGATION_SYSTEM_PROMPT = """
你是一位“跨帖子学习助理”，任务是把多篇帖子进行学习向整合，输出与单篇分析一致的学习结构。

执行原则：
1) 先归纳内容，再形成方法，再给出练习任务。
2) 聚焦学习价值与落地执行，不做热度/传播分析。
3) 关键结论必须提供原文证据短句。
4) 输出应能帮助用户快速理解杂乱内容并形成学习路线。

请只输出 JSON，不要Markdown代码块。
JSON结构：
{
  "summary": {
    "one_liner": "跨帖一句话学习结论",
    "keywords": ["关键词1","关键词2","关键词3"]
  },
  "learning_insight": {
    "core_takeaways": ["3-10条核心收获"],
    "key_concepts": [
      {"term":"术语","explanation":"解释","application":"适用场景"}
    ],
    "method_playbook": ["步骤化可执行方法"],
    "evidence_snippets": ["来自原文的证据短句"],
    "pitfalls": ["常见误区或失败点"],
    "prerequisites": ["前置知识或工具"],
    "practice_tasks": [
      {"task":"练习任务","difficulty":"入门|中级|进阶","expected_outcome":"完成标准"}
    ],
    "reflection_questions": ["复盘问题"],
    "next_actions_24h": ["24小时内可执行动作"]
  },
  "cross_post_synthesis": {
    "consensus": ["跨帖共识"],
    "conflicts": ["跨帖分歧与适用条件"],
    "knowledge_map": ["概念关系要点"]
  }
}
"""

import re
import ast

def get_compatible_temperature(default_value: float) -> float:
    base_url = (settings.openai_base_url or "").lower()
    if "moonshot.cn" in base_url:
        return 1
    return default_value

def clean_json_response(response_text: str) -> str:
    """
    Cleans the LLM response to ensure it's valid JSON.
    Removes Markdown code blocks and whitespace.
    Tries to extract the JSON object from the text.
    """
    # Remove markdown code blocks
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        response_text = match.group(1)
    else:
        pattern_simple = r"```\s*(.*?)\s*```"
        match_simple = re.search(pattern_simple, response_text, re.DOTALL)
        if match_simple:
            response_text = match_simple.group(1)
            
    # Locate the first '{' and last '}'
    start = response_text.find('{')
    end = response_text.rfind('}')
    
    if start != -1 and end != -1:
        return response_text[start:end+1]
        
    return response_text.strip()


def ensure_string(value) -> str:
    """Helper to convert structured data to string for Pydantic compatibility"""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        try:
            if isinstance(value, dict):
                items = []
                for k, v in value.items():
                    if isinstance(v, (list, tuple)):
                        val_str = ", ".join(map(str, v))
                    else:
                        val_str = str(v)
                    items.append(f"- {k}: {val_str}")
                return "\n".join(items)
            return json.dumps(value, ensure_ascii=False, indent=2)
        except:
            return str(value)
    return str(value)

def ensure_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]

def analyze_post(post: RawPost) -> InsightBrief:
    """
    调用 LLM 分析帖子内容
    """
    print(f"DEBUG: analyze_post called (v2) for {post.source_id}")
    
    # Check for AI tags
    # Handle tags (assuming post.tags is List[str])
    is_ai_post = False
    if post.tags:
        for tag in post.tags:
            if "ai" in tag.lower():
                is_ai_post = True
                break
    
    # Fallback: check title if no tags or not found
    if not is_ai_post and "ai" in post.title.lower():
         is_ai_post = True

    # Select Prompt
    selected_system_prompt = AI_SYSTEM_PROMPT if is_ai_post else SYSTEM_PROMPT
    
    # Debug info
    # print(f"DEBUG: is_ai_post={is_ai_post}")
    # print(f"DEBUG: Selected Prompt: {'AI_SYSTEM_PROMPT' if is_ai_post else 'SYSTEM_PROMPT'}")

    # 构造 Prompt 输入
    user_content_text = f"""
    【标题】: {post.title}
    【作者】: {post.author.name}
    【正文】: 
    {post.content}
    
    【图片文字提取 (OCR)】:
    {post.ocr_content if post.ocr_content else "无 (尝试直接分析图片)"}

    【高赞评论】:
    {json.dumps(post.top_comments, ensure_ascii=False)}
    
    【数据】:
    点赞: {post.stats.likes}, 收藏: {post.stats.collects}
    """

    # --- Vision Logic Start ---
    # Try to process images if available
    vision_payload = None
    if post.media.images:
        try:
            print(f"DEBUG: Attempting Vision analysis for {post.source_id}")
            # Process first 2 images to avoid excessive token usage
            images_to_process = post.media.images[:2]
            image_contents = []
            
            for img_url in images_to_process:
                base64_img = encode_image_from_url(img_url)
                if base64_img:
                    image_contents.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_img}"
                        }
                    })
            
            if image_contents:
                vision_payload = {
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": selected_system_prompt},
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": user_content_text},
                                *image_contents
                            ]
                        }
                    ],
                    "max_tokens": 4000,
                    "temperature": get_compatible_temperature(0.7)
                }
        except Exception as e:
            print(f"DEBUG: Vision preparation failed: {e}. Falling back to text.")

    # --- Vision Logic End ---

    # 使用 requests 调用
    # print("DEBUG: Sending request to LLM (requests)...")
    url = f"{settings.openai_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }
    
    # Default Text Payload
    text_payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": selected_system_prompt},
            {"role": "user", "content": user_content_text}
        ],
        "max_tokens": 4000,
        "temperature": get_compatible_temperature(0.7)
    }

    # Decide which payload to use
    payload = vision_payload if vision_payload else text_payload
    
    # print(f"DEBUG: Payload: {json.dumps(payload, ensure_ascii=False)[:500]}...") # Print first 500 chars of payload

    try:
        # print("DEBUG: Before requests.post")
        response = requests.post(url, headers=headers, json=payload, timeout=90) # Increased timeout for images
        
        # If 400 Bad Request (likely model doesn't support vision), fallback to text
        if response.status_code == 400 and vision_payload:
             print("DEBUG: Vision request failed (400). Retrying with text only...")
             response = requests.post(url, headers=headers, json=text_payload, timeout=60)
             
        # print(f"DEBUG: After requests.post, status={response.status_code}")
        response.raise_for_status() # Check for HTTP errors
        result_json = response.json()['choices'][0]['message']['content']
    except Exception as e:
        # print(f"DEBUG: Request failed: {e}")
        # If we failed with vision payload (and it wasn't a 400 caught above), try text fallback one last time
        if vision_payload:
             try:
                 print("DEBUG: Vision request failed with exception. Retrying with text only...")
                 response = requests.post(url, headers=headers, json=text_payload, timeout=60)
                 response.raise_for_status()
                 result_json = response.json()['choices'][0]['message']['content']
             except Exception as text_e:
                 raise ValueError(f"LLM Request Failed (Both Vision and Text): {text_e}")
        else:
             raise ValueError(f"LLM Request Failed: {e}")

    # print(f"DEBUG: Raw response: {result_json[:200]}...")
    
    # Clean the response
    cleaned_json = clean_json_response(result_json)
    
    try:
        data = json.loads(cleaned_json)
    except json.JSONDecodeError:
        print(f"DEBUG: Invalid JSON: {cleaned_json}")
        # Try ast.literal_eval as fallback for Python-style dicts
        try:
            print("DEBUG: Trying ast.literal_eval...")
            data = ast.literal_eval(cleaned_json)
        except Exception as e:
            # If both fail, raise the original error but with more context
            raise ValueError(f"LLM returned invalid JSON (and ast.literal_eval failed): {cleaned_json[:500]}...")
    
    # 补全 meta 信息
    meta_info = {
        "original_id": post.source_id,
        "processed_at": str(post.captured_at)
    }
    
    try:
        summary_data = data.get('summary')
        if not isinstance(summary_data, dict):
            summary_data = {
                "one_liner": "已完成学习向信息提取，请查看学习任务与步骤化方法。",
                "keywords": ["学习助理", "方法提取", "行动计划"]
            }
        summary_data.setdefault("one_liner", "已完成学习向信息提取。")
        summary_data["keywords"] = ensure_list(summary_data.get("keywords"))[:8]

        learning_data = data.get('learning_insight')
        if not isinstance(learning_data, dict):
            learning_data = {}
        learning_data.setdefault("core_takeaways", ensure_list(data.get("domain_knowledge")))
        learning_data.setdefault("key_concepts", [])
        learning_data.setdefault("method_playbook", ensure_list(data.get("learning_path")))
        learning_data.setdefault("evidence_snippets", [])
        learning_data.setdefault("pitfalls", [])
        learning_data.setdefault("prerequisites", [])
        learning_data.setdefault("practice_tasks", [])
        learning_data.setdefault("reflection_questions", [])
        learning_data.setdefault("next_actions_24h", [])
        for list_key in [
            "core_takeaways",
            "method_playbook",
            "evidence_snippets",
            "pitfalls",
            "prerequisites",
            "reflection_questions",
            "next_actions_24h"
        ]:
            learning_data[list_key] = ensure_list(learning_data.get(list_key))

        return InsightBrief(
            meta=meta_info,
            type="ai" if is_ai_post else "general",
            summary=Summary(**summary_data),
            learning_insight=learning_data,
            ai_insight=data.get('ai_insight') if isinstance(data.get('ai_insight'), dict) else None,
            analysis=data.get('analysis'),
            creative_expansion=data.get('creative_expansion'),
            assets=data.get('assets')
        )
    except Exception as e:
        raise ValueError(f"Schema Validation Failed: {str(e)} | Raw: {result_json[:200]}...")

def analyze_multiple_posts(posts: List[RawPost]) -> AggregatedInsight:
    """
    调用 LLM 整合分析多篇帖子
    """
    extractions = [extract_structured_post(post) for post in posts]
    combined_content, source_evidence, diagnostics = build_weighted_context(extractions)
    
    url = f"{settings.openai_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": AGGREGATION_SYSTEM_PROMPT},
            {"role": "user", "content": combined_content}
        ],
        "max_tokens": 4000,
        "temperature": get_compatible_temperature(0.2)
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)
    if response.status_code >= 400:
        raise ValueError(f"Aggregation LLM Request Failed: status={response.status_code}, body={response.text[:500]}")
    result_json = response.json()['choices'][0]['message']['content']
    
    # Clean the response
    cleaned_json = clean_json_response(result_json)
    
    data = json.loads(cleaned_json)

    summary_data = data.get("summary")
    if not isinstance(summary_data, dict):
        summary_data = {
            "one_liner": ensure_string(data.get("topic_overview") or "已完成跨帖学习提炼。"),
            "keywords": ensure_list(data.get("domain_knowledge"))[:8]
        }
    summary_data.setdefault("one_liner", "已完成跨帖学习提炼。")
    summary_data["keywords"] = ensure_list(summary_data.get("keywords"))[:8]

    learning_data = data.get("learning_insight")
    if not isinstance(learning_data, dict):
        learning_data = {}
    learning_data.setdefault("core_takeaways", ensure_list(data.get("domain_knowledge")))
    learning_data.setdefault("key_concepts", [])
    learning_data.setdefault("method_playbook", ensure_list(data.get("learning_path")))
    learning_data.setdefault("evidence_snippets", ensure_list(data.get("source_evidence")))
    learning_data.setdefault("pitfalls", [])
    learning_data.setdefault("prerequisites", [])
    learning_data.setdefault("practice_tasks", [])
    learning_data.setdefault("reflection_questions", ensure_list(data.get("checkpoint_quiz")))
    learning_data.setdefault("next_actions_24h", ensure_list(data.get("implementation_plan")))
    for list_key in [
        "core_takeaways",
        "method_playbook",
        "evidence_snippets",
        "pitfalls",
        "prerequisites",
        "reflection_questions",
        "next_actions_24h"
    ]:
        learning_data[list_key] = ensure_list(learning_data.get(list_key))

    synthesis_data = data.get("cross_post_synthesis")
    if not isinstance(synthesis_data, dict):
        synthesis_data = {}
    synthesis_data.setdefault("consensus", ensure_list(data.get("cross_post_consensus")))
    synthesis_data.setdefault("conflicts", ensure_list(data.get("cross_post_conflicts")))
    synthesis_data.setdefault("knowledge_map", ensure_list(data.get("concept_map")))
    synthesis_data["consensus"] = ensure_list(synthesis_data.get("consensus"))
    synthesis_data["conflicts"] = ensure_list(synthesis_data.get("conflicts"))
    synthesis_data["knowledge_map"] = ensure_list(synthesis_data.get("knowledge_map"))
    synthesis_data["source_evidence"] = source_evidence

    extended_insight = ensure_string(data.get("extended_insight", ""))
    evidence_block = "\n".join([f"- {item}" for item in source_evidence[:8]])
    if evidence_block and "原文证据片段" not in extended_insight:
        extended_insight = f"{extended_insight}\n\n原文证据片段：\n{evidence_block}".strip()

    normalized = {
        "summary": summary_data,
        "learning_insight": learning_data,
        "cross_post_synthesis": synthesis_data,
        "topic_overview": ensure_string(data.get("topic_overview") or summary_data.get("one_liner")),
        "domain_knowledge": ensure_list(data.get("domain_knowledge") or learning_data.get("core_takeaways")),
        "learning_path": ensure_list(data.get("learning_path") or learning_data.get("method_playbook")),
        "extended_insight": extended_insight,
        "concept_map": ensure_list(data.get("concept_map") or synthesis_data.get("knowledge_map")),
        "skill_ladder": ensure_list(data.get("skill_ladder")),
        "implementation_plan": ensure_list(data.get("implementation_plan") or learning_data.get("next_actions_24h")),
        "cross_post_consensus": ensure_list(data.get("cross_post_consensus") or synthesis_data.get("consensus")),
        "cross_post_conflicts": ensure_list(data.get("cross_post_conflicts") or synthesis_data.get("conflicts")),
        "checkpoint_quiz": ensure_list(data.get("checkpoint_quiz") or learning_data.get("reflection_questions")),
        "source_evidence": source_evidence,
        "extraction_diagnostics": diagnostics
    }
    if not normalized["learning_insight"]["evidence_snippets"]:
        normalized["learning_insight"]["evidence_snippets"] = source_evidence[:12]

    return AggregatedInsight(**normalized)

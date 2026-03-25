import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .schemas import RawPost


CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```|`[^`\n]+`")
TOPIC_PATTERN = re.compile(r"#[^#\s\n]{1,80}#?")
MENTION_PATTERN = re.compile(r"@[A-Za-z0-9_\u4e00-\u9fff-]{1,60}")
LINK_PATTERN = re.compile(r"https?://[^\s]+")


@dataclass
class Segment:
    segment_type: str
    text: str
    weight: float
    start: int
    end: int


@dataclass
class StructuredExtraction:
    source_id: str
    normalized_text: str
    segments: List[Segment]
    source_evidence: List[str]
    metrics: Dict[str, float]


def _contains_emoji(text: str) -> bool:
    for char in text:
        code = ord(char)
        if 0x1F300 <= code <= 0x1FAFF:
            return True
    return False


def _collect_matches(pattern: re.Pattern, text: str, label: str, weight: float) -> List[Segment]:
    results: List[Segment] = []
    for match in pattern.finditer(text):
        token = match.group(0).strip()
        if token:
            results.append(Segment(label, token, weight, match.start(), match.end()))
    return results


def _build_section(name: str, value: str) -> str:
    safe_value = value or ""
    return f"[{name}]\n{safe_value}\n"


def _build_base_text(post: RawPost) -> str:
    comments = "\n".join([f"- {item}" for item in post.top_comments]) if post.top_comments else ""
    parts = [
        _build_section("TITLE", post.title),
        _build_section("BODY", post.content),
        _build_section("OCR", post.ocr_content or ""),
        _build_section("COMMENTS", comments),
        _build_section("AUTHOR", post.author.name),
        _build_section("URL", post.url),
    ]
    return "\n".join(parts).strip()


def _extract_evidence(text: str, max_count: int = 6) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    keywords = ("openclaw", "安全", "方案", "控制", "防护", "策略")
    preferred = [line for line in lines if any(keyword in line.lower() for keyword in keywords)]
    if len(preferred) >= max_count:
        return preferred[:max_count]
    fallback = [line for line in lines if len(line) >= 12]
    dedup: List[str] = []
    for line in preferred + fallback:
        if line not in dedup:
            dedup.append(line)
        if len(dedup) >= max_count:
            break
    return dedup


def extract_structured_post(post: RawPost) -> StructuredExtraction:
    normalized_text = _build_base_text(post)
    base_segments = [
        Segment("title", post.title or "", 1.35, 0, len(post.title or "")),
        Segment("body", post.content or "", 1.2, 0, len(post.content or "")),
        Segment("ocr", post.ocr_content or "", 1.1, 0, len(post.ocr_content or "")),
    ]
    if post.top_comments:
        comments_text = "\n".join(post.top_comments)
        base_segments.append(Segment("comment", comments_text, 0.9, 0, len(comments_text)))

    token_segments: List[Segment] = []
    token_segments.extend(_collect_matches(CODE_BLOCK_PATTERN, normalized_text, "code_block", 1.45))
    token_segments.extend(_collect_matches(TOPIC_PATTERN, normalized_text, "topic", 1.05))
    token_segments.extend(_collect_matches(MENTION_PATTERN, normalized_text, "mention", 1.0))
    token_segments.extend(_collect_matches(LINK_PATTERN, normalized_text, "link", 1.0))

    emoji_count = sum(1 for char in normalized_text if 0x1F300 <= ord(char) <= 0x1FAFF)
    if _contains_emoji(normalized_text):
        token_segments.append(Segment("emoji", f"emoji_count={emoji_count}", 0.95, 0, 0))

    source_evidence = _extract_evidence(normalized_text)
    original_len = max(len(post.content or "") + len(post.title or ""), 1)
    preserved_len = len(normalized_text)
    retention_ratio = min(1.0, preserved_len / original_len)

    metrics = {
        "char_retention_ratio": round(retention_ratio, 4),
        "token_segment_count": float(len(token_segments)),
        "evidence_count": float(len(source_evidence)),
    }
    return StructuredExtraction(
        source_id=post.source_id,
        normalized_text=normalized_text,
        segments=base_segments + token_segments,
        source_evidence=source_evidence,
        metrics=metrics,
    )


def build_weighted_context(extractions: List[StructuredExtraction], max_chars_per_post: int = 2500) -> Tuple[str, List[str], Dict[str, float]]:
    blocks: List[str] = []
    merged_evidence: List[str] = []
    total_retention = 0.0
    total_posts = max(len(extractions), 1)

    for idx, item in enumerate(extractions, start=1):
        text = item.normalized_text
        if len(text) > max_chars_per_post:
            text = text[:max_chars_per_post]
        segment_lines = []
        for segment in item.segments:
            if segment.text:
                segment_lines.append(f"- {segment.segment_type} | weight={segment.weight:.2f} | {segment.text[:160]}")
        blocks.append(
            "\n".join(
                [
                    f"--- 笔记 {idx} ({item.source_id}) ---",
                    text,
                    "[结构化标注]",
                    "\n".join(segment_lines[:25]),
                ]
            )
        )
        total_retention += item.metrics.get("char_retention_ratio", 0.0)
        for snippet in item.source_evidence:
            if snippet not in merged_evidence:
                merged_evidence.append(snippet)

    diagnostics = {
        "avg_char_retention_ratio": round(total_retention / total_posts, 4),
        "post_count": float(len(extractions)),
        "evidence_snippet_count": float(len(merged_evidence)),
    }
    return "\n\n".join(blocks), merged_evidence[:20], diagnostics

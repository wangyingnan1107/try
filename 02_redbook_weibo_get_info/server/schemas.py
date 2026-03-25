from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- Raw Data (Input) ---

class Author(BaseModel):
    name: str
    uid: str

class Media(BaseModel):
    images: List[str] = []
    video_cover: Optional[str] = None

class Stats(BaseModel):
    likes: int = 0
    collects: int = 0
    comments_count: int = 0

class RawPost(BaseModel):
    source_id: str = Field(..., description="平台唯一ID")
    platform: str = Field(default="xiaohongshu")
    url: str
    title: str
    content: str
    ocr_content: Optional[str] = Field(default=None, description="图片中的文字内容")
    author: Author
    media: Media
    stats: Stats
    top_comments: List[str] = []
    tags: List[str] = []
    captured_at: datetime = Field(default_factory=datetime.now)

# --- Insight (Output/Processed) ---

class Summary(BaseModel):
    one_liner: str
    keywords: List[str]

class Analysis(BaseModel):
    hook_point: str
    emotional_value: str
    target_audience: str

class CreativeExpansion(BaseModel):
    viewpoints: List[str]
    counter_intuition: Optional[str] = None
    writing_angle: Optional[str] = None

class Assets(BaseModel):
    quotes: List[str] = []
    image_prompts: List[str] = []

# --- AI Specific Schemas ---

class GlossaryItem(BaseModel):
    term: str
    definition: str
    importance: str
    analogy: str

class Architecture(BaseModel):
    analogy: str
    flow_diagram: str
    components: str

class CompetitorAnalysis(BaseModel):
    comparison_table: str
    unique_selling_point: str
    weakness: str

class RadarDimension(BaseModel):
    dimension: str
    score: int

class AiAnalysis(BaseModel):
    glossary: List[GlossaryItem]
    architecture: Architecture
    competitor_analysis: CompetitorAnalysis
    radar_chart: List[RadarDimension]

class KeyConcept(BaseModel):
    term: str
    explanation: str
    application: str

class PracticeTask(BaseModel):
    task: str
    difficulty: str
    expected_outcome: str

class LearningInsight(BaseModel):
    core_takeaways: List[str] = []
    key_concepts: List[KeyConcept] = []
    method_playbook: List[str] = []
    evidence_snippets: List[str] = []
    pitfalls: List[str] = []
    prerequisites: List[str] = []
    practice_tasks: List[PracticeTask] = []
    reflection_questions: List[str] = []
    next_actions_24h: List[str] = []

class CrossPostSynthesis(BaseModel):
    consensus: List[str] = []
    conflicts: List[str] = []
    knowledge_map: List[str] = []
    source_evidence: List[str] = []

class InsightBrief(BaseModel):
    meta: Dict[str, Any]
    type: str = "general" # general | ai
    
    # General Fields
    summary: Optional[Summary] = None
    analysis: Optional[Analysis] = None
    creative_expansion: Optional[CreativeExpansion] = None
    assets: Optional[Assets] = None
    
    # AI Fields
    ai_insight: Optional[AiAnalysis] = None
    learning_insight: Optional[LearningInsight] = None

# --- Aggregated Report (New Iteration) ---

class AggregatedInsight(BaseModel):
    summary: Summary = Field(..., description="整合后的一句话结论与关键词")
    learning_insight: LearningInsight = Field(..., description="跨帖子学习提炼")
    cross_post_synthesis: CrossPostSynthesis = Field(default_factory=CrossPostSynthesis, description="跨帖综合归纳")
    topic_overview: str = Field(default="", description="方向：整合后的主题方向概述")
    domain_knowledge: List[str] = Field(default_factory=list, description="涉及的领域的知识：核心知识点列表")
    learning_path: List[str] = Field(default_factory=list, description="需要学习的内容：针对AI Coding新人的具体学习建议")
    extended_insight: str = Field(default="", description="适量扩展：基于内容的深度分析与扩展")
    concept_map: List[str] = Field(default_factory=list, description="概念图谱")
    skill_ladder: List[str] = Field(default_factory=list, description="技能阶梯")
    implementation_plan: List[str] = Field(default_factory=list, description="落地执行计划")
    cross_post_consensus: List[str] = Field(default_factory=list, description="跨帖共识")
    cross_post_conflicts: List[str] = Field(default_factory=list, description="跨帖分歧与适用条件")
    checkpoint_quiz: List[str] = Field(default_factory=list, description="自测题")
    source_evidence: List[str] = Field(default_factory=list, description="关键原文证据片段")
    extraction_diagnostics: Dict[str, float] = Field(default_factory=dict, description="抽取链路诊断指标")

class ReportRequest(BaseModel):
    post_ids: List[str]

"""Pydantic 스키마 정의"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ===== Clause 스키마 =====
class ClauseBase(BaseModel):
    clause_number: int
    clause_number_display: str
    title: str
    content: Optional[Any] = None
    order_index: int


class ClauseCreate(ClauseBase):
    pass


class ClauseResponse(ClauseBase):
    id: int
    article_id: int

    class Config:
        from_attributes = True


# ===== Article 스키마 =====
class ArticleBase(BaseModel):
    article_number: int
    article_number_display: str
    title: str
    order_index: int


class ArticleCreate(ArticleBase):
    clauses: List[ClauseCreate] = []


class ArticleResponse(ArticleBase):
    id: int
    agreement_id: int
    clause_count: int = 0

    class Config:
        from_attributes = True


class ArticleWithClauses(ArticleResponse):
    clauses: List[ClauseResponse] = []


# ===== LoanAgreement 스키마 =====
class LoanAgreementBase(BaseModel):
    name: str
    file_name: str
    description: Optional[str] = None


class LoanAgreementCreate(LoanAgreementBase):
    articles: List[ArticleCreate] = []


class LoanAgreementResponse(LoanAgreementBase):
    id: int
    created_at: datetime
    updated_at: datetime
    article_count: int = 0

    class Config:
        from_attributes = True


class LoanAgreementWithArticles(LoanAgreementResponse):
    articles: List[ArticleResponse] = []


class LoanAgreementFull(LoanAgreementResponse):
    articles: List[ArticleWithClauses] = []


# ===== 파싱 결과 스키마 =====
class ParsedClause(BaseModel):
    clause_number: int
    clause_number_display: str
    title: str
    content: Any
    order_index: int


class ParsedArticle(BaseModel):
    article_number: int
    article_number_display: str
    title: str
    order_index: int
    clauses: List[ParsedClause] = []


class ParsedDocument(BaseModel):
    name: str
    file_name: str
    description: Optional[str] = None
    articles: List[ParsedArticle] = []


# ===== 프롬프트 생성 스키마 =====

class PromptGenerateRequest(BaseModel):
    """프롬프트 생성 요청"""
    term_sheet_text: str  # Term Sheet 텍스트
    agreement_id: int  # 참조할 대출약정서 ID
    article_id: int  # 참조할 조 ID
    clause_id: Optional[int] = None  # 참조할 항 ID (선택적)


class PromptGenerateResponse(BaseModel):
    """프롬프트 생성 응답"""
    prompt: str  # 생성된 프롬프트
    reference_article: str  # 참조된 조 정보
    reference_clauses: List[str]  # 참조된 항 정보 목록


# ===== 생성 대출약정서 스키마 =====

class GeneratedClauseBase(BaseModel):
    clause_number: Optional[int] = None
    clause_number_display: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    order_index: int = 0
    ref_clause_id: Optional[int] = None
    score: Optional[int] = None  # 담당자 평가 점수 (1-5)


class GeneratedClauseCreate(GeneratedClauseBase):
    pass


class GeneratedClauseUpdate(BaseModel):
    clause_number: Optional[int] = None
    clause_number_display: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    order_index: Optional[int] = None


class GeneratedClauseResponse(GeneratedClauseBase):
    id: int
    article_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GeneratedArticleBase(BaseModel):
    article_number: Optional[int] = None
    article_number_display: Optional[str] = None
    title: Optional[str] = None
    order_index: int = 0
    ref_agreement_id: Optional[int] = None
    ref_article_id: Optional[int] = None
    term_sheet_text: Optional[str] = None


class GeneratedArticleCreate(GeneratedArticleBase):
    clauses: List[GeneratedClauseCreate] = []


class GeneratedArticleUpdate(BaseModel):
    article_number: Optional[int] = None
    article_number_display: Optional[str] = None
    title: Optional[str] = None
    order_index: Optional[int] = None
    term_sheet_text: Optional[str] = None


class GeneratedArticleResponse(GeneratedArticleBase):
    id: int
    agreement_id: int
    created_at: datetime
    clause_count: int = 0

    class Config:
        from_attributes = True


class GeneratedArticleWithClauses(GeneratedArticleResponse):
    clauses: List[GeneratedClauseResponse] = []


class GeneratedAgreementBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_agreement_id: Optional[int] = None


class GeneratedAgreementCreate(GeneratedAgreementBase):
    pass


class GeneratedAgreementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_agreement_id: Optional[int] = None


class GeneratedAgreementResponse(GeneratedAgreementBase):
    id: int
    created_at: datetime
    updated_at: datetime
    article_count: int = 0

    class Config:
        from_attributes = True


class GeneratedAgreementWithArticles(GeneratedAgreementResponse):
    articles: List[GeneratedArticleResponse] = []


class GeneratedAgreementFull(GeneratedAgreementResponse):
    articles: List[GeneratedArticleWithClauses] = []


# ===== AI 결과 저장 스키마 =====

class SaveAIResultRequest(BaseModel):
    """AI 결과 저장 요청"""
    generated_agreement_id: int  # 저장할 생성 약정서 ID
    article_number: Optional[int] = None
    article_number_display: Optional[str] = None
    article_title: Optional[str] = None
    clause_title: Optional[str] = None  # 항 제목
    ref_agreement_id: Optional[int] = None  # 참조한 원본 약정서 ID
    ref_article_id: Optional[int] = None  # 참조한 원본 조 ID
    ref_clause_id: Optional[int] = None  # 참조한 원본 항 ID
    term_sheet_text: Optional[str] = None  # 사용된 Term Sheet
    ai_content: str  # AI 생성 내용
    multi_clause_mode: bool = False  # True면 AI 응답을 파싱하여 다중 항 저장
    clause_number: Optional[int] = None          # 저장할 항 번호
    clause_number_display: Optional[str] = None  # 저장할 항 번호 표시용
    log_id: Optional[int] = None  # 연결된 AI 호출 로그 ID
    score: Optional[int] = None  # 평가 점수 (1-5)
    target_article_id: Optional[int] = None  # 기존 조 ID (있으면 해당 조에 항 추가)


# ===== ChatGPT 호출 스키마 =====

class ChatGPTGenerateRequest(BaseModel):
    """ChatGPT 호출 및 저장 요청"""
    generated_agreement_id: int  # 저장할 생성 약정서 ID
    term_sheet_text: str  # Term Sheet 텍스트
    agreement_id: int  # 참조할 대출약정서 ID
    article_id: int  # 참조할 조 ID
    clause_id: Optional[int] = None  # 참조할 항 ID (선택적)
    skip_save: bool = False  # True면 저장하지 않고 결과만 반환
    custom_prompt: Optional[str] = None  # 사용자가 수정한 프롬프트 (있으면 이걸 사용)


class ChatGPTGenerateResponse(BaseModel):
    """ChatGPT 호출 및 저장 응답"""
    success: bool
    generated_article_id: Optional[int] = None  # 저장된 생성 조 ID (skip_save=True면 None)
    generated_agreement_id: int  # 생성 약정서 ID
    reference_article: str  # 참조된 조 정보
    ai_content: str  # AI 생성 내용
    message: str  # 결과 메시지
    log_id: Optional[int] = None  # 생성된 AI 호출 로그 ID


# ===== AI 로그 점수 업데이트 스키마 =====

class AILogScoreUpdate(BaseModel):
    """AI 로그 점수 업데이트 요청"""
    score: int  # 1-5

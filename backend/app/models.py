"""SQLAlchemy 데이터베이스 모델 정의"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .database import Base


class LoanAgreement(Base):
    """대출약정서 기본 정보 테이블"""
    __tablename__ = "loan_agreements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)  # 약정서 이름
    file_name = Column(String(500), nullable=False)  # 원본 파일명
    description = Column(Text, nullable=True)  # 설명
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    # 관계 설정
    articles = relationship("Article", back_populates="agreement",
                           cascade="all, delete-orphan",
                           order_by="Article.order_index")

    def __repr__(self):
        return f"<LoanAgreement(id={self.id}, name='{self.name}')>"


class Article(Base):
    """조(Article) 테이블 - 대출약정서의 조항"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, ForeignKey("loan_agreements.id"), nullable=False)
    article_number = Column(Integer, nullable=False)  # 조 번호 (정수)
    article_number_display = Column(String(20), nullable=False)  # 표시용 (예: "4조의2")
    title = Column(String(500), nullable=False, index=True)  # 조 타이틀
    order_index = Column(Integer, nullable=False)  # 정렬 순서

    # 관계 설정
    agreement = relationship("LoanAgreement", back_populates="articles")
    clauses = relationship("Clause", back_populates="article",
                          cascade="all, delete-orphan",
                          order_by="Clause.order_index")

    def __repr__(self):
        return f"<Article(id={self.id}, number={self.article_number_display}, title='{self.title}')>"


class Clause(Base):
    """항(Clause) 테이블 - 조 아래의 세부 항목"""
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    clause_number = Column(Integer, nullable=False)  # 항 번호
    clause_number_display = Column(String(20), nullable=False)  # 표시용
    title = Column(String(500), nullable=False, index=True)  # 항 타이틀
    content = Column(JSON, nullable=True)  # 항 내용 (JSON 형태로 저장)
    order_index = Column(Integer, nullable=False)  # 정렬 순서

    # 관계 설정
    article = relationship("Article", back_populates="clauses")

    def __repr__(self):
        return f"<Clause(id={self.id}, number={self.clause_number_display}, title='{self.title}')>"


# ===== 생성 대출약정서 관련 모델 =====

class GeneratedAgreement(Base):
    """생성 대출약정서 테이블"""
    __tablename__ = "generated_agreements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)  # 약정서 이름
    description = Column(Text, nullable=True)  # 설명
    base_agreement_id = Column(Integer, ForeignKey("loan_agreements.id"), nullable=True)  # 참조 원본
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    # 관계 설정
    base_agreement = relationship("LoanAgreement")
    articles = relationship("GeneratedArticle", back_populates="agreement",
                           cascade="all, delete-orphan",
                           order_by="GeneratedArticle.order_index")

    def __repr__(self):
        return f"<GeneratedAgreement(id={self.id}, name='{self.name}')>"


class GeneratedArticle(Base):
    """생성 조(Article) 테이블"""
    __tablename__ = "generated_articles"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, ForeignKey("generated_agreements.id"), nullable=False)
    article_number = Column(Integer, nullable=True)  # 조 번호
    article_number_display = Column(String(20), nullable=True)  # 표시용 ("4의2")
    title = Column(String(500), nullable=True, index=True)  # 조 제목
    order_index = Column(Integer, nullable=False, default=0)  # 정렬 순서

    # 참조 정보
    ref_agreement_id = Column(Integer, nullable=True)  # 참조한 원본 약정서
    ref_article_id = Column(Integer, nullable=True)  # 참조한 원본 조
    term_sheet_text = Column(Text, nullable=True)  # 사용된 Term Sheet

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 관계 설정
    agreement = relationship("GeneratedAgreement", back_populates="articles")
    clauses = relationship("GeneratedClause", back_populates="article",
                          cascade="all, delete-orphan",
                          order_by="GeneratedClause.order_index")

    def __repr__(self):
        return f"<GeneratedArticle(id={self.id}, number={self.article_number_display}, title='{self.title}')>"


class GeneratedClause(Base):
    """생성 항(Clause) 테이블"""
    __tablename__ = "generated_clauses"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("generated_articles.id"), nullable=False)
    clause_number = Column(Integer, nullable=True)  # 항 번호
    clause_number_display = Column(String(20), nullable=True)  # 표시용
    title = Column(String(500), nullable=True, index=True)  # 항 제목
    content = Column(Text, nullable=True)  # AI 생성 내용 (JSON 또는 텍스트)
    order_index = Column(Integer, nullable=False, default=0)  # 정렬 순서

    # 참조 정보
    ref_clause_id = Column(Integer, nullable=True)  # 참조한 원본 항

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    # 관계 설정
    article = relationship("GeneratedArticle", back_populates="clauses")

    def __repr__(self):
        return f"<GeneratedClause(id={self.id}, number={self.clause_number_display}, title='{self.title}')>"

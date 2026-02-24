"""CRUD 작업 정의"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from . import models, schemas


# ===== LoanAgreement CRUD =====

def create_agreement(db: Session, parsed_doc: schemas.ParsedDocument) -> models.LoanAgreement:
    """파싱된 문서에서 대출약정서 생성"""
    # 약정서 생성
    db_agreement = models.LoanAgreement(
        name=parsed_doc.name,
        file_name=parsed_doc.file_name,
        description=parsed_doc.description
    )
    db.add(db_agreement)
    db.flush()  # ID 생성을 위해

    # 조 생성
    for article in parsed_doc.articles:
        db_article = models.Article(
            agreement_id=db_agreement.id,
            article_number=article.article_number,
            article_number_display=article.article_number_display,
            title=article.title,
            order_index=article.order_index
        )
        db.add(db_article)
        db.flush()

        # 항 생성
        for clause in article.clauses:
            db_clause = models.Clause(
                article_id=db_article.id,
                clause_number=clause.clause_number,
                clause_number_display=clause.clause_number_display,
                title=clause.title,
                content=clause.content,
                order_index=clause.order_index
            )
            db.add(db_clause)

    db.commit()
    db.refresh(db_agreement)
    return db_agreement


def get_agreements(db: Session, skip: int = 0, limit: int = 100) -> List[models.LoanAgreement]:
    """모든 대출약정서 조회"""
    return db.query(models.LoanAgreement)\
             .order_by(models.LoanAgreement.created_at.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()


def get_agreement(db: Session, agreement_id: int) -> Optional[models.LoanAgreement]:
    """특정 대출약정서 조회"""
    return db.query(models.LoanAgreement)\
             .filter(models.LoanAgreement.id == agreement_id)\
             .first()


def get_agreement_with_article_count(db: Session, agreement_id: int) -> Optional[dict]:
    """조 개수 포함하여 약정서 조회"""
    agreement = get_agreement(db, agreement_id)
    if not agreement:
        return None

    article_count = db.query(func.count(models.Article.id))\
                      .filter(models.Article.agreement_id == agreement_id)\
                      .scalar()

    return {
        "agreement": agreement,
        "article_count": article_count
    }


def delete_agreement(db: Session, agreement_id: int) -> bool:
    """대출약정서 삭제 (CASCADE로 조/항도 삭제)"""
    agreement = get_agreement(db, agreement_id)
    if not agreement:
        return False
    db.delete(agreement)
    db.commit()
    return True


# ===== Article CRUD =====

def get_articles(db: Session, agreement_id: int) -> List[models.Article]:
    """약정서의 모든 조 조회"""
    return db.query(models.Article)\
             .filter(models.Article.agreement_id == agreement_id)\
             .order_by(models.Article.order_index)\
             .all()


def get_articles_with_clause_count(db: Session, agreement_id: int) -> List[dict]:
    """항 개수 포함하여 조 조회"""
    articles = get_articles(db, agreement_id)
    result = []

    for article in articles:
        clause_count = db.query(func.count(models.Clause.id))\
                         .filter(models.Clause.article_id == article.id)\
                         .scalar()
        result.append({
            "article": article,
            "clause_count": clause_count
        })

    return result


def get_article(db: Session, article_id: int) -> Optional[models.Article]:
    """특정 조 조회"""
    return db.query(models.Article)\
             .filter(models.Article.id == article_id)\
             .first()


# ===== Clause CRUD =====

def get_clauses(db: Session, article_id: int) -> List[models.Clause]:
    """조의 모든 항 조회"""
    return db.query(models.Clause)\
             .filter(models.Clause.article_id == article_id)\
             .order_by(models.Clause.order_index)\
             .all()


def get_clause(db: Session, clause_id: int) -> Optional[models.Clause]:
    """특정 항 조회"""
    return db.query(models.Clause)\
             .filter(models.Clause.id == clause_id)\
             .first()


# ===== 검색 기능 =====

def search_articles_by_title(db: Session, title_keyword: str) -> List[models.Article]:
    """조 타이틀로 검색"""
    return db.query(models.Article)\
             .filter(models.Article.title.contains(title_keyword))\
             .order_by(models.Article.agreement_id, models.Article.order_index)\
             .all()


def search_clauses_by_title(db: Session, title_keyword: str) -> List[models.Clause]:
    """항 타이틀로 검색"""
    return db.query(models.Clause)\
             .filter(models.Clause.title.contains(title_keyword))\
             .order_by(models.Clause.article_id, models.Clause.order_index)\
             .all()


# ===== GeneratedAgreement CRUD =====

def create_generated_agreement(db: Session, data: schemas.GeneratedAgreementCreate) -> models.GeneratedAgreement:
    """생성 대출약정서 생성"""
    db_agreement = models.GeneratedAgreement(
        name=data.name,
        description=data.description,
        base_agreement_id=data.base_agreement_id
    )
    db.add(db_agreement)
    db.commit()
    db.refresh(db_agreement)
    return db_agreement


def get_generated_agreements(db: Session, skip: int = 0, limit: int = 100) -> List[models.GeneratedAgreement]:
    """모든 생성 대출약정서 조회"""
    return db.query(models.GeneratedAgreement)\
             .order_by(models.GeneratedAgreement.created_at.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()


def get_generated_agreement(db: Session, agreement_id: int) -> Optional[models.GeneratedAgreement]:
    """특정 생성 대출약정서 조회"""
    return db.query(models.GeneratedAgreement)\
             .filter(models.GeneratedAgreement.id == agreement_id)\
             .first()


def update_generated_agreement(
    db: Session, agreement_id: int, data: schemas.GeneratedAgreementUpdate
) -> Optional[models.GeneratedAgreement]:
    """생성 대출약정서 수정"""
    agreement = get_generated_agreement(db, agreement_id)
    if not agreement:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agreement, key, value)

    db.commit()
    db.refresh(agreement)
    return agreement


def delete_generated_agreement(db: Session, agreement_id: int) -> bool:
    """생성 대출약정서 삭제 (CASCADE로 조/항도 삭제)"""
    agreement = get_generated_agreement(db, agreement_id)
    if not agreement:
        return False
    db.delete(agreement)
    db.commit()
    return True


# ===== GeneratedArticle CRUD =====

def get_generated_articles(db: Session, agreement_id: int) -> List[models.GeneratedArticle]:
    """생성 약정서의 모든 조 조회"""
    return db.query(models.GeneratedArticle)\
             .filter(models.GeneratedArticle.agreement_id == agreement_id)\
             .order_by(models.GeneratedArticle.order_index)\
             .all()


def get_generated_article(db: Session, article_id: int) -> Optional[models.GeneratedArticle]:
    """특정 생성 조 조회"""
    return db.query(models.GeneratedArticle)\
             .filter(models.GeneratedArticle.id == article_id)\
             .first()


def create_generated_article(
    db: Session, agreement_id: int, data: schemas.GeneratedArticleCreate
) -> models.GeneratedArticle:
    """생성 조 추가"""
    # 현재 최대 order_index 조회
    max_order = db.query(func.max(models.GeneratedArticle.order_index))\
                  .filter(models.GeneratedArticle.agreement_id == agreement_id)\
                  .scalar() or 0

    db_article = models.GeneratedArticle(
        agreement_id=agreement_id,
        article_number=data.article_number,
        article_number_display=data.article_number_display,
        title=data.title,
        order_index=data.order_index if data.order_index > 0 else max_order + 1,
        ref_agreement_id=data.ref_agreement_id,
        ref_article_id=data.ref_article_id,
        term_sheet_text=data.term_sheet_text
    )
    db.add(db_article)
    db.flush()

    # 항 추가
    for clause_data in data.clauses:
        db_clause = models.GeneratedClause(
            article_id=db_article.id,
            clause_number=clause_data.clause_number,
            clause_number_display=clause_data.clause_number_display,
            title=clause_data.title,
            content=clause_data.content,
            order_index=clause_data.order_index,
            ref_clause_id=clause_data.ref_clause_id,
            score=clause_data.score
        )
        db.add(db_clause)

    db.commit()
    db.refresh(db_article)
    return db_article


def update_generated_article(
    db: Session, article_id: int, data: schemas.GeneratedArticleUpdate
) -> Optional[models.GeneratedArticle]:
    """생성 조 수정"""
    article = get_generated_article(db, article_id)
    if not article:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)

    db.commit()
    db.refresh(article)
    return article


def delete_generated_article(db: Session, article_id: int) -> bool:
    """생성 조 삭제 (CASCADE로 항도 삭제)"""
    article = get_generated_article(db, article_id)
    if not article:
        return False
    db.delete(article)
    db.commit()
    return True


# ===== GeneratedClause CRUD =====

def get_generated_clauses(db: Session, article_id: int) -> List[models.GeneratedClause]:
    """생성 조의 모든 항 조회"""
    return db.query(models.GeneratedClause)\
             .filter(models.GeneratedClause.article_id == article_id)\
             .order_by(models.GeneratedClause.clause_number)\
             .all()


def get_generated_clause(db: Session, clause_id: int) -> Optional[models.GeneratedClause]:
    """특정 생성 항 조회"""
    return db.query(models.GeneratedClause)\
             .filter(models.GeneratedClause.id == clause_id)\
             .first()


def create_generated_clause(
    db: Session, article_id: int, data: schemas.GeneratedClauseCreate
) -> models.GeneratedClause:
    """생성 항 추가"""
    # 현재 최대 order_index 조회
    max_order = db.query(func.max(models.GeneratedClause.order_index))\
                  .filter(models.GeneratedClause.article_id == article_id)\
                  .scalar() or 0

    db_clause = models.GeneratedClause(
        article_id=article_id,
        clause_number=data.clause_number,
        clause_number_display=data.clause_number_display,
        title=data.title,
        content=data.content,
        order_index=data.order_index if data.order_index > 0 else max_order + 1,
        ref_clause_id=data.ref_clause_id,
        score=data.score
    )
    db.add(db_clause)
    db.commit()
    db.refresh(db_clause)
    return db_clause


def update_generated_clause(
    db: Session, clause_id: int, data: schemas.GeneratedClauseUpdate
) -> Optional[models.GeneratedClause]:
    """생성 항 수정"""
    clause = get_generated_clause(db, clause_id)
    if not clause:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(clause, key, value)

    db.commit()
    db.refresh(clause)
    return clause


def delete_generated_clause(db: Session, clause_id: int) -> bool:
    """생성 항 삭제"""
    clause = get_generated_clause(db, clause_id)
    if not clause:
        return False
    db.delete(clause)
    db.commit()
    return True

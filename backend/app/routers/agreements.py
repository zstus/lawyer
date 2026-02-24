"""대출약정서 API 라우터"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import crud, schemas, models
from ..parser import parse_docx_bytes
from ..services.prompt_service import build_generation_prompt

router = APIRouter(prefix="/api/agreements", tags=["agreements"])


# ===== 약정서 관련 API =====

@router.post("/upload", response_model=schemas.LoanAgreementResponse)
async def upload_agreement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """대출약정서 DOCX 파일 업로드 및 파싱"""
    # 파일 확장자 검증
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="DOCX 파일만 업로드 가능합니다.")

    try:
        # 파일 읽기
        content = await file.read()

        # 파싱
        parsed_doc = parse_docx_bytes(content, file.filename)

        # 저장
        agreement = crud.create_agreement(db, parsed_doc)

        return schemas.LoanAgreementResponse(
            id=agreement.id,
            name=agreement.name,
            file_name=agreement.file_name,
            description=agreement.description,
            created_at=agreement.created_at,
            updated_at=agreement.updated_at,
            article_count=len(parsed_doc.articles)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류: {str(e)}")


@router.get("/", response_model=List[schemas.LoanAgreementResponse])
def list_agreements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """모든 대출약정서 목록 조회"""
    agreements = crud.get_agreements(db, skip=skip, limit=limit)
    result = []

    for agreement in agreements:
        article_count = len(agreement.articles)
        result.append(schemas.LoanAgreementResponse(
            id=agreement.id,
            name=agreement.name,
            file_name=agreement.file_name,
            description=agreement.description,
            created_at=agreement.created_at,
            updated_at=agreement.updated_at,
            article_count=article_count
        ))

    return result


@router.get("/{agreement_id}", response_model=schemas.LoanAgreementWithArticles)
def get_agreement(agreement_id: int, db: Session = Depends(get_db)):
    """특정 대출약정서 상세 조회 (조 목록 포함)"""
    agreement = crud.get_agreement(db, agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="대출약정서를 찾을 수 없습니다.")

    articles = crud.get_articles_with_clause_count(db, agreement_id)

    return schemas.LoanAgreementWithArticles(
        id=agreement.id,
        name=agreement.name,
        file_name=agreement.file_name,
        description=agreement.description,
        created_at=agreement.created_at,
        updated_at=agreement.updated_at,
        article_count=len(articles),
        articles=[
            schemas.ArticleResponse(
                id=a["article"].id,
                agreement_id=a["article"].agreement_id,
                article_number=a["article"].article_number,
                article_number_display=a["article"].article_number_display,
                title=a["article"].title,
                order_index=a["article"].order_index,
                clause_count=a["clause_count"]
            )
            for a in articles
        ]
    )


@router.delete("/{agreement_id}")
def delete_agreement(agreement_id: int, db: Session = Depends(get_db)):
    """대출약정서 삭제"""
    if not crud.delete_agreement(db, agreement_id):
        raise HTTPException(status_code=404, detail="대출약정서를 찾을 수 없습니다.")
    return {"message": "삭제되었습니다."}


# ===== 조(Article) 관련 API =====

@router.get("/{agreement_id}/articles", response_model=List[schemas.ArticleResponse])
def list_articles(agreement_id: int, db: Session = Depends(get_db)):
    """약정서의 조 목록 조회"""
    # 약정서 존재 확인
    agreement = crud.get_agreement(db, agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="대출약정서를 찾을 수 없습니다.")

    articles = crud.get_articles_with_clause_count(db, agreement_id)

    return [
        schemas.ArticleResponse(
            id=a["article"].id,
            agreement_id=a["article"].agreement_id,
            article_number=a["article"].article_number,
            article_number_display=a["article"].article_number_display,
            title=a["article"].title,
            order_index=a["article"].order_index,
            clause_count=a["clause_count"]
        )
        for a in articles
    ]


@router.get("/{agreement_id}/articles/{article_id}", response_model=schemas.ArticleWithClauses)
def get_article(agreement_id: int, article_id: int, db: Session = Depends(get_db)):
    """특정 조 상세 조회 (항 목록 포함)"""
    article = crud.get_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="조를 찾을 수 없습니다.")

    clauses = crud.get_clauses(db, article_id)

    return schemas.ArticleWithClauses(
        id=article.id,
        agreement_id=article.agreement_id,
        article_number=article.article_number,
        article_number_display=article.article_number_display,
        title=article.title,
        order_index=article.order_index,
        clause_count=len(clauses),
        clauses=[
            schemas.ClauseResponse(
                id=c.id,
                article_id=c.article_id,
                clause_number=c.clause_number,
                clause_number_display=c.clause_number_display,
                title=c.title,
                content=c.content,
                order_index=c.order_index
            )
            for c in clauses
        ]
    )


# ===== 항(Clause) 관련 API =====

@router.get("/{agreement_id}/articles/{article_id}/clauses", response_model=List[schemas.ClauseResponse])
def list_clauses(agreement_id: int, article_id: int, db: Session = Depends(get_db)):
    """조의 항 목록 조회"""
    article = crud.get_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="조를 찾을 수 없습니다.")

    clauses = crud.get_clauses(db, article_id)

    return [
        schemas.ClauseResponse(
            id=c.id,
            article_id=c.article_id,
            clause_number=c.clause_number,
            clause_number_display=c.clause_number_display,
            title=c.title,
            content=c.content,
            order_index=c.order_index
        )
        for c in clauses
    ]


@router.get("/{agreement_id}/articles/{article_id}/clauses/{clause_id}", response_model=schemas.ClauseResponse)
def get_clause(agreement_id: int, article_id: int, clause_id: int, db: Session = Depends(get_db)):
    """특정 항 상세 조회 (내용 포함)"""
    clause = crud.get_clause(db, clause_id)
    if not clause or clause.article_id != article_id:
        raise HTTPException(status_code=404, detail="항을 찾을 수 없습니다.")

    # 조-약정서 관계 확인
    article = crud.get_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="항을 찾을 수 없습니다.")

    return schemas.ClauseResponse(
        id=clause.id,
        article_id=clause.article_id,
        clause_number=clause.clause_number,
        clause_number_display=clause.clause_number_display,
        title=clause.title,
        content=clause.content,
        order_index=clause.order_index
    )


# ===== 검색 API =====

@router.get("/search/articles")
def search_articles(q: str, db: Session = Depends(get_db)):
    """조 타이틀로 검색"""
    articles = crud.search_articles_by_title(db, q)
    return [
        {
            "id": a.id,
            "agreement_id": a.agreement_id,
            "article_number_display": a.article_number_display,
            "title": a.title
        }
        for a in articles
    ]


@router.get("/search/clauses")
def search_clauses(q: str, db: Session = Depends(get_db)):
    """항 타이틀로 검색"""
    clauses = crud.search_clauses_by_title(db, q)
    return [
        {
            "id": c.id,
            "article_id": c.article_id,
            "clause_number_display": c.clause_number_display,
            "title": c.title
        }
        for c in clauses
    ]


# ===== 프롬프트 생성 API =====

@router.post("/generate-prompt", response_model=schemas.PromptGenerateResponse)
def generate_prompt(
    request: schemas.PromptGenerateRequest,
    db: Session = Depends(get_db)
):
    """Term Sheet 정보를 기반으로 대출약정서 조항 생성 프롬프트 생성"""

    # 1. 약정서 존재 확인
    agreement = crud.get_agreement(db, request.agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="대출약정서를 찾을 수 없습니다.")

    # 2. 조 존재 확인
    article = crud.get_article(db, request.article_id)
    if not article or article.agreement_id != request.agreement_id:
        raise HTTPException(status_code=404, detail="조를 찾을 수 없습니다.")

    # 3. 항 목록 조회
    clauses = crud.get_clauses(db, request.article_id)

    # 4. 특정 항이 지정된 경우 해당 항만 사용
    if request.clause_id:
        clauses = [c for c in clauses if c.id == request.clause_id]
        if not clauses:
            raise HTTPException(status_code=404, detail="항을 찾을 수 없습니다.")

    # 5. 참조 정보 구성
    reference_article = f"제{article.article_number_display}조 {article.title}"
    reference_clauses = []
    clause_structure = []

    for clause in clauses:
        clause_info = f"제{clause.clause_number_display}항 {clause.title}"
        reference_clauses.append(clause_info)

        # 항 내용 추출
        content_text = ""
        if clause.content:
            if isinstance(clause.content, dict):
                content_text = clause.content.get("text", "")
            else:
                content_text = str(clause.content)

        clause_structure.append({
            "number": clause.clause_number_display,
            "title": clause.title,
            "content": content_text
        })

    # 6. 프롬프트 생성
    prompt = build_generation_prompt(
        term_sheet_text=request.term_sheet_text,
        agreement_name=agreement.name,
        clause_structure=clause_structure
    )

    return schemas.PromptGenerateResponse(
        prompt=prompt,
        reference_article=reference_article,
        reference_clauses=reference_clauses
    )



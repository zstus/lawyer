"""생성 대출약정서 API 라우터"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from .. import crud, schemas, models
from ..services import openai_service

router = APIRouter(prefix="/api/generated", tags=["generated"])


# ===== 생성 약정서 관련 API =====

@router.get("/", response_model=List[schemas.GeneratedAgreementResponse])
def list_generated_agreements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """모든 생성 대출약정서 목록 조회"""
    agreements = crud.get_generated_agreements(db, skip=skip, limit=limit)
    result = []

    for agreement in agreements:
        article_count = len(agreement.articles)
        result.append(schemas.GeneratedAgreementResponse(
            id=agreement.id,
            name=agreement.name,
            description=agreement.description,
            base_agreement_id=agreement.base_agreement_id,
            created_at=agreement.created_at,
            updated_at=agreement.updated_at,
            article_count=article_count
        ))

    return result


@router.post("/", response_model=schemas.GeneratedAgreementResponse)
def create_generated_agreement(
    data: schemas.GeneratedAgreementCreate,
    db: Session = Depends(get_db)
):
    """새 생성 대출약정서 생성"""
    # base_agreement_id가 있으면 존재 여부 확인
    if data.base_agreement_id:
        base = crud.get_agreement(db, data.base_agreement_id)
        if not base:
            raise HTTPException(status_code=404, detail="참조 대출약정서를 찾을 수 없습니다.")

    agreement = crud.create_generated_agreement(db, data)
    return schemas.GeneratedAgreementResponse(
        id=agreement.id,
        name=agreement.name,
        description=agreement.description,
        base_agreement_id=agreement.base_agreement_id,
        created_at=agreement.created_at,
        updated_at=agreement.updated_at,
        article_count=0
    )


@router.get("/{agreement_id}", response_model=schemas.GeneratedAgreementWithArticles)
def get_generated_agreement(agreement_id: int, db: Session = Depends(get_db)):
    """특정 생성 대출약정서 상세 조회 (조 목록 포함)"""
    agreement = crud.get_generated_agreement(db, agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="생성 대출약정서를 찾을 수 없습니다.")

    articles = crud.get_generated_articles(db, agreement_id)

    return schemas.GeneratedAgreementWithArticles(
        id=agreement.id,
        name=agreement.name,
        description=agreement.description,
        base_agreement_id=agreement.base_agreement_id,
        created_at=agreement.created_at,
        updated_at=agreement.updated_at,
        article_count=len(articles),
        articles=[
            schemas.GeneratedArticleResponse(
                id=a.id,
                agreement_id=a.agreement_id,
                article_number=a.article_number,
                article_number_display=a.article_number_display,
                title=a.title,
                order_index=a.order_index,
                ref_agreement_id=a.ref_agreement_id,
                ref_article_id=a.ref_article_id,
                term_sheet_text=a.term_sheet_text,
                created_at=a.created_at,
                clause_count=len(a.clauses)
            )
            for a in articles
        ]
    )


@router.put("/{agreement_id}", response_model=schemas.GeneratedAgreementResponse)
def update_generated_agreement(
    agreement_id: int,
    data: schemas.GeneratedAgreementUpdate,
    db: Session = Depends(get_db)
):
    """생성 대출약정서 수정"""
    agreement = crud.update_generated_agreement(db, agreement_id, data)
    if not agreement:
        raise HTTPException(status_code=404, detail="생성 대출약정서를 찾을 수 없습니다.")

    return schemas.GeneratedAgreementResponse(
        id=agreement.id,
        name=agreement.name,
        description=agreement.description,
        base_agreement_id=agreement.base_agreement_id,
        created_at=agreement.created_at,
        updated_at=agreement.updated_at,
        article_count=len(agreement.articles)
    )


@router.delete("/{agreement_id}")
def delete_generated_agreement(agreement_id: int, db: Session = Depends(get_db)):
    """생성 대출약정서 삭제"""
    if not crud.delete_generated_agreement(db, agreement_id):
        raise HTTPException(status_code=404, detail="생성 대출약정서를 찾을 수 없습니다.")
    return {"message": "삭제되었습니다."}


# ===== 생성 조(Article) 관련 API =====

@router.get("/{agreement_id}/articles", response_model=List[schemas.GeneratedArticleResponse])
def list_generated_articles(agreement_id: int, db: Session = Depends(get_db)):
    """생성 약정서의 조 목록 조회"""
    agreement = crud.get_generated_agreement(db, agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="생성 대출약정서를 찾을 수 없습니다.")

    articles = crud.get_generated_articles(db, agreement_id)

    return [
        schemas.GeneratedArticleResponse(
            id=a.id,
            agreement_id=a.agreement_id,
            article_number=a.article_number,
            article_number_display=a.article_number_display,
            title=a.title,
            order_index=a.order_index,
            ref_agreement_id=a.ref_agreement_id,
            ref_article_id=a.ref_article_id,
            term_sheet_text=a.term_sheet_text,
            created_at=a.created_at,
            clause_count=len(a.clauses)
        )
        for a in articles
    ]


@router.post("/{agreement_id}/articles", response_model=schemas.GeneratedArticleResponse)
def create_generated_article(
    agreement_id: int,
    data: schemas.GeneratedArticleCreate,
    db: Session = Depends(get_db)
):
    """생성 조 추가"""
    agreement = crud.get_generated_agreement(db, agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="생성 대출약정서를 찾을 수 없습니다.")

    article = crud.create_generated_article(db, agreement_id, data)

    return schemas.GeneratedArticleResponse(
        id=article.id,
        agreement_id=article.agreement_id,
        article_number=article.article_number,
        article_number_display=article.article_number_display,
        title=article.title,
        order_index=article.order_index,
        ref_agreement_id=article.ref_agreement_id,
        ref_article_id=article.ref_article_id,
        term_sheet_text=article.term_sheet_text,
        created_at=article.created_at,
        clause_count=len(article.clauses)
    )


@router.get("/{agreement_id}/articles/{article_id}", response_model=schemas.GeneratedArticleWithClauses)
def get_generated_article(agreement_id: int, article_id: int, db: Session = Depends(get_db)):
    """특정 생성 조 상세 조회 (항 목록 포함)"""
    article = crud.get_generated_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="조를 찾을 수 없습니다.")

    clauses = crud.get_generated_clauses(db, article_id)

    return schemas.GeneratedArticleWithClauses(
        id=article.id,
        agreement_id=article.agreement_id,
        article_number=article.article_number,
        article_number_display=article.article_number_display,
        title=article.title,
        order_index=article.order_index,
        ref_agreement_id=article.ref_agreement_id,
        ref_article_id=article.ref_article_id,
        term_sheet_text=article.term_sheet_text,
        created_at=article.created_at,
        clause_count=len(clauses),
        clauses=[
            schemas.GeneratedClauseResponse(
                id=c.id,
                article_id=c.article_id,
                clause_number=c.clause_number,
                clause_number_display=c.clause_number_display,
                title=c.title,
                content=c.content,
                order_index=c.order_index,
                ref_clause_id=c.ref_clause_id,
                created_at=c.created_at,
                updated_at=c.updated_at
            )
            for c in clauses
        ]
    )


@router.put("/{agreement_id}/articles/{article_id}", response_model=schemas.GeneratedArticleResponse)
def update_generated_article(
    agreement_id: int,
    article_id: int,
    data: schemas.GeneratedArticleUpdate,
    db: Session = Depends(get_db)
):
    """생성 조 수정"""
    article = crud.get_generated_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="조를 찾을 수 없습니다.")

    article = crud.update_generated_article(db, article_id, data)

    return schemas.GeneratedArticleResponse(
        id=article.id,
        agreement_id=article.agreement_id,
        article_number=article.article_number,
        article_number_display=article.article_number_display,
        title=article.title,
        order_index=article.order_index,
        ref_agreement_id=article.ref_agreement_id,
        ref_article_id=article.ref_article_id,
        term_sheet_text=article.term_sheet_text,
        created_at=article.created_at,
        clause_count=len(article.clauses)
    )


@router.delete("/{agreement_id}/articles/{article_id}")
def delete_generated_article(agreement_id: int, article_id: int, db: Session = Depends(get_db)):
    """생성 조 삭제"""
    article = crud.get_generated_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="조를 찾을 수 없습니다.")

    if not crud.delete_generated_article(db, article_id):
        raise HTTPException(status_code=500, detail="삭제에 실패했습니다.")

    return {"message": "삭제되었습니다."}


# ===== 생성 항(Clause) 관련 API =====

@router.get("/{agreement_id}/articles/{article_id}/clauses", response_model=List[schemas.GeneratedClauseResponse])
def list_generated_clauses(agreement_id: int, article_id: int, db: Session = Depends(get_db)):
    """생성 조의 항 목록 조회"""
    article = crud.get_generated_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="조를 찾을 수 없습니다.")

    clauses = crud.get_generated_clauses(db, article_id)

    return [
        schemas.GeneratedClauseResponse(
            id=c.id,
            article_id=c.article_id,
            clause_number=c.clause_number,
            clause_number_display=c.clause_number_display,
            title=c.title,
            content=c.content,
            order_index=c.order_index,
            ref_clause_id=c.ref_clause_id,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in clauses
    ]


@router.post("/{agreement_id}/articles/{article_id}/clauses", response_model=schemas.GeneratedClauseResponse)
def create_generated_clause(
    agreement_id: int,
    article_id: int,
    data: schemas.GeneratedClauseCreate,
    db: Session = Depends(get_db)
):
    """생성 항 추가"""
    article = crud.get_generated_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="조를 찾을 수 없습니다.")

    clause = crud.create_generated_clause(db, article_id, data)

    return schemas.GeneratedClauseResponse(
        id=clause.id,
        article_id=clause.article_id,
        clause_number=clause.clause_number,
        clause_number_display=clause.clause_number_display,
        title=clause.title,
        content=clause.content,
        order_index=clause.order_index,
        ref_clause_id=clause.ref_clause_id,
        created_at=clause.created_at,
        updated_at=clause.updated_at
    )


@router.put("/{agreement_id}/articles/{article_id}/clauses/{clause_id}", response_model=schemas.GeneratedClauseResponse)
def update_generated_clause(
    agreement_id: int,
    article_id: int,
    clause_id: int,
    data: schemas.GeneratedClauseUpdate,
    db: Session = Depends(get_db)
):
    """생성 항 수정"""
    clause = crud.get_generated_clause(db, clause_id)
    if not clause or clause.article_id != article_id:
        raise HTTPException(status_code=404, detail="항을 찾을 수 없습니다.")

    # 조-약정서 관계 확인
    article = crud.get_generated_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="항을 찾을 수 없습니다.")

    clause = crud.update_generated_clause(db, clause_id, data)

    return schemas.GeneratedClauseResponse(
        id=clause.id,
        article_id=clause.article_id,
        clause_number=clause.clause_number,
        clause_number_display=clause.clause_number_display,
        title=clause.title,
        content=clause.content,
        order_index=clause.order_index,
        ref_clause_id=clause.ref_clause_id,
        created_at=clause.created_at,
        updated_at=clause.updated_at
    )


@router.delete("/{agreement_id}/articles/{article_id}/clauses/{clause_id}")
def delete_generated_clause(
    agreement_id: int,
    article_id: int,
    clause_id: int,
    db: Session = Depends(get_db)
):
    """생성 항 삭제"""
    clause = crud.get_generated_clause(db, clause_id)
    if not clause or clause.article_id != article_id:
        raise HTTPException(status_code=404, detail="항을 찾을 수 없습니다.")

    # 조-약정서 관계 확인
    article = crud.get_generated_article(db, article_id)
    if not article or article.agreement_id != agreement_id:
        raise HTTPException(status_code=404, detail="항을 찾을 수 없습니다.")

    if not crud.delete_generated_clause(db, clause_id):
        raise HTTPException(status_code=500, detail="삭제에 실패했습니다.")

    return {"message": "삭제되었습니다."}


# ===== AI 결과 저장 API =====

@router.post("/save-ai-result", response_model=schemas.GeneratedArticleResponse)
def save_ai_result(
    data: schemas.SaveAIResultRequest,
    db: Session = Depends(get_db)
):
    """AI 생성 결과를 생성 약정서에 저장"""
    # 생성 약정서 존재 확인
    agreement = crud.get_generated_agreement(db, data.generated_agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="생성 대출약정서를 찾을 수 없습니다.")

    # 조 생성 데이터 구성
    article_data = schemas.GeneratedArticleCreate(
        article_number=data.article_number,
        article_number_display=data.article_number_display,
        title=data.article_title,
        ref_agreement_id=data.ref_agreement_id,
        ref_article_id=data.ref_article_id,
        term_sheet_text=data.term_sheet_text,
        clauses=[
            schemas.GeneratedClauseCreate(
                clause_number=1,
                clause_number_display="1",
                title=data.clause_title or "AI 생성 내용",
                content=data.ai_content,
                order_index=1,
                ref_clause_id=data.ref_clause_id
            )
        ]
    )

    article = crud.create_generated_article(db, data.generated_agreement_id, article_data)

    return schemas.GeneratedArticleResponse(
        id=article.id,
        agreement_id=article.agreement_id,
        article_number=article.article_number,
        article_number_display=article.article_number_display,
        title=article.title,
        order_index=article.order_index,
        ref_agreement_id=article.ref_agreement_id,
        ref_article_id=article.ref_article_id,
        term_sheet_text=article.term_sheet_text,
        created_at=article.created_at,
        clause_count=len(article.clauses)
    )


# ===== ChatGPT API 호출 =====

@router.get("/api-status")
def check_api_status():
    """OpenAI API 키 설정 상태 확인"""
    is_configured = openai_service.check_api_key_configured()
    return {
        "configured": is_configured,
        "message": "API 키가 설정되어 있습니다." if is_configured else "API 키가 설정되지 않았습니다. .env 파일을 확인하세요."
    }


@router.post("/generate-with-chatgpt", response_model=schemas.ChatGPTGenerateResponse)
async def generate_with_chatgpt(
    request: schemas.ChatGPTGenerateRequest,
    db: Session = Depends(get_db)
):
    """ChatGPT를 호출하여 조항 생성 후 저장"""

    # 1. API 키 확인
    if not openai_service.check_api_key_configured():
        raise HTTPException(
            status_code=500,
            detail="OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요."
        )

    # 2. 생성 약정서 존재 확인
    generated_agreement = crud.get_generated_agreement(db, request.generated_agreement_id)
    if not generated_agreement:
        raise HTTPException(status_code=404, detail="생성 대출약정서를 찾을 수 없습니다.")

    # 3. 참조 약정서/조 존재 확인
    agreement = crud.get_agreement(db, request.agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="참조 대출약정서를 찾을 수 없습니다.")

    article = crud.get_article(db, request.article_id)
    if not article or article.agreement_id != request.agreement_id:
        raise HTTPException(status_code=404, detail="참조 조를 찾을 수 없습니다.")

    # 4. 항 목록 조회
    clauses = crud.get_clauses(db, request.article_id)
    if request.clause_id:
        clauses = [c for c in clauses if c.id == request.clause_id]
        if not clauses:
            raise HTTPException(status_code=404, detail="참조 항을 찾을 수 없습니다.")

    # 5. 프롬프트 생성
    reference_article = f"제{article.article_number_display}조 {article.title}"
    clause_structure = []

    for clause in clauses:
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

    prompt = _build_chatgpt_prompt(
        term_sheet_text=request.term_sheet_text,
        agreement_name=agreement.name,
        article_info=reference_article,
        clause_structure=clause_structure
    )

    # 6. ChatGPT 호출
    try:
        ai_content = await openai_service.generate_article_content(prompt)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ChatGPT API 호출 중 오류가 발생했습니다: {str(e)}"
        )

    # 7. skip_save 옵션이 있으면 저장하지 않고 결과만 반환
    if request.skip_save:
        return schemas.ChatGPTGenerateResponse(
            success=True,
            generated_article_id=None,
            generated_agreement_id=request.generated_agreement_id,
            reference_article=reference_article,
            ai_content=ai_content,
            message=f"'{reference_article}' 조항이 생성되었습니다. (저장되지 않음)"
        )

    # 8. 결과 저장
    article_data = schemas.GeneratedArticleCreate(
        article_number=article.article_number,
        article_number_display=article.article_number_display,
        title=article.title,
        ref_agreement_id=request.agreement_id,
        ref_article_id=request.article_id,
        term_sheet_text=request.term_sheet_text,
        clauses=[
            schemas.GeneratedClauseCreate(
                clause_number=1,
                clause_number_display="1",
                title="AI 생성 내용",
                content=ai_content,
                order_index=1,
                ref_clause_id=request.clause_id
            )
        ]
    )

    saved_article = crud.create_generated_article(db, request.generated_agreement_id, article_data)

    return schemas.ChatGPTGenerateResponse(
        success=True,
        generated_article_id=saved_article.id,
        generated_agreement_id=request.generated_agreement_id,
        reference_article=reference_article,
        ai_content=ai_content,
        message=f"'{reference_article}' 조항이 생성되어 저장되었습니다."
    )


def _build_chatgpt_prompt(
    term_sheet_text: str,
    agreement_name: str,
    article_info: str,
    clause_structure: list
) -> str:
    """대출약정서 조항 생성을 위한 프롬프트 구성"""

    clause_examples = []
    for clause in clause_structure:
        example = f"""### 제{clause['number']}항 {clause['title']}
{clause['content']}"""
        clause_examples.append(example)

    clause_structure_text = "\n\n".join(clause_examples)

    prompt = f"""당신은 대출약정서 작성 전문가입니다. 아래 Term Sheet 정보를 바탕으로 대출약정서의 조항을 작성해주세요.

## 작성 지침

1. **참조 문서**: "{agreement_name}"
2. **참조 조항**: {article_info}
3. 참조 조항의 **구조와 형식**을 그대로 따라 작성하되, Term Sheet의 정보를 반영하세요.
4. 법률 문서 특유의 정확하고 명확한 문체를 유지하세요.
5. 조항 번호, 항 번호 체계를 유지하세요.

---

## Term Sheet 정보

{term_sheet_text}

---

## 참조 조항 구조 (이 구조를 따라 작성)

{clause_structure_text}

---

## 작성 요청

위의 Term Sheet 정보를 반영하여, 참조 조항과 동일한 구조로 새로운 "{article_info}" 조항을 작성해주세요.

- 각 항의 제목과 구조는 참조 조항을 따르세요.
- 구체적인 수치, 날짜, 조건 등은 Term Sheet 정보를 사용하세요.
- Term Sheet에 없는 정보는 "[확인 필요]"로 표시하세요.
"""

    return prompt

"""생성 대출약정서 API 라우터"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timezone

from ..database import get_db
from .. import crud, schemas, models
from ..services import openai_service
from ..services.prompt_service import build_generation_prompt
from ..parser import parse_ai_generated_clauses, extract_plain_text_from_ai_response

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
                score=c.score,
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
            score=c.score,
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
        score=clause.score,
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
        score=clause.score,
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

    # 다중 항 모드: AI 응답을 파싱하여 여러 항 생성
    if data.multi_clause_mode:
        parsed_clauses = parse_ai_generated_clauses(data.ai_content)
        clauses_data = [
            schemas.GeneratedClauseCreate(
                clause_number=clause['clause_number'],
                clause_number_display=clause['clause_number_display'],
                title=clause['title'] or f"제{clause['clause_number']}항",
                content=clause['content'],
                order_index=idx + 1,
                ref_clause_id=None,
                score=data.score  # 담당자 평가 점수
            )
            for idx, clause in enumerate(parsed_clauses)
        ]
    else:
        # 단일 항 생성 — 2단계에서 선택한 항 번호 사용 (없으면 1)
        clause_num = data.clause_number if data.clause_number else 1
        clause_num_display = data.clause_number_display if data.clause_number_display else str(clause_num)
        # JSON 형식 응답에서 순수 텍스트 추출 (공통 함수)
        plain_text = extract_plain_text_from_ai_response(data.ai_content)
        clauses_data = [
            schemas.GeneratedClauseCreate(
                clause_number=clause_num,
                clause_number_display=clause_num_display,
                title=data.clause_title or "AI 생성 내용",
                content=plain_text,
                order_index=1,
                ref_clause_id=data.ref_clause_id,
                score=data.score  # 담당자 평가 점수
            )
        ]

    # 기존 조에 항 추가 vs 새 조 생성 분기
    if data.target_article_id:
        # ── 기존 조에 항 추가 ──
        target_article = crud.get_generated_article(db, data.target_article_id)
        if not target_article or target_article.agreement_id != data.generated_agreement_id:
            raise HTTPException(status_code=404, detail="대상 조를 찾을 수 없습니다.")

        existing_clauses = crud.get_generated_clauses(db, data.target_article_id)

        if data.multi_clause_mode:
            # 기존 항 전체 삭제 후 새 항들 추가
            for c in existing_clauses:
                db.delete(c)
            db.flush()
            for cd in clauses_data:
                db.add(models.GeneratedClause(
                    article_id=data.target_article_id,
                    clause_number=cd.clause_number,
                    clause_number_display=cd.clause_number_display,
                    title=cd.title,
                    content=cd.content,
                    order_index=cd.order_index,
                    ref_clause_id=cd.ref_clause_id,
                    score=cd.score
                ))
        else:
            # 동일 항 번호가 있으면 삭제 후 새 항 추가
            cd = clauses_data[0]
            for c in existing_clauses:
                if c.clause_number_display == cd.clause_number_display:
                    db.delete(c)
            db.flush()
            max_order = db.query(func.max(models.GeneratedClause.order_index))\
                          .filter(models.GeneratedClause.article_id == data.target_article_id)\
                          .scalar() or 0
            db.add(models.GeneratedClause(
                article_id=data.target_article_id,
                clause_number=cd.clause_number,
                clause_number_display=cd.clause_number_display,
                title=cd.title,
                content=cd.content,
                order_index=max_order + 1,
                ref_clause_id=cd.ref_clause_id,
                score=cd.score
            ))

        db.commit()
        db.refresh(target_article)
        article = target_article

    else:
        # ── 새 조 생성 ──
        article_data = schemas.GeneratedArticleCreate(
            article_number=data.article_number,
            article_number_display=data.article_number_display,
            title=data.article_title,
            ref_agreement_id=data.ref_agreement_id,
            ref_article_id=data.ref_article_id,
            term_sheet_text=data.term_sheet_text,
            clauses=clauses_data
        )
        article = crud.create_generated_article(db, data.generated_agreement_id, article_data)

    # 로그 점수 업데이트 (log_id와 score가 모두 있을 때)
    if data.log_id and data.score and 1 <= data.score <= 5:
        log = db.query(models.AIGenerationLog).filter(
            models.AIGenerationLog.id == data.log_id
        ).first()
        if log:
            log.score = data.score
            db.commit()

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
    http_request: Request,
    request: schemas.ChatGPTGenerateRequest,
    db: Session = Depends(get_db)
):
    """ChatGPT를 호출하여 조항 생성 후 저장"""

    # 세션에서 작성자 확인
    username = http_request.session.get("username", "unknown")

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

    # 4. 항 정보 조회 (로그용)
    ref_clause_title = None
    clauses = crud.get_clauses(db, request.article_id)
    if request.clause_id:
        clauses = [c for c in clauses if c.id == request.clause_id]
        if not clauses:
            raise HTTPException(status_code=404, detail="참조 항을 찾을 수 없습니다.")
        ref_clause_title = clauses[0].title if clauses else None

    # 5. 프롬프트 결정 (사용자 수정본 우선, 없으면 자동 생성)
    reference_article = f"제{article.article_number_display}조 {article.title}"

    if request.custom_prompt:
        prompt = request.custom_prompt
    else:
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
        prompt = build_generation_prompt(
            term_sheet_text=request.term_sheet_text,
            agreement_name=agreement.name,
            clause_structure=clause_structure
        )

    # 6. ChatGPT 호출
    called_at = datetime.now(timezone.utc)
    try:
        ai_content = await openai_service.generate_article_content(prompt)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ChatGPT API 호출 중 오류가 발생했습니다: {str(e)}"
        )

    # 7. AI 호출 로그 저장
    log = models.AIGenerationLog(
        username=username,
        generated_agreement_id=request.generated_agreement_id,
        ref_agreement_id=request.agreement_id,
        ref_article_id=request.article_id,
        ref_clause_id=request.clause_id,
        ref_agreement_name=agreement.name,
        ref_article_title=article.title,
        ref_clause_title=ref_clause_title,
        called_at=called_at,
        used_prompt=prompt,
        ai_response=ai_content,
        score=None
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    log_id = log.id

    # 8. skip_save 옵션이 있으면 저장하지 않고 결과만 반환
    if request.skip_save:
        return schemas.ChatGPTGenerateResponse(
            success=True,
            generated_article_id=None,
            generated_agreement_id=request.generated_agreement_id,
            reference_article=reference_article,
            ai_content=ai_content,
            message=f"'{reference_article}' 조항이 생성되었습니다. (저장되지 않음)",
            log_id=log_id
        )

    # 9. 결과 저장 (JSON → 순수 텍스트 변환 후 저장)
    plain_text = extract_plain_text_from_ai_response(ai_content)
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
                content=plain_text,
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
        message=f"'{reference_article}' 조항이 생성되어 저장되었습니다.",
        log_id=log_id
    )


@router.put("/logs/{log_id}/score")
def update_log_score(
    log_id: int,
    data: schemas.AILogScoreUpdate,
    db: Session = Depends(get_db)
):
    """AI 호출 로그에 점수 업데이트"""
    if not (1 <= data.score <= 5):
        raise HTTPException(status_code=400, detail="점수는 1~5 사이여야 합니다.")

    log = db.query(models.AIGenerationLog).filter(models.AIGenerationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="로그를 찾을 수 없습니다.")

    log.score = data.score
    db.commit()
    return {"message": "점수가 저장되었습니다.", "log_id": log_id, "score": data.score}



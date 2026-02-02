"""FastAPI 메인 애플리케이션"""
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from .database import init_db
from .routers import agreements, generated

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# FastAPI 앱 생성
app = FastAPI(
    title="대출약정서 관리 시스템",
    description="대출약정서 DOCX 파일을 파싱하여 조/항 단위로 관리하는 시스템",
    version="1.0.0"
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# API 라우터 등록
app.include_router(agreements.router)
app.include_router(generated.router)


# ===== 웹 페이지 라우트 =====

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지 - 기준약정서 목록"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/reference/{agreement_id}", response_class=HTMLResponse)
async def reference_detail(request: Request, agreement_id: int):
    """기준약정서 상세 페이지 - 조/항 아코디언"""
    return templates.TemplateResponse(
        "reference_detail.html",
        {"request": request, "agreement_id": agreement_id}
    )


@app.get("/work", response_class=HTMLResponse)
async def work_list(request: Request):
    """작업약정서 목록 페이지"""
    return templates.TemplateResponse("work_list.html", {"request": request})


@app.get("/work/{agreement_id}", response_class=HTMLResponse)
async def work_detail(request: Request, agreement_id: int):
    """작업약정서 상세 페이지 - 조/항 아코디언"""
    return templates.TemplateResponse(
        "work_detail.html",
        {"request": request, "agreement_id": agreement_id}
    )


@app.get("/work/{agreement_id}/add-article", response_class=HTMLResponse)
async def add_article(request: Request, agreement_id: int):
    """조항추가 페이지"""
    return templates.TemplateResponse(
        "add_article.html",
        {"request": request, "agreement_id": agreement_id}
    )


# ===== 기존 라우트 (호환성 유지) =====

@app.get("/agreement/{agreement_id}", response_class=HTMLResponse)
async def agreement_detail(request: Request, agreement_id: int):
    """약정서 상세 페이지 - 조 목록 (기존 호환)"""
    return templates.TemplateResponse(
        "agreement.html",
        {"request": request, "agreement_id": agreement_id}
    )


@app.get("/agreement/{agreement_id}/article/{article_id}", response_class=HTMLResponse)
async def article_detail(request: Request, agreement_id: int, article_id: int):
    """조 상세 페이지 - 항 목록 (기존 호환)"""
    return templates.TemplateResponse(
        "article.html",
        {"request": request, "agreement_id": agreement_id, "article_id": article_id}
    )


@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """대출약정서 항목 생성 페이지"""
    return templates.TemplateResponse("generate.html", {"request": request})


# ===== 생성 대출약정서 웹 페이지 라우트 =====

@app.get("/generated", response_class=HTMLResponse)
async def generated_list(request: Request):
    """생성 대출약정서 목록 페이지"""
    return templates.TemplateResponse("generated_list.html", {"request": request})


@app.get("/generated/{agreement_id}", response_class=HTMLResponse)
async def generated_detail(request: Request, agreement_id: int):
    """생성 대출약정서 상세 페이지 - 조 목록"""
    return templates.TemplateResponse(
        "generated_detail.html",
        {"request": request, "agreement_id": agreement_id}
    )


@app.get("/generated/{agreement_id}/article/{article_id}", response_class=HTMLResponse)
async def generated_article_detail(request: Request, agreement_id: int, article_id: int):
    """생성 조 상세 페이지 - 항 편집"""
    return templates.TemplateResponse(
        "generated_article.html",
        {"request": request, "agreement_id": agreement_id, "article_id": article_id}
    )


# ===== 이벤트 핸들러 =====

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 데이터베이스 초기화"""
    init_db()


# ===== 실행 =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

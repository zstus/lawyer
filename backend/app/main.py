"""FastAPI 메인 애플리케이션"""
import os
import hashlib
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from .database import init_db, SessionLocal
from .routers import agreements, generated
from . import models

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 시크릿 키 (세션 쿠키 서명용)
SECRET_KEY = os.environ.get("SECRET_KEY", "lawyer-system-secret-key-2024-change-in-production")

# FastAPI 앱 생성
app = FastAPI(
    title="대출약정서 관리 시스템",
    description="대출약정서 DOCX 파일을 파싱하여 조/항 단위로 관리하는 시스템",
    version="1.0.0"
)

# 세션 미들웨어 추가 (쿠키 기반 서명 세션)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# API 라우터 등록
app.include_router(agreements.router)
app.include_router(generated.router)


# ===== 인증 유틸리티 =====

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증 (salt:hash 형식)"""
    try:
        salt, hash_val = hashed_password.split(":", 1)
        expected = hashlib.sha256(f"{salt}{plain_password}".encode()).hexdigest()
        return expected == hash_val
    except Exception:
        return False


def get_username(request: Request):
    """세션에서 사용자명 반환 (미로그인 시 None)"""
    return request.session.get("username")


# ===== 로그인 / 로그아웃 =====

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지"""
    if get_username(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """로그인 처리"""
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user and verify_password(password, user.hashed_password):
            request.session["username"] = username
            return RedirectResponse(url="/", status_code=302)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "아이디 또는 비밀번호가 올바르지 않습니다."}
        )
    finally:
        db.close()


@app.get("/logout")
async def logout(request: Request):
    """로그아웃"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# ===== 웹 페이지 라우트 =====

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지 - 기준약정서 목록"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request, "username": username})


@app.get("/reference/{agreement_id}", response_class=HTMLResponse)
async def reference_detail(request: Request, agreement_id: int):
    """기준약정서 상세 페이지 - 조/항 아코디언"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "reference_detail.html",
        {"request": request, "agreement_id": agreement_id, "username": username}
    )


@app.get("/work", response_class=HTMLResponse)
async def work_list(request: Request):
    """작업약정서 목록 페이지"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("work_list.html", {"request": request, "username": username})


@app.get("/work/{agreement_id}", response_class=HTMLResponse)
async def work_detail(request: Request, agreement_id: int):
    """작업약정서 상세 페이지 - 조/항 아코디언"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "work_detail.html",
        {"request": request, "agreement_id": agreement_id, "username": username}
    )


@app.get("/work/{agreement_id}/add-article", response_class=HTMLResponse)
async def add_article(request: Request, agreement_id: int):
    """조항추가 페이지"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "add_article.html",
        {"request": request, "agreement_id": agreement_id, "username": username}
    )


# ===== 기존 라우트 (호환성 유지) =====

@app.get("/agreement/{agreement_id}", response_class=HTMLResponse)
async def agreement_detail(request: Request, agreement_id: int):
    """약정서 상세 페이지 - 조 목록 (기존 호환)"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "agreement.html",
        {"request": request, "agreement_id": agreement_id, "username": username}
    )


@app.get("/agreement/{agreement_id}/article/{article_id}", response_class=HTMLResponse)
async def article_detail(request: Request, agreement_id: int, article_id: int):
    """조 상세 페이지 - 항 목록 (기존 호환)"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "article.html",
        {"request": request, "agreement_id": agreement_id, "article_id": article_id, "username": username}
    )


@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """대출약정서 항목 생성 페이지"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("generate.html", {"request": request, "username": username})


# ===== 생성 대출약정서 웹 페이지 라우트 =====

@app.get("/generated", response_class=HTMLResponse)
async def generated_list(request: Request):
    """생성 대출약정서 목록 페이지"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("generated_list.html", {"request": request, "username": username})


@app.get("/generated/{agreement_id}", response_class=HTMLResponse)
async def generated_detail(request: Request, agreement_id: int):
    """생성 대출약정서 상세 페이지 - 조 목록"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "generated_detail.html",
        {"request": request, "agreement_id": agreement_id, "username": username}
    )


@app.get("/generated/{agreement_id}/article/{article_id}", response_class=HTMLResponse)
async def generated_article_detail(request: Request, agreement_id: int, article_id: int):
    """생성 조 상세 페이지 - 항 편집"""
    username = get_username(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "generated_article.html",
        {"request": request, "agreement_id": agreement_id, "article_id": article_id, "username": username}
    )


# ===== 이벤트 핸들러 =====

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 데이터베이스 초기화 및 기본 사용자 생성"""
    init_db()


# ===== 실행 =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

# Claude Code 작업 지침

## 프로젝트 접근 환경

현재 프로젝트는 **NAS 공유폴더를 네트워크 드라이브로 연결**하여 접근하는 환경입니다.

- 경로: `\\synologyNAS\docker\ubt_lawyer\lawyer`
- 서버(NAS)에서 Docker 컨테이너로 FastAPI 애플리케이션이 실행 중
- Claude Code는 소스 파일을 읽고 수정할 수 있지만, **서버에서 명령어를 직접 실행할 수 없음**

## 작업 원칙

### 소스 수정만 직접 진행
- 파일 읽기, 편집, 생성은 Claude Code가 직접 수행
- 수정한 파일은 공유폴더를 통해 즉시 서버에 반영됨

### 명령어 실행은 사용자에게 안내
아래 작업은 **사용자가 서버(NAS) 또는 Docker 컨테이너에 직접 접속하여 실행**해야 합니다:

- 패키지/모듈 설치 (`pip install ...`)
- 서버 재시작 (`docker restart ...` 또는 `uvicorn` 재기동)
- 데이터베이스 마이그레이션 스크립트 실행
- 환경변수 설정

Claude Code는 실행이 필요한 경우 **구체적인 명령어를 안내**하고, 사용자가 직접 실행하도록 합니다.

## 안내 방식 예시

```bash
# 서버에서 실행해주세요:
docker exec -it <컨테이너명> pip install <패키지명>

# 또는 컨테이너 재시작:
docker restart <컨테이너명>
```

---

## 프로젝트 구조 및 모듈 설명

### 기술 스택
- **Backend**: FastAPI + Uvicorn
- **ORM**: SQLAlchemy + SQLite (`backend/data/loan_agreements.db`)
- **Template**: Jinja2
- **AI**: OpenAI API (gpt-4o)
- **인증**: 세션 쿠키 기반 (username/password, SHA-256 해시)
- **컨테이너**: Docker (NAS에서 운영)

---

### 디렉토리 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 앱 + 웹 라우트 (페이지 반환)
│   ├── database.py          # DB 연결, 초기화, 마이그레이션
│   ├── models.py            # SQLAlchemy ORM 모델 (테이블 정의)
│   ├── schemas.py           # Pydantic 스키마 (요청/응답 검증)
│   ├── crud.py              # DB CRUD 함수 모음
│   ├── parser.py            # DOCX 파서 + AI 응답 파서
│   ├── routers/
│   │   ├── agreements.py    # 기준약정서 REST API
│   │   └── generated.py     # 작업약정서 REST API + AI 생성
│   └── services/
│       ├── openai_service.py # ChatGPT API 호출
│       └── prompt_service.py # 프롬프트 생성 로직
├── templates/               # Jinja2 HTML 템플릿
├── static/
│   └── style.css            # 전체 CSS
└── data/
    └── loan_agreements.db   # SQLite DB 파일
```

---

### 핵심 모듈 상세 설명

#### `app/main.py` — FastAPI 앱 + 웹 라우트
- FastAPI 앱 생성, 세션 미들웨어, 정적파일/템플릿 마운트
- **인증 함수**: `verify_password()`, `get_username()`
- **웹 페이지 라우트** (HTML 반환):
  - `/login`, `/logout`
  - `/` — 기준약정서 목록
  - `/reference/{id}` — 기준약정서 상세
  - `/work` — 작업약정서 목록
  - `/work/{id}` — 작업약정서 상세
  - `/work/{id}/add-article` — 조항추가 4단계 페이지
  - `/generate` — 독립 프롬프트 생성 페이지
- DB 초기화는 `@app.on_event("startup")`에서 호출

---

#### `app/database.py` — DB 연결 및 초기화
- `get_db()` — DB 세션 DI (Dependency Injection)
- `init_db()` — 테이블 생성 + 마이그레이션 + 기본 유저 생성 호출
- `_migrate_columns()` — 기존 DB에 누락된 컬럼 추가 (ALTER TABLE)
  - 현재: `generated_clauses.score` 컬럼 추가
  - 새 컬럼 추가 시 여기에 등록
- `_create_default_user()` — 기본 계정 생성
  - insu/oldman, user1/user1, user2/user2, user3/user3

---

#### `app/models.py` — SQLAlchemy ORM 모델
**기준약정서 모델:**
- `User` — 사용자 (id, username, hashed_password)
- `LoanAgreement` — 기준 대출약정서 (id, name, file_name, description)
- `Article` — 조 (agreement_id FK, article_number, article_number_display, title, order_index)
- `Clause` — 항 (article_id FK, clause_number, clause_number_display, title, content[JSON], order_index)

**작업약정서 모델:**
- `GeneratedAgreement` — 작업약정서 (id, name, description, base_agreement_id)
- `GeneratedArticle` — 생성 조 (agreement_id FK, ref_agreement_id, ref_article_id, term_sheet_text)
- `GeneratedClause` — 생성 항 (article_id FK, content[Text], ref_clause_id, score[1-5])

**로그 모델:**
- `AIGenerationLog` — AI 호출 로그 (username, used_prompt, ai_response, score, called_at)

---

#### `app/schemas.py` — Pydantic 스키마
- 요청/응답 데이터 검증 및 직렬화
- 주요 스키마:
  - `ParsedDocument`, `ParsedArticle`, `ParsedClause` — DOCX 파서 출력
  - `SaveAIResultRequest` — AI 결과 저장 요청 (`target_article_id` 포함)
  - `ChatGPTGenerateRequest/Response` — ChatGPT 호출
  - `GeneratedArticleCreate`, `GeneratedClauseCreate` — 생성 조/항 추가
  - `AILogScoreUpdate` — AI 로그 점수 수정

---

#### `app/crud.py` — DB CRUD 함수
- 각 모델별 Create/Read/Update/Delete 함수 정의
- **정렬 주의**: `get_generated_clauses()`는 `clause_number` 기준 정렬
  (order_index는 삽입 순서라 개별 추가 시 순서가 틀릴 수 있음)
- 주요 함수:
  - `create_agreement()` — DOCX 파싱 결과를 DB에 저장
  - `create_generated_article()` — 조 + 항 일괄 추가 (order_index 자동)
  - `create_generated_clause()` — 항 단독 추가
  - `delete_generated_article()` — 조 삭제 (CASCADE로 항도 삭제)

---

#### `app/parser.py` — DOCX 파서 + AI 응답 파서
**DOCX 파싱:**
- `parse_docx_bytes(file_content, file_name)` — 업로드된 DOCX 바이트 파싱
- 패턴: `제N조`, `제N조의M`, `제N항` 정규식으로 구조 추출
- 조에 항이 없으면 "본문" 항 자동 생성
- 부록/별첨 구간에서 파싱 종료

**AI 응답 파싱:**
- `parse_ai_generated_clauses(ai_content)` — AI 응답에서 항 배열 추출
  1. JSON 블록 (` ```json ``` `) 파싱 우선
  2. 마크다운 패턴 폴백
  3. 전체를 단일 항으로 처리 (최종 폴백)
- `extract_plain_text_from_ai_response(ai_content)` — JSON 응답에서 평문 추출

---

#### `app/routers/agreements.py` — 기준약정서 API
- `POST /api/agreements/upload` — DOCX 업로드 및 파싱 저장
- `GET /api/agreements/` — 목록
- `GET /api/agreements/{id}` — 상세 (조 포함)
- `GET /api/agreements/{id}/articles/{article_id}` — 조 상세 (항 포함)
- `POST /api/agreements/generate-prompt` — 프롬프트 생성 (Step 3용)
- `DELETE /api/agreements/{id}` — 삭제

---

#### `app/routers/generated.py` — 작업약정서 API + AI 생성 ★ 핵심
- **약정서 CRUD**: `/api/generated/` (GET, POST, PUT, DELETE)
- **조 CRUD**: `/api/generated/{id}/articles/` (GET, POST, PUT, DELETE)
- **항 CRUD**: `/api/generated/{id}/articles/{aid}/clauses/` (GET, POST, PUT, DELETE)
- `POST /api/generated/generate-with-chatgpt` — ChatGPT 호출 + 로그 저장 + 결과 저장
- `POST /api/generated/save-ai-result` — AI 결과 저장
  - `target_article_id` 있으면 기존 조에 항 추가 (중복 조 방지)
  - `multi_clause_mode`: True면 기존 항 전체 교체, False면 동일 항만 교체
- `PUT /api/generated/logs/{log_id}/score` — AI 로그 점수 업데이트

---

#### `app/services/openai_service.py` — ChatGPT API 연동
- `generate_article_content(prompt)` — ChatGPT 비동기 호출
  - temperature: 0.3 (낮은 창의성, 일관된 법률 문서 생성)
  - max_tokens: gpt-4o는 16,000, 기타 4,096
- `check_api_key_configured()` — API 키 설정 여부 확인
- 모델 설정: `.env`의 `OPENAI_MODEL` (기본값: `gpt-4o`)

---

#### `app/services/prompt_service.py` — 프롬프트 생성
- `build_generation_prompt(term_sheet_text, agreement_name, clause_structure)` — 프롬프트 생성
- **절대 규칙 (AI에게 전달)**:
  1. 출력 JSON 배열 길이 = 입력 배열 길이 (추가/삭제 금지)
  2. clause_number, clause_title은 입력과 동일 유지
  3. content만 Term Sheet 값으로 치환
  4. 없는 값은 `[확인 필요]`로 표시
  5. 마크다운 사용 금지, 순수 JSON만 출력

---

### 템플릿 파일 (templates/)

| 파일 | 역할 |
|------|------|
| `base.html` | 공통 레이아웃 (네비게이션, 로그인 상태) |
| `login.html` | 로그인 페이지 |
| `index.html` | 기준약정서 목록 + DOCX 업로드 |
| `reference_detail.html` | 기준약정서 상세 (조/항 아코디언) |
| `work_list.html` | 작업약정서 목록 + 새 약정서 생성 |
| `work_detail.html` | 작업약정서 상세 (조/항 아코디언, 삭제) |
| `add_article.html` | 조항추가 4단계 워크플로우 ★ 핵심 |
| `generate.html` | 독립 프롬프트 생성 페이지 |
| `generated_list.html` | 생성 약정서 목록 (레거시) |
| `generated_detail.html` | 생성 약정서 상세 (레거시) |
| `generated_article.html` | 생성 조 상세 + 항 편집 (레거시) |

---

### 주요 데이터 흐름

```
DOCX 업로드
  → parser.py (parse_docx_bytes)
  → crud.create_agreement()
  → LoanAgreement + Article + Clause DB 저장

조항추가 (add_article.html 4단계)
  1. Term Sheet 입력
  2. 기준약정서 / 조 / 항 선택
  3. [프롬프트 생성] → /api/agreements/generate-prompt
       → prompt_service.build_generation_prompt()
  4. [생성형AI 호출] → /api/generated/generate-with-chatgpt
       → openai_service.generate_article_content()
       → parser.parse_ai_generated_clauses() (JSON 파싱)
       → AIGenerationLog 저장
  5. [생성된조항추가] → /api/generated/save-ai-result
       → target_article_id 있으면 기존 조에 항 추가
       → GeneratedArticle + GeneratedClause DB 저장
```

---

### DB 스키마 변경 시 주의사항
새 컬럼 추가 시 `create_all()`은 기존 테이블을 변경하지 않음.
**반드시 `database.py`의 `_migrate_columns()`에 ALTER TABLE 구문 추가 필요.**

```python
def _migrate_columns():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(테이블명)"))
        columns = [row[1] for row in result.fetchall()]
        if "새컬럼명" not in columns:
            conn.execute(text("ALTER TABLE 테이블명 ADD COLUMN 새컬럼명 타입"))
            conn.commit()
```

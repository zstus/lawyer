# 대출약정서 관리 시스템

대출약정서 DOCX 파일을 파싱하여 조/항 단위로 관리하고, Term Sheet 정보와 AI(ChatGPT)를 활용하여 새로운 대출약정서를 생성하는 시스템.

## 비즈니스 개요

### 시스템 목적
금융권에서 사용하는 대출약정서는 복잡한 법률 문서로, 새로운 대출 건마다 유사한 구조의 약정서를 작성해야 합니다. 이 시스템은:
1. 기존 대출약정서(DOCX)를 파싱하여 **기준약정서**로 등록
2. Term Sheet 정보를 기반으로 기준약정서의 구조를 참조하여 **새로운 조항 생성**
3. 생성된 조항들을 모아 **작업약정서**로 관리

### 핵심 기능
- **기준약정서 관리**: DOCX 업로드 → 조/항 구조 파싱 → DB 저장
- **작업약정서 생성**: 새 약정서 생성 → 조항 추가 → AI 생성 → 편집/저장
- **AI 조항 생성**: Term Sheet + 참조 조항 → ChatGPT 프롬프트 → 자동 생성

---

## 비즈니스 워크플로우

### 1. 기준약정서 등록 (Reference Agreement)

```
DOCX 파일 업로드 → 조/항 구조 자동 파싱 → 기준약정서로 저장
```

- 관리자가 기존 대출약정서 DOCX 파일을 업로드
- 시스템이 "제N조", "제N항" 패턴을 인식하여 계층 구조로 분해
- 등록된 기준약정서는 새 약정서 작성 시 참조용 템플릿으로 활용

### 2. 작업약정서 생성 (Working Agreement)

```
새 작업약정서 생성 → 조항추가 반복 → 완성된 약정서
```

**작업약정서 목록 페이지** (`/work`)
- 작업 중인 약정서 목록 표시
- 새 작업약정서 생성 (이름 입력)

**작업약정서 상세 페이지** (`/work/{id}`)
- 현재 추가된 조/항 목록 (아코디언 UI)
- [조항추가] 버튼으로 새 조항 생성

### 3. 조항추가 워크플로우 (Add Article)

`/work/{id}/add-article` 페이지에서 4단계로 진행:

```
┌─────────────────────────────────────────────────────────────┐
│ 1단계: Term Sheet 정보 입력                                   │
│   - 대출금액, 대출기간, 이자율, 상환방식 등 입력              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 2단계: 참조 대출약정서 선택                                   │
│   - 기준약정서 선택 (드롭다운)                                │
│   - 조(Article) 선택 (드롭다운)                               │
│   - 항(Clause) 선택 (드롭다운, 선택사항)                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
                     [프롬프트 생성] 버튼
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 3단계: 생성된 프롬프트                                        │
│   - AI용 프롬프트 표시 (복사 가능)                            │
│   - [생성형AI 호출] 버튼                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
                   ChatGPT API 호출
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 4단계: 생성된 조항                                            │
│   - AI가 생성한 조항 내용 표시                                │
│   - 조번호, 조제목, 항제목 입력 (참조 조항 기본값)             │
│   - [생성된조항추가] 버튼 → 작업약정서에 저장                  │
└─────────────────────────────────────────────────────────────┘
```

#### 다중 항 저장 모드

2단계에서 항 선택 여부에 따라 동작이 달라집니다:

| 선택 상태 | 프롬프트에 전달 | 4단계 입력 필드 | 저장 동작 |
|----------|----------------|----------------|----------|
| 조+항 선택 | 해당 항 1개 | 항제목 입력 가능 | 단일 항 저장 |
| 조만 선택 | 해당 조의 모든 항 | 항제목 disabled | AI 응답 파싱하여 다중 항 저장 |

- **조 이름(제목)**: 기준약정서의 조 제목을 그대로 사용
- **다중 항 모드**: AI가 JSON 배열로 여러 항을 반환하면 각각 개별 항으로 저장

### 4. 프롬프트 생성 로직

프롬프트는 `services/prompt_service.py`에서 통합 관리됩니다.

#### 핵심 원칙
- **원문 구조 최대 유지**: 기존 대출약정서의 문장 구조, 표현, 형식을 그대로 유지
- **값만 치환**: Term Sheet의 구체적인 값(금액, 날짜, 당사자명, 조건 등)만 대체
- **1:1 대응**: 입력 항 개수와 출력 항 개수가 반드시 동일

#### 입출력 형식
- **입력**: 참조 항들을 JSON 배열로 전달
- **출력**: AI가 JSON 배열로 응답 (마크다운 사용 금지)

```json
// 입력 (참조 항)
[
  {"clause_number": 1, "clause_title": "항제목", "content": "원문 내용"},
  {"clause_number": 2, "clause_title": "항제목", "content": "원문 내용"}
]

// 출력 (AI 생성)
[
  {"clause_number": 1, "clause_title": "항제목", "content": "Term Sheet 값 대체된 내용"},
  {"clause_number": 2, "clause_title": "항제목", "content": "Term Sheet 값 대체된 내용"}
]
```

#### 프롬프트 절대 규칙
1. 출력 JSON 배열 길이 = 입력 배열 길이 (항 추가/삭제 금지)
2. clause_number, clause_title은 입력과 동일하게 유지
3. content만 Term Sheet 값으로 치환
4. Term Sheet에 없는 값은 `[확인 필요]`로 표시 (해당 값만, 문장 전체 X)

---

## 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 및 웹 라우트
│   ├── database.py          # SQLite 데이터베이스 설정
│   ├── models.py            # SQLAlchemy 모델
│   ├── schemas.py           # Pydantic 스키마
│   ├── crud.py              # CRUD 작업
│   ├── parser.py            # DOCX 파서 (조/항 구조 추출)
│   ├── routers/
│   │   ├── agreements.py    # 기준약정서 API
│   │   └── generated.py     # 작업약정서 API
│   └── services/
│       ├── openai_service.py # ChatGPT API 연동
│       └── prompt_service.py # 프롬프트 생성 (통합 모듈)
├── templates/
│   ├── base.html            # 기본 레이아웃 (네비게이션 포함)
│   ├── index.html           # 기준약정서 목록
│   ├── reference_detail.html # 기준약정서 상세 (조/항 아코디언)
│   ├── work_list.html       # 작업약정서 목록
│   ├── work_detail.html     # 작업약정서 상세 (조/항 아코디언)
│   ├── add_article.html     # 조항추가 4단계 워크플로우
│   ├── generate.html        # 프롬프트 생성 (독립 페이지)
│   ├── generated_list.html  # 생성 약정서 목록 (레거시)
│   ├── generated_detail.html # 생성 약정서 상세 (레거시)
│   ├── agreement.html       # 약정서 상세 (레거시)
│   └── article.html         # 조 상세 (레거시)
├── static/
│   └── style.css            # 스타일시트
├── data/
│   └── agreements.db        # SQLite 데이터베이스
├── .env                     # 환경변수 (OPENAI_API_KEY)
├── requirements.txt
└── CLAUDE.md
```

---

## 데이터 모델

### 기준약정서 모델

#### LoanAgreement (기준 대출약정서)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | 기본 키 |
| name | String | 약정서 이름 |
| file_name | String | 원본 파일명 |
| description | String | 설명 |
| created_at | DateTime | 생성일시 |
| updated_at | DateTime | 수정일시 |

#### Article (조)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | 기본 키 |
| agreement_id | Integer | 약정서 FK |
| article_number | Integer | 조 번호 |
| article_number_display | String | 표시용 ("4", "4의2") |
| title | String | 조 제목 |
| order_index | Integer | 정렬 순서 |

#### Clause (항)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | 기본 키 |
| article_id | Integer | 조 FK |
| clause_number | Integer | 항 번호 |
| clause_number_display | String | 표시용 |
| title | String | 항 제목 |
| content | JSON | 항 내용 |
| order_index | Integer | 정렬 순서 |

### 작업약정서 모델

#### GeneratedAgreement (작업 대출약정서)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | 기본 키 |
| name | String | 약정서 이름 |
| description | String | 설명 |
| base_agreement_id | Integer | 참조 기준약정서 FK (선택) |
| created_at | DateTime | 생성일시 |
| updated_at | DateTime | 수정일시 |

#### GeneratedArticle (생성 조)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | 기본 키 |
| agreement_id | Integer | 작업약정서 FK |
| article_number | Integer | 조 번호 |
| article_number_display | String | 표시용 |
| title | String | 조 제목 |
| order_index | Integer | 정렬 순서 |
| ref_agreement_id | Integer | 참조한 기준약정서 ID |
| ref_article_id | Integer | 참조한 기준 조 ID |
| term_sheet_text | Text | 사용된 Term Sheet |
| created_at | DateTime | 생성일시 |

#### GeneratedClause (생성 항)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | 기본 키 |
| article_id | Integer | 생성 조 FK |
| clause_number | Integer | 항 번호 |
| clause_number_display | String | 표시용 |
| title | String | 항 제목 |
| content | Text | AI 생성 내용 |
| order_index | Integer | 정렬 순서 |
| ref_clause_id | Integer | 참조한 기준 항 ID |
| created_at | DateTime | 생성일시 |
| updated_at | DateTime | 수정일시 |

---

## API 엔드포인트

### 기준약정서 API (`/api/agreements`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/upload` | DOCX 업로드 및 파싱 |
| GET | `/` | 목록 조회 |
| GET | `/{id}` | 상세 조회 |
| DELETE | `/{id}` | 삭제 |
| GET | `/{id}/articles` | 조 목록 |
| GET | `/{id}/articles/{article_id}` | 조 상세 (항 포함) |
| GET | `/{id}/articles/{article_id}/clauses` | 항 목록 |
| POST | `/generate-prompt` | 프롬프트 생성 |

### 작업약정서 API (`/api/generated`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 작업약정서 목록 |
| POST | `/` | 새 작업약정서 생성 |
| GET | `/{id}` | 작업약정서 상세 |
| PUT | `/{id}` | 작업약정서 수정 |
| DELETE | `/{id}` | 작업약정서 삭제 |
| GET | `/{id}/articles` | 생성 조 목록 |
| POST | `/{id}/articles` | 생성 조 추가 |
| GET | `/{id}/articles/{article_id}` | 생성 조 상세 |
| PUT | `/{id}/articles/{article_id}` | 생성 조 수정 |
| DELETE | `/{id}/articles/{article_id}` | 생성 조 삭제 |
| POST | `/generate-with-chatgpt` | ChatGPT로 조항 생성 |
| POST | `/save-ai-result` | AI 결과 저장 |
| GET | `/api-status` | OpenAI API 상태 확인 |

---

## 웹 페이지 구조

### 네비게이션
- **기준약정서**: 업로드된 원본 약정서 관리
- **작업약정서**: 새로 생성 중인 약정서 관리

### 페이지 목록

| 경로 | 페이지 | 설명 |
|------|--------|------|
| `/` | 기준약정서 목록 | DOCX 업로드, 목록 표시 |
| `/reference/{id}` | 기준약정서 상세 | 조/항 아코디언으로 표시 |
| `/work` | 작업약정서 목록 | 새 약정서 생성, 목록 표시 |
| `/work/{id}` | 작업약정서 상세 | 생성된 조/항 아코디언, [조항추가] 버튼 |
| `/work/{id}/add-article` | 조항추가 | 4단계 워크플로우 |
| `/generate` | 프롬프트 생성 | 독립 프롬프트 생성 페이지 |

---

## 파서 설계 (parser.py)

### DOCX 파싱

#### 핵심 원칙
- 조(Article)와 항(Clause) 패턴을 **유일한 분류 기준**으로 사용
- 첫 번째 조 이전 = 문서 헤더/기본정보
- 첫 번째 조 이후 = 본문 (조/항 구조 파싱)
- 부록/별첨 = 파싱 종료 지점

#### 패턴 매칭
```python
# 조 패턴: "제1조 대출약정", "제4조의2 시장붕괴"
ARTICLE_PATTERN = r'^제[\s\t]*(\d+)[\s\t]*조(?:의[\s\t]*(\d+))?[\s\t]+(?!제[\s\t]*\d+[\s\t]*항)(.{1,80})$'

# 항 패턴: "제1항 차입의 종류"
CLAUSE_PATTERN = r'^제[\s\t]*(\d+)[\s\t]*항[\s\t]*(.{1,100})$'
```

#### 특수 처리
- 항이 없는 조: "본문" 항으로 자동 생성
- 페이지 번호 제거: `clean_title()` 함수로 후처리

### AI 응답 파싱

`parse_ai_generated_clauses(ai_content)` 함수로 AI 응답에서 다중 항을 추출합니다.

#### 파싱 우선순위
1. **JSON 파싱** (우선): `[{"clause_number": 1, "clause_title": "...", "content": "..."}]`
2. **마크다운 폴백**: `### 제1항 제목` 패턴
3. **최종 폴백**: 전체를 단일 항으로 처리

#### JSON 추출 방식
- ` ```json ... ``` ` 블록에서 추출
- ` ``` ... ``` ` 블록에서 `[`로 시작하면 추출
- `[{...}]` 배열 패턴 직접 탐색

---

## 환경 설정

### .env 파일
```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o  # 선택사항 (기본값: gpt-4o)
```

### 실행 방법
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**주의**: `--reload` 옵션 사용 시 venv 디렉토리 감시로 인해 성능 저하 발생. 개발 시에도 `--reload` 없이 실행 권장.

접속: `http://localhost:8000`

---

## 의존성

- fastapi
- uvicorn
- sqlalchemy
- python-docx
- pydantic
- jinja2
- python-multipart
- openai
- python-dotenv

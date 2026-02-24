"""SQLite 데이터베이스 연결 및 세션 관리"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 데이터베이스 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'loan_agreements.db')}"

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 전용
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()


def get_db():
    """의존성 주입용 데이터베이스 세션 제공"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 테이블 초기화"""
    from . import models  # 순환 참조 방지
    Base.metadata.create_all(bind=engine)
    _migrate_columns()
    _create_default_user()


def _migrate_columns():
    """기존 테이블에 누락된 컬럼을 추가하는 마이그레이션"""
    from sqlalchemy import text
    with engine.connect() as conn:
        # generated_clauses 테이블에 score 컬럼 추가
        result = conn.execute(text("PRAGMA table_info(generated_clauses)"))
        columns = [row[1] for row in result.fetchall()]
        if "score" not in columns:
            conn.execute(text("ALTER TABLE generated_clauses ADD COLUMN score INTEGER"))
            conn.commit()


def _create_default_user():
    """기본 사용자 생성 - 없을 때만 생성"""
    import hashlib
    import secrets
    from . import models

    default_users = [
        ("insu",  "oldman"),
        ("user1", "user1"),
        ("user2", "user2"),
        ("user3", "user3"),
    ]

    db = SessionLocal()
    try:
        for username, password in default_users:
            exists = db.query(models.User).filter(models.User.username == username).first()
            if not exists:
                salt = secrets.token_hex(16)
                hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
                db.add(models.User(username=username, hashed_password=f"{salt}:{hashed}"))
        db.commit()
    finally:
        db.close()

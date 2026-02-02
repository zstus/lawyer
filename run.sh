#!/bin/bash
# 대출약정서 관리 시스템 실행 스크립트

cd "$(dirname "$0")"

# 가상환경 활성화
source venv/bin/activate

# 서버 실행
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

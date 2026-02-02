# 대출약정서 관리 시스템 배포 가이드

Ubuntu 서버에 처음부터 세팅하여 웹서비스를 배포하는 가이드입니다.

---

## 1. GitHub 저장소 설정 (로컬에서)

```bash
# 프로젝트 디렉토리로 이동
cd /path/to/project

# Git 초기화
git init

# .gitignore 생성
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.venv/
env/

# 환경설정
.env
*.env.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# 데이터베이스
*.db
data/*.db

# 업로드 파일
uploads/

# 참조 파일 (프로젝트 외)
ref/
변호사교육자료/
EOF

# 파일 추가 및 커밋
git add .
git commit -m "Initial commit: 대출약정서 관리 시스템"

# GitHub 저장소 연결 (저장소 먼저 생성 필요)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

## 2. Ubuntu 서버 초기 설정

### 2.1 시스템 업데이트

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.2 필수 패키지 설치

```bash
sudo apt install -y git python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw
```

### 2.3 방화벽 설정

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 3. 프로젝트 디렉토리 생성 및 소스 다운로드

### 3.1 zstus 폴더 생성

```bash
sudo mkdir -p /zstus
sudo chown $USER:$USER /zstus
```

### 3.2 GitHub에서 소스 클론

```bash
cd /zstus
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git app
cd app
```

---

## 4. Python 환경 설정

### 4.1 가상환경 생성 및 활성화

```bash
cd /zstus/app
python3 -m venv venv
source venv/bin/activate
```

### 4.2 의존성 설치

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4.3 환경변수 설정

```bash
cat > /zstus/app/backend/.env << 'EOF'
OPENAI_API_KEY=sk-your-openai-api-key-here
EOF

# 권한 설정
chmod 600 /zstus/app/backend/.env
```

---

## 5. 데이터베이스 디렉토리 설정

```bash
mkdir -p /zstus/app/backend/data
chmod 755 /zstus/app/backend/data
```

---

## 6. Systemd 서비스 설정

### 6.1 서비스 파일 생성

```bash
sudo tee /etc/systemd/system/loanapp.service << 'EOF'
[Unit]
Description=대출약정서 관리 시스템
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/zstus/app/backend
Environment="PATH=/zstus/app/venv/bin"
EnvironmentFile=/zstus/app/backend/.env
ExecStart=/zstus/app/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

### 6.2 서비스 시작

```bash
sudo systemctl daemon-reload
sudo systemctl enable loanapp
sudo systemctl start loanapp
```

### 6.3 서비스 상태 확인

```bash
sudo systemctl status loanapp
```

---

## 7. Nginx 리버스 프록시 설정

### 7.1 Nginx 설정 파일 생성

```bash
sudo tee /etc/nginx/sites-available/loanapp << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 도메인 또는 서버 IP로 변경

    client_max_body_size 50M;  # 파일 업로드 크기 제한

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    location /static {
        alias /zstus/app/backend/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF
```

### 7.2 사이트 활성화

```bash
sudo ln -s /etc/nginx/sites-available/loanapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # 기본 설정 제거 (선택)
sudo nginx -t  # 설정 검증
sudo systemctl reload nginx
```

---

## 8. SSL 인증서 설정 (HTTPS)

### 8.1 Let's Encrypt 인증서 발급

```bash
sudo certbot --nginx -d your-domain.com
```

### 8.2 자동 갱신 테스트

```bash
sudo certbot renew --dry-run
```

---

## 9. 배포 완료 확인

### 9.1 서비스 상태 확인

```bash
# 애플리케이션 서비스
sudo systemctl status loanapp

# Nginx
sudo systemctl status nginx

# 로그 확인
sudo journalctl -u loanapp -f
```

### 9.2 웹 접속 테스트

```bash
# 로컬 테스트
curl http://127.0.0.1:8000

# 또는 브라우저에서
# http://your-domain.com (HTTP)
# https://your-domain.com (HTTPS, SSL 설정 후)
```

---

## 10. 유지보수 명령어

### 소스 업데이트

```bash
cd /zstus/app
git pull origin main
source venv/bin/activate
pip install -r backend/requirements.txt
sudo systemctl restart loanapp
```

### 서비스 제어

```bash
# 재시작
sudo systemctl restart loanapp

# 중지
sudo systemctl stop loanapp

# 시작
sudo systemctl start loanapp

# 로그 확인
sudo journalctl -u loanapp -n 100 -f
```

### 데이터베이스 백업

```bash
cp /zstus/app/backend/data/agreements.db /zstus/app/backend/data/agreements.db.backup.$(date +%Y%m%d)
```

---

## 11. 문제 해결

### 포트 확인

```bash
sudo netstat -tlnp | grep 8000
```

### 방화벽 상태

```bash
sudo ufw status
```

### Nginx 에러 로그

```bash
sudo tail -f /var/log/nginx/error.log
```

### Python 환경 확인

```bash
source /zstus/app/venv/bin/activate
python --version
pip list
```

---

## 요약 체크리스트

- [ ] GitHub 저장소 생성 및 소스 푸시
- [ ] Ubuntu 서버 패키지 업데이트
- [ ] Python, Nginx, Git 설치
- [ ] /zstus 폴더 생성
- [ ] GitHub에서 소스 클론
- [ ] Python 가상환경 및 의존성 설치
- [ ] .env 파일에 OpenAI API 키 설정
- [ ] Systemd 서비스 등록 및 시작
- [ ] Nginx 리버스 프록시 설정
- [ ] SSL 인증서 발급 (선택)
- [ ] 웹 접속 테스트

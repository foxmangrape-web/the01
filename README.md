# 🚀 Git Quick Start Guide

Git 기초 사용법 및 핵심 명령어 정리 문서입니다.

## 🛠️ 핵심 명령어 (Cheat Sheet)

```bash
# 1. 저장소 초기화 및 설정
git init
git config --global user.name "내이름"
git config --global user.email "내이메일@example.com"

# 2. 상태 확인 및 스테이징
git status
git add .                  # 모든 변경사항 스테이징

# 3. 커밋
git commit -m "feat: 첫 번째 커밋"

# 4. 원격 저장소 연결 및 푸시
git remote add origin <저장소 URL>
git branch -M main
git push -u origin main

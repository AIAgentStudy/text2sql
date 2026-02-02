# Text2SQL Agent Frontend Dockerfile
# Node.js 20 기반 단일 스테이지 빌드 (serve 사용)

FROM node:20-slim

WORKDIR /app

# 패키지 파일 복사
COPY package.json package-lock.json* ./

# 의존성 설치
RUN npm ci

# 소스 코드 복사
COPY . .

# 빌드 시 환경 변수 설정 (필요한 경우)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# 프로덕션 빌드
RUN npm run build

# serve 패키지 전역 설치
RUN npm install -g serve

# 포트 노출
EXPOSE 3000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

# serve로 정적 파일 서빙 (SPA 모드)
CMD ["serve", "-s", "dist", "-l", "3000"]

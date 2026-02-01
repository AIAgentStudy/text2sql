# Text2SQL Agent Frontend Dockerfile
# Node.js 20 기반 멀티스테이지 빌드

# -------------------------------------------
# Builder 스테이지: 빌드
# -------------------------------------------
FROM node:20-slim AS builder

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

# -------------------------------------------
# Production 스테이지: Nginx로 정적 파일 서빙
# -------------------------------------------
FROM nginx:alpine AS production

# Nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드된 파일 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 비루트 사용자로 실행 (Nginx alpine 이미지 지원)
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# 포트 노출
EXPOSE 80

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]

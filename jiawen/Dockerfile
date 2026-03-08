FROM node:22-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm

# 复制所有依赖相关文件（含 patches/）
COPY package.json pnpm-lock.yaml ./
COPY patches/ ./patches/
RUN pnpm install --frozen-lockfile

# 复制全部源码并构建
COPY . .
RUN pnpm build

# ─── 运行阶段 ───
FROM node:22-alpine AS runner

WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-lock.yaml ./
COPY patches/ ./patches/
RUN pnpm install --frozen-lockfile --prod

# 从构建阶段复制产物
COPY --from=builder /app/dist ./dist

EXPOSE 3000

ENV NODE_ENV=production

CMD ["node", "dist/index.js"]

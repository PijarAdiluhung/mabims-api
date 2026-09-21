FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
# Lockfiles are generated on Windows; npm's platform-optional resolution can
# leave an alpine-only subtree out, which only fails inside a musl image. Fall
# back to a live resolve instead of hard-failing the deploy; CI runs the strict
# npm ci against node:22-alpine to surface drift on every push.
RUN npm ci --no-fund --no-audit || npm install --no-fund --no-audit

COPY . .
ARG PUBLIC_API_BASE=https://api.mabims.dev
ENV PUBLIC_API_BASE=$PUBLIC_API_BASE
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -qO /dev/null http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

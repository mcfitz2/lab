FROM node:18-alpine AS builder

WORKDIR /build
COPY . .
RUN npm install --no-package-lock
RUN npx ng build --configuration production

FROM nginx:1.25-alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /build/dist/ui /usr/share/nginx/html

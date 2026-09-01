# Frontend Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Argumentos de build para URLs
ARG VITE_API_URL
ARG VITE_WS_URL

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm install && npm cache clean --force

# Copiar código fuente
COPY . .

# Build de producción
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_URL=${VITE_WS_URL}
RUN npm run build

# Imagen de producción con nginx
FROM nginx:alpine

# Copiar archivos compilados
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

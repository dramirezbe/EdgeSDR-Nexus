#!/bin/bash
# Script de instalación en servidor
# Generado automáticamente - 12/02/2025 18:35:55

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  INSTALACIÓN ANE REALTIME                             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 1. Ir al directorio del proyecto
echo "📁 Configurando directorio..."
cd /opt/ane-realtime || exit 1

# 2. Hacer backup si existe instalación previa
if [ -d "backend" ]; then
    echo "💾 Creando backup de instalación anterior..."
    tar -czf /opt/ane-backups/backup-20251202-183536.tar.gz backend frontend docker-compose.yml 2>/dev/null || true
fi

# 3. Extraer archivos
echo "📦 Extrayendo archivos..."
tar -xzf ane-realtime-20251202-183536.tar.gz

# 4. Verificar/Instalar Docker
echo "🐳 Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Verificar Docker Compose
if ! docker compose version &> /dev/null; then
    echo "Instalando Docker Compose plugin..."
    apt-get update
    apt-get install -y docker-compose-plugin
fi

# 5. Configurar variables de entorno
echo "⚙️  Configurando variables de entorno..."
cat > .env << 'ENVFILE'
NODE_ENV=production
PORT=3000
DATABASE_PATH=/app/data/ane.db
VITE_API_URL=http:///api
VITE_WS_URL=ws:///ws
ENVFILE

# 6. Crear directorios necesarios
echo "📂 Creando directorios..."
mkdir -p backend/data backend/logs

# 7. Detener contenedores existentes (si los hay)
echo "🛑 Deteniendo contenedores previos..."
docker compose down 2>/dev/null || true

# 8. Construir imágenes
echo "🏗️  Construyendo imágenes Docker..."
docker compose build --no-cache

# 9. Inicializar base de datos (si es necesario)
if [ ! -f "backend/data/ane.db" ]; then
    echo "🗄️  Inicializando base de datos..."
    docker compose run --rm backend node dist/database/migrate.js
    docker compose run --rm backend node dist/database/seed.js
fi

# 10. Levantar servicios
echo "🚀 Levantando servicios..."
docker compose up -d

# 11. Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios inicien..."
sleep 10

# 12. Verificar estado
echo ""
echo "✅ Estado de los servicios:"
docker compose ps

echo ""
echo "📊 Logs recientes:"
docker compose logs --tail=20

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  INSTALACIÓN COMPLETADA                               ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 URLs de acceso:"
echo "   Frontend (usuarios): http://"
echo "   Backend (sensores): http:///api"
echo "   WebSocket: ws:///ws"
echo ""
echo "📝 Comandos útiles:"
echo "   Ver logs: docker compose logs -f"
echo "   Reiniciar: docker compose restart"
echo "   Detener: docker compose down"
echo "   Actualizar: docker compose pull && docker compose up -d"
echo ""

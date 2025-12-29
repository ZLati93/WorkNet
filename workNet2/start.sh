#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-docker}

if [ "$MODE" = "local" ] || [ "$MODE" = "dev" ]; then
  echo "🚀 Démarrage en mode local (dev) — processus en avant-plan"
  # Use npx concurrently so no global install required
  npx concurrently "(cd backend-node && npm run dev)" "(cd frontend-client && npm run dev)" "(cd frontend-freelancer && npm run dev)" "(cd rpc-server && npm run dev)"
  exit $?
fi

# Default: docker-compose up
if command -v docker >/dev/null 2>&1; then
  echo "🐳 Démarrage des services via Docker Compose (docker compose up -d --build)"
  # Prefer modern docker compose command
  if docker compose version >/dev/null 2>&1; then
    docker compose up -d --build
  else
    docker-compose up -d --build
  fi
  echo "✅ Services démarrés (conteneurs en arrière-plan)"
  exit 0
fi

echo "⚠️  Docker non trouvé. Pour un démarrage local, lancez : ./start.sh local"
exit 1

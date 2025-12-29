#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-docker}

if [ "$MODE" = "local" ] || [ "$MODE" = "dev" ]; then
  echo "🛑 Arrêt du mode local : tentative d'arrêt des processus sur les ports usuels"
  # Kill common ports used by the project
  if npx kill-port --version >/dev/null 2>&1; then
    npx kill-port 3000 3001 8000 || true
  else
    # try to use lsof/kill or warn
    echo "⚠️  'kill-port' non disponible. Fermez manuellement les terminaux qui ont lancé 'start:local'."
  fi
  exit 0
fi

if command -v docker >/dev/null 2>&1; then
  echo "🐳 Arrêt des services Docker (docker compose down -v)"
  if docker compose version >/dev/null 2>&1; then
    docker compose down -v
  else
    docker-compose down -v
  fi
  echo "✅ Conteneurs arrêtés et volumes supprimés (si présents)"
  exit 0
fi

echo "⚠️  Docker non trouvé. Si vous avez démarré en local, utilisez: ./stop.sh local"
exit 1

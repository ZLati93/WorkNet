#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Démarrage de l'installation du projet WorkNet"

# Helper
command_exists() { command -v "$1" >/dev/null 2>&1; }

# Check basic tools
echo "Vérification des outils requis..."
for cmd in docker npm node python3 pip3; do
  if command_exists "$cmd"; then
    echo "  ✅ $cmd"
  else
    echo "  ⚠️  $cmd n'est pas installé ou introuvable dans le PATH"
  fi
done

# NPM install in root to install dev tools (concurrently, kill-port)
if [ -f package.json ]; then
  echo "\n-> Installation des dépendances racine (npm install)"
  npm install
fi

# Install node packages in each subproject that has package.json
SUBDIRS=(backend-node frontend-client frontend-freelancer database integration-qa rpc-server)
for d in "${SUBDIRS[@]}"; do
  if [ -f "$d/package.json" ]; then
    echo "\n-> npm install dans $d"
    (cd "$d" && npm install)
  fi
done

# Install python requirements where present
PY_DIRS=(rpc-server integration-qa)
for d in "${PY_DIRS[@]}"; do
  if [ -f "$d/requirements.txt" ]; then
    if command_exists pip3 || command_exists pip; then
      PIP_CMD="$(command -v pip3 || command -v pip)"
      echo "\n-> Installation des dépendances Python dans $d"
      (cd "$d" && "$PIP_CMD" install -r requirements.txt)
    else
      echo "\n⚠️  pip introuvable : impossible d'installer les dépendances Python pour $d"
    fi
  fi
done

# Make shell scripts executable (Unix systems)
chmod +x ./setup.sh ./start.sh ./stop.sh ./test.sh || true

cat <<'EOF'

✅ Installation terminée.
- Pour démarrer les services avec Docker : ./start.sh
- Pour démarrer en local (dev) : ./start.sh local
- Pour lancer les tests : ./test.sh
- Pour arrêter les services : ./stop.sh

EOF

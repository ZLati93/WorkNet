#!/usr/bin/env bash
set -euo pipefail

EXIT_CODE=0

run_cmd() {
  echo "\n➡️  Exécution : $*"
  if ! eval "$@"; then
    echo "❌ Échec : $*"
    EXIT_CODE=1
  else
    echo "✅ Succès : $*"
  fi
}

# Node projects
if [ -f backend-node/package.json ]; then
  run_cmd "(cd backend-node && npm test)"
fi

if [ -f frontend-client/package.json ]; then
  run_cmd "(cd frontend-client && npm test)"
fi

if [ -f frontend-freelancer/package.json ]; then
  run_cmd "(cd frontend-freelancer && npm test)"
fi

# Integration QA (uses npm scripts to run multiple test suites)
if [ -f integration-qa/package.json ]; then
  run_cmd "(cd integration-qa && npm run test:all)"
fi

# RPC server (node/typescript tests)
if [ -f rpc-server/package.json ]; then
  run_cmd "(cd rpc-server && npm test)"
fi

if [ "$EXIT_CODE" -ne 0 ]; then
  echo "\n❌ Au moins un jeu de tests a échoué"
else
  echo "\n✅ Tous les tests sont passés (ou les scripts ont été exécutés)"
fi

exit $EXIT_CODE

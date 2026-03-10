#!/usr/bin/env bash
set -euxo pipefail

REPO_URL="${REPO_URL:-git@github.com:your-org/borofone_chat.git}"
PROD_PATH="/opt/borofone-chat-prod"
STAGING_PATH="/opt/borofone-chat-staging"
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOOTSTRAP_PENDING=0

mkdir -p "${PROD_PATH}" "${STAGING_PATH}"

if [ ! -d "${PROD_PATH}/.git" ]; then
  git clone "${REPO_URL}" "${PROD_PATH}"
fi

if [ ! -d "${STAGING_PATH}/.git" ]; then
  git clone "${REPO_URL}" "${STAGING_PATH}"
fi

cd "${PROD_PATH}"
git fetch --prune origin
git checkout main
if [ ! -f .env ]; then
  cp .env.production.example .env
  BOOTSTRAP_PENDING=1
fi
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
mkdir -p uploads uploads/avatars uploads/attachments logs
if [ "${BOOTSTRAP_PENDING}" -eq 0 ]; then
  alembic upgrade head
fi
deactivate

cd "${STAGING_PATH}"
git fetch --prune origin
git checkout dev
if [ ! -f .env ]; then
  cp .env.staging.example .env
  BOOTSTRAP_PENDING=1
fi
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
mkdir -p uploads uploads/avatars uploads/attachments logs
if [ "${BOOTSTRAP_PENDING}" -eq 0 ]; then
  alembic upgrade head
fi
deactivate

install -m 644 "${SCRIPT_ROOT}/deploy/systemd/borofone-prod.service" /etc/systemd/system/borofone-prod.service
install -m 644 "${SCRIPT_ROOT}/deploy/systemd/borofone-staging.service" /etc/systemd/system/borofone-staging.service
install -m 644 "${SCRIPT_ROOT}/deploy/nginx/borofone.conf" /etc/nginx/sites-available/borofone.conf

ln -sfn /etc/nginx/sites-available/borofone.conf /etc/nginx/sites-enabled/borofone.conf

systemctl daemon-reload
systemctl enable borofone-prod
systemctl enable borofone-staging
nginx -t
systemctl reload nginx

if [ "${BOOTSTRAP_PENDING}" -eq 1 ]; then
  echo "Edit ${PROD_PATH}/.env and ${STAGING_PATH}/.env, then rerun this script to apply migrations and restart services."
  exit 0
fi

systemctl restart borofone-prod
systemctl restart borofone-staging


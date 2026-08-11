#!/usr/bin/env bash
# Развёртывание Banetskaya.by на Ubuntu/Debian VPS (Contabo) с HTTPS (Caddy) + DuckDNS.
# Запускать на СЕРВЕРЕ под root.  Перед запуском задайте REPO_URL (ваш GitHub после "Save to GitHub").
set -e

REPO_URL="${REPO_URL:-}"                       # напр. https://github.com/USER/REPO.git
DOMAIN="banetskaya.duckdns.org"
DUCKDNS_TOKEN="ddd1b399-0607-4cce-82c2-8632c61c29bc"
DUCKDNS_SUB="banetskaya"
APP_DIR="/opt/banetskaya"

if [ -z "$REPO_URL" ]; then echo "Задайте REPO_URL=... (ссылка на ваш GitHub-репозиторий)"; exit 1; fi

echo "== пакеты =="
apt-get update -y
apt-get install -y git curl python3 python3-venv python3-pip libreoffice-writer libreoffice-core \
  gnupg ca-certificates debian-keyring debian-archive-keyring apt-transport-https

echo "== node 20 + yarn =="
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
corepack enable

echo "== mongodb =="
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb.gpg --dearmor
. /etc/os-release
if [ "$ID" = "ubuntu" ]; then
  # MongoDB 7.0 не публикует репозиторий для noble(24.04); пакеты jammy(22.04) работают.
  MONGO_CODENAME="$VERSION_CODENAME"
  [ "$VERSION_CODENAME" = "noble" ] && MONGO_CODENAME="jammy"
  echo "deb [ signed-by=/usr/share/keyrings/mongodb.gpg ] https://repo.mongodb.org/apt/ubuntu ${MONGO_CODENAME}/mongodb-org/7.0 multiverse" > /etc/apt/sources.list.d/mongodb.list
else
  echo "deb [ signed-by=/usr/share/keyrings/mongodb.gpg ] http://repo.mongodb.org/apt/debian ${VERSION_CODENAME}/mongodb-org/7.0 main" > /etc/apt/sources.list.d/mongodb.list
fi
apt-get update -y && apt-get install -y mongodb-org
systemctl enable --now mongod

echo "== код =="
rm -rf "$APP_DIR"; git clone "$REPO_URL" "$APP_DIR"

echo "== backend =="
cd "$APP_DIR/backend"
python3 -m venv .venv && . .venv/bin/activate
pip install --upgrade pip
pip install -r "$APP_DIR/windows-package/requirements-windows.txt" "uvicorn[standard]"
printf 'MONGO_URL="mongodb://127.0.0.1:27017"\nDB_NAME="banetskaya_db"\nCORS_ORIGINS="*"\n' > .env
deactivate

echo "== frontend build =="
cd "$APP_DIR/frontend"
printf 'REACT_APP_BACKEND_URL=https://%s\n' "$DOMAIN" > .env
yarn install && yarn build

echo "== systemd (uvicorn раздаёт фронтенд на 8001) =="
cat > /etc/systemd/system/banetskaya.service <<EOF
[Unit]
Description=Banetskaya.by
After=network.target mongod.service
[Service]
WorkingDirectory=$APP_DIR/backend
Environment=FRONTEND_BUILD_DIR=$APP_DIR/frontend/build
ExecStart=$APP_DIR/backend/.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001
Restart=always
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable --now banetskaya

echo "== DuckDNS (обновление IP каждые 5 мин) =="
mkdir -p /opt/duckdns
cat > /opt/duckdns/upd.sh <<EOF
curl -s "https://www.duckdns.org/update?domains=$DUCKDNS_SUB&token=$DUCKDNS_TOKEN&ip=" >/dev/null
EOF
chmod +x /opt/duckdns/upd.sh && /opt/duckdns/upd.sh
( crontab -l 2>/dev/null; echo "*/5 * * * * /opt/duckdns/upd.sh" ) | crontab -

echo "== Caddy (авто-HTTPS) =="
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy.gpg
echo "deb [signed-by=/usr/share/keyrings/caddy.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" > /etc/apt/sources.list.d/caddy.list
apt-get update -y && apt-get install -y caddy
cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
    reverse_proxy 127.0.0.1:8001
}
EOF
systemctl restart caddy

echo "== ГОТОВО. Откройте: https://$DOMAIN =="

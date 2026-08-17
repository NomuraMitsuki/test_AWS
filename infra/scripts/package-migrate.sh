#!/usr/bin/env bash
# migrate Lambda 用 zip を Linux / Python 3.12 向けに作り、UpdateFunctionCode する。
# Mac の python3 で pip install -t すると macos arm64 / cp310 になり Lambda で動かない。
# apply はしない。関数が無いときは先に ./infra/scripts/tf-dev.sh apply。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FUNCTION_NAME="${LAMBDA_MIGRATE_NAME:-attendance-dev-migrate}"
REGION="${AWS_DEFAULT_REGION:-${AWS_REGION:-ap-northeast-1}}"
export AWS_DEFAULT_REGION="$REGION"
export AWS_REGION="$REGION"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: $1 が見つかりません。" >&2
    exit 1
  fi
}

require_cmd aws
require_cmd python3
require_cmd zip

unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_SECURITY_TOKEN
if ! aws sts get-caller-identity --output text >/dev/null 2>&1; then
  echo "ERROR: AWS 資格情報がありません。先に ./infra/scripts/tf-dev.sh auth を実行してください。" >&2
  exit 1
fi
eval "$(aws configure export-credentials --format env)"

if ! aws lambda get-function --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
  echo "ERROR: 関数 ${FUNCTION_NAME} がありません。git pull のあと ./infra/scripts/tf-dev.sh apply してください。" >&2
  exit 1
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "→ pip install（manylinux2014_x86_64 / Python 3.12。Mac 用 wheel は使わない）"
python3 -m pip install -r "${REPO_ROOT}/backend/migrate/requirements.txt" -t "$WORK" \
  --python-version 3.12 \
  --platform manylinux2014_x86_64 \
  --only-binary=:all: \
  --upgrade \
  --quiet

cp "${REPO_ROOT}/backend/migrate/"*.py "$WORK/"
mkdir -p "${WORK}/migrations"
cp "${REPO_ROOT}/backend/migrations/"*.sql "${WORK}/migrations/"

ZIP="/tmp/migrate.zip"
rm -f "$ZIP"
(cd "$WORK" && zip -qr "$ZIP" .)

echo "→ aws lambda update-function-code ${FUNCTION_NAME}"
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file "fileb://${ZIP}" \
  --query '{FunctionName:FunctionName,LastModified:LastModified,CodeSize:CodeSize}' \
  --output table

echo "OK: ${ZIP} を ${FUNCTION_NAME} に載せました。次: ./infra/scripts/invoke-migrate.sh"

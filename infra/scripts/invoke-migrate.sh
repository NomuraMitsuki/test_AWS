#!/usr/bin/env bash
# Mac から migrate Lambda を invoke する（terraform apply はしない）。
# 事前に aws login + export-credentials（または ./infra/scripts/tf-dev.sh auth）。
# 使い方（リポジトリルートから）:
#   ./infra/scripts/invoke-migrate.sh
#   ./infra/scripts/invoke-migrate.sh migrate
#   ./infra/scripts/invoke-migrate.sh seed-admin <email> <cognito_sub> <name>
set -euo pipefail

FUNCTION_NAME="${LAMBDA_MIGRATE_NAME:-attendance-dev-migrate}"
REGION="${AWS_DEFAULT_REGION:-${AWS_REGION:-ap-northeast-1}}"
export AWS_DEFAULT_REGION="$REGION"
export AWS_REGION="$REGION"

usage() {
  cat <<'EOF'
使い方: ./infra/scripts/invoke-migrate.sh [migrate]
        ./infra/scripts/invoke-migrate.sh seed-admin <email> <cognito_sub> <name>

  migrate      SQL 001〜003 を適用（引数省略時のデフォルト）
  seed-admin   users に admin/active を INSERT（Cognito は呼ばない）

関数名は LAMBDA_MIGRATE_NAME（既定: attendance-dev-migrate）。
apply は実行しない。認証は ./infra/scripts/tf-dev.sh auth を先に。
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: $1 が見つかりません。" >&2
    exit 1
  fi
}

export_creds() {
  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_SECURITY_TOKEN
  if aws sts get-caller-identity --output text >/dev/null 2>&1; then
    echo "→ aws configure export-credentials を環境変数へ展開"
    eval "$(aws configure export-credentials --format env)"
    return 0
  fi
  echo "ERROR: AWS 資格情報がありません。先に ./infra/scripts/tf-dev.sh auth を実行してください。" >&2
  exit 1
}

invoke_payload() {
  local payload="$1"
  local out
  out="$(mktemp)"
  echo "→ aws lambda invoke ${FUNCTION_NAME}"
  aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --cli-binary-format raw-in-base64-out \
    --payload "$payload" \
    "$out" >/dev/null
  echo "応答:"
  cat "$out"
  echo
  rm -f "$out"
}

main() {
  if [[ $# -ge 1 && "$1" =~ ^(-h|--help|help)$ ]]; then
    usage
    exit 0
  fi

  require_cmd aws
  export_creds

  local cmd="${1:-migrate}"
  case "$cmd" in
    migrate)
      invoke_payload '{}'
      ;;
    seed-admin)
      if [[ $# -lt 4 ]]; then
        echo "ERROR: seed-admin には email / cognito_sub / name が必要です。" >&2
        usage
        exit 1
      fi
      local email="$2"
      local sub="$3"
      local name="$4"
      local payload
      payload="$(python3 -c 'import json,sys; print(json.dumps({"action":"seed_admin","email":sys.argv[1],"cognito_sub":sys.argv[2],"name":sys.argv[3]}, ensure_ascii=False))' "$email" "$sub" "$name")"
      invoke_payload "$payload"
      ;;
    *)
      echo "ERROR: 不明なサブコマンド: $cmd" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"

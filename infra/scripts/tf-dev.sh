#!/usr/bin/env bash
# aws login（必要時）+ export-credentials のあと、本体（infra/envs/dev）向け terraform を実行する。
# infra/bootstrap は対象外（bootstrap は cd infra/bootstrap して直接 terraform する）。
# 使い方（リポジトリルートから）:
#   ./infra/scripts/tf-dev.sh auth
#   ./infra/scripts/tf-dev.sh plan
#   ./infra/scripts/tf-dev.sh apply
#   ./infra/scripts/tf-dev.sh up --admin-email you@example.com
#   ./infra/scripts/tf-dev.sh down
set -euo pipefail

# aws の JSON 出力が less に捕まらないようにする。
export AWS_PAGER=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DEV_DIR="${REPO_ROOT}/infra/envs/dev"
CHECK_AUTH="${SCRIPT_DIR}/check-aws-auth.sh"
PACKAGE_MIGRATE="${SCRIPT_DIR}/package-migrate.sh"
INVOKE_MIGRATE="${SCRIPT_DIR}/invoke-migrate.sh"
PLAN_FILE="${DEV_DIR}/tfplan"
FRONTEND_ENV="${REPO_ROOT}/frontend/.env.local"

REGION="${AWS_DEFAULT_REGION:-${AWS_REGION:-ap-northeast-1}}"
export AWS_DEFAULT_REGION="$REGION"
export AWS_REGION="$REGION"

usage() {
  cat <<'EOF'
使い方: ./infra/scripts/tf-dev.sh <auth|plan|apply|up|down>

  auth   aws login（必要時）と export-credentials、認証確認のみ
  plan   上記のあと terraform init / plan -out=tfplan
  apply  内部で plan し直し、yes 確認のあと terraform apply tfplan
  up     apply のあと migrate zip / SQL、任意で初回 admin、frontend/.env.local
  down   本体（infra/envs/dev）を destroy。[y/N] 確認。bootstrap は消さない

  up のオプション:
    --admin-email EMAIL      Cognito AdminCreateUser + グループ admin + seed
                             （省略時は Cognito / seed をスキップ）
    --admin-name NAME        表示名（省略時: Admin）
    --admin-password PASS    仮パスワード（省略時は生成して標準出力のみ）

aws login の資格情報は Terraform が直接拾えないことがあるため、
必ず aws configure export-credentials を環境変数へ展開してから実行する。
down は infra/bootstrap では絶対に destroy しない。
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: $1 が見つかりません。" >&2
    exit 1
  fi
}

# 期限切れの AWS_* 環境変数はプロファイルより優先され、aws login 後も sts が失敗する。
clear_env_creds() {
  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_SECURITY_TOKEN
}

ensure_aws_session() {
  require_cmd aws

  if aws sts get-caller-identity --output text >/dev/null 2>&1; then
    echo "→ 既存の AWS セッションを利用します"
    return 0
  fi

  echo "→ sts に失敗したため、シェルの AWS_* 環境変数を外して再試行します"
  clear_env_creds
  if aws sts get-caller-identity --output text >/dev/null 2>&1; then
    echo "→ プロファイルの資格情報を利用します"
    return 0
  fi

  echo "→ AWS 資格情報がありません。aws login を実行します（ブラウザが開く場合があります）"
  if ! aws login; then
    echo "ERROR: aws login に失敗しました。手動で aws login または aws sso login を試してください。" >&2
    exit 1
  fi

  # login はプロファイルを更新する。残っている古い環境変数を捨ててから sts する。
  clear_env_creds
  local sts_err
  if ! sts_err="$(aws sts get-caller-identity --output text 2>&1)"; then
    echo "ERROR: aws login 後も sts get-caller-identity に失敗しました。" >&2
    echo "$sts_err" >&2
    echo "ヒント: このシェルで次を実行してからやり直してください:" >&2
    echo "  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_SECURITY_TOKEN" >&2
    exit 1
  fi
}

export_creds_for_terraform() {
  # --help の終了コードは AWS CLI によって非 0 になり得るため、存在チェックに使わない。
  echo "→ aws configure export-credentials を環境変数へ展開（Terraform 用）"
  local creds
  if ! creds="$(aws configure export-credentials --format env 2>&1)"; then
    cat <<'EOF' >&2
ERROR: export-credentials に失敗しました。

aws login / SSO のセッションが有効か確認し、AWS CLI v2 が
`aws configure export-credentials --format env` をサポートしているか確認してください。
EOF
    echo "$creds" >&2
    exit 1
  fi
  # shellcheck disable=SC1090
  eval "$creds"

  if [[ -z "${AWS_ACCESS_KEY_ID:-}" ]]; then
    echo "ERROR: export-credentials 後も AWS_ACCESS_KEY_ID が空です。" >&2
    exit 1
  fi
}

run_auth_check() {
  if [[ ! -x "$CHECK_AUTH" ]]; then
    echo "ERROR: $CHECK_AUTH がありません（実行権限を確認してください）。" >&2
    exit 1
  fi
  "$CHECK_AUTH"
}

prepare_auth() {
  ensure_aws_session
  export_creds_for_terraform
  run_auth_check
}

ensure_tfvars() {
  if [[ ! -f "${DEV_DIR}/terraform.tfvars" && -f "${DEV_DIR}/terraform.tfvars.example" ]]; then
    echo "→ terraform.tfvars が無いため example からコピーします"
    cp "${DEV_DIR}/terraform.tfvars.example" "${DEV_DIR}/terraform.tfvars"
  fi
}

confirm_yes() {
  local prompt="$1"
  local answer
  printf "%s" "$prompt"
  read -r answer
  if [[ ! "$answer" =~ ^[yY]$ ]]; then
    return 1
  fi
  return 0
}

run_plan() {
  require_cmd terraform
  ensure_tfvars
  cd "$DEV_DIR"
  echo "→ terraform init -backend-config=backend.hcl"
  terraform init -input=false -backend-config=backend.hcl
  echo "→ terraform plan -out=tfplan"
  terraform plan -input=false -out="$PLAN_FILE"
  echo "OK: plan を ${PLAN_FILE} に保存しました。apply する場合: ./infra/scripts/tf-dev.sh apply"
}

run_apply() {
  require_cmd terraform
  ensure_tfvars
  cd "$DEV_DIR"
  echo "→ apply 前に最新の plan を取ります（保存済み plan への apply には Terraform の yes/no が出ないため、ここで確認します）"
  terraform init -input=false -backend-config=backend.hcl
  terraform plan -input=false -out="$PLAN_FILE"
  echo ""
  echo "警告: apply すると NAT Gateway / RDS など課金リソースが作成または更新されます。"
  if ! confirm_yes "この plan を apply しますか? [y/N] "; then
    echo "中止しました（apply なし）。"
    exit 1
  fi
  echo "→ terraform apply tfplan"
  terraform apply -input=false "$PLAN_FILE"
  echo "OK: apply 完了。OIDC 用に次を控えてください:"
  terraform output gha_infra_role_arn
  terraform output gha_backend_role_arn
}

tf_output_raw() {
  (cd "$DEV_DIR" && terraform output -raw "$1")
}

generate_temp_password() {
  # Cognito: 最低 8 文字、大文字・小文字・数字必須。記号は任意なので使わない。
  if command -v python3 >/dev/null 2>&1; then
    python3 -c '
import secrets, string
alphabet = string.ascii_letters + string.digits
while True:
    pw = "".join(secrets.choice(alphabet) for _ in range(16))
    if (any(c.islower() for c in pw) and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw)):
        print(pw)
        break
'
    return 0
  fi
  require_cmd openssl
  local raw
  raw="$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9')"
  printf 'A1a%s\n' "${raw:0:13}"
}

write_frontend_env() {
  local pool_id client_id api_endpoint
  pool_id="$(tf_output_raw cognito_user_pool_id)"
  client_id="$(tf_output_raw cognito_client_id)"
  api_endpoint="$(tf_output_raw api_endpoint)"
  cat > "$FRONTEND_ENV" <<EOF
NEXT_PUBLIC_AWS_REGION=${REGION}
NEXT_PUBLIC_COGNITO_USER_POOL_ID=${pool_id}
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=${client_id}
NEXT_PUBLIC_API_BASE_URL=${api_endpoint}
EOF
  echo "→ ${FRONTEND_ENV} を terraform output から書きました（gitignore 済み）"
}

# seed が新規作成したときだけ仮パスワードを保持する（stdout には出さない）。
SEED_ADMIN_CREATED_PASSWORD=""

seed_admin_user() {
  local email="$1"
  local name="$2"
  local password="$3"
  local pool_id created=1 create_out=""
  pool_id="$(tf_output_raw cognito_user_pool_id)"
  SEED_ADMIN_CREATED_PASSWORD=""

  echo "→ Cognito AdminCreateUser (${email})"
  if ! create_out="$(aws cognito-idp admin-create-user \
    --user-pool-id "$pool_id" \
    --username "$email" \
    --user-attributes "Name=email,Value=${email}" "Name=email_verified,Value=true" "Name=name,Value=${name}" \
    --temporary-password "$password" \
    --message-action SUPPRESS 2>&1)"; then
    if grep -q 'UsernameExistsException' <<<"$create_out"; then
      echo "→ 既存ユーザーです（UsernameExistsException）。作成はスキップします"
      created=0
    else
      echo "$create_out" >&2
      echo "ERROR: AdminCreateUser に失敗しました。" >&2
      exit 1
    fi
  fi

  echo "→ admin-add-user-to-group admin"
  aws cognito-idp admin-add-user-to-group \
    --user-pool-id "$pool_id" \
    --username "$email" \
    --group-name admin

  local sub
  sub="$(aws cognito-idp admin-get-user \
    --user-pool-id "$pool_id" \
    --username "$email" \
    --query "UserAttributes[?Name=='sub'].Value" \
    --output text)"
  if [[ -z "$sub" || "$sub" == "None" ]]; then
    echo "ERROR: Cognito sub を取得できませんでした。" >&2
    exit 1
  fi
  echo "→ cognito_sub=${sub}"

  echo "→ invoke-migrate.sh seed-admin"
  "$INVOKE_MIGRATE" seed-admin "$email" "$sub" "$name"

  if [[ "$created" -eq 1 ]]; then
    SEED_ADMIN_CREATED_PASSWORD="$password"
  fi
}

parse_up_args() {
  UP_ADMIN_EMAIL=""
  UP_ADMIN_NAME="Admin"
  UP_ADMIN_PASSWORD=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --admin-email)
        if [[ $# -lt 2 || "$2" == --* ]]; then
          echo "ERROR: --admin-email には値が必要です。" >&2
          exit 1
        fi
        UP_ADMIN_EMAIL="$2"
        shift 2
        ;;
      --admin-name)
        if [[ $# -lt 2 || "$2" == --* ]]; then
          echo "ERROR: --admin-name には値が必要です。" >&2
          exit 1
        fi
        UP_ADMIN_NAME="$2"
        shift 2
        ;;
      --admin-password)
        if [[ $# -lt 2 || "$2" == --* ]]; then
          echo "ERROR: --admin-password には値が必要です。" >&2
          exit 1
        fi
        UP_ADMIN_PASSWORD="$2"
        shift 2
        ;;
      -h | --help | help)
        usage
        exit 0
        ;;
      *)
        echo "ERROR: 不明なオプション: $1" >&2
        usage
        exit 1
        ;;
    esac
  done
}

run_up() {
  parse_up_args "$@"
  prepare_auth
  run_apply

  if [[ ! -x "$PACKAGE_MIGRATE" ]]; then
    echo "ERROR: $PACKAGE_MIGRATE がありません（実行権限を確認してください）。" >&2
    exit 1
  fi
  echo "→ package-migrate.sh"
  "$PACKAGE_MIGRATE"

  if [[ ! -x "$INVOKE_MIGRATE" ]]; then
    echo "ERROR: $INVOKE_MIGRATE がありません（実行権限を確認してください）。" >&2
    exit 1
  fi
  echo "→ invoke-migrate.sh"
  "$INVOKE_MIGRATE"

  SEED_ADMIN_CREATED_PASSWORD=""
  if [[ -n "$UP_ADMIN_EMAIL" ]]; then
    local password="$UP_ADMIN_PASSWORD"
    if [[ -z "$password" ]]; then
      password="$(generate_temp_password)"
    fi
    seed_admin_user "$UP_ADMIN_EMAIL" "$UP_ADMIN_NAME" "$password"
  else
    echo "→ --admin-email がないため Cognito / seed-admin はスキップします"
  fi

  write_frontend_env

  cat <<EOF

========================================
OK: 本体の立ち上げが完了しました。
EOF
  if [[ -n "$UP_ADMIN_EMAIL" ]]; then
    if [[ -n "$SEED_ADMIN_CREATED_PASSWORD" ]]; then
      cat <<EOF

仮パスワード（この画面にだけ表示。コミットしない）:
  ${SEED_ADMIN_CREATED_PASSWORD}

初回ログイン後にパスワード変更を求められます。
EOF
    else
      cat <<EOF

Cognito ユーザー ${UP_ADMIN_EMAIL} は既存のため、仮パスワードは発行していません。
EOF
    fi
  fi
  cat <<'EOF'

ローカルフロント:
  cd frontend && npm run dev
  http://localhost:3000
========================================
EOF
}

run_down() {
  require_cmd terraform
  prepare_auth
  ensure_tfvars
  echo ""
  echo "警告: 本体（infra/envs/dev）の NAT Gateway / RDS / Cognito / Lambda などが削除されます。"
  echo "infra/bootstrap（tfstate 用 S3 / DynamoDB）は削除しません。"
  if ! confirm_yes "本体を destroy しますか? [y/N] "; then
    echo "中止しました（destroy なし）。"
    exit 1
  fi
  cd "$DEV_DIR"
  echo "→ terraform init -backend-config=backend.hcl"
  terraform init -input=false -backend-config=backend.hcl
  echo "→ terraform destroy -auto-approve（確認はスクリプト側で実施済み）"
  terraform destroy -input=false -auto-approve
  echo "OK: 本体の destroy 完了。bootstrap は残しています。"
}

main() {
  if [[ $# -lt 1 ]]; then
    usage
    exit 1
  fi

  local cmd="$1"
  shift
  case "$cmd" in
    auth)
      prepare_auth
      echo "OK: 認証準備完了（terraform は実行していません）"
      ;;
    plan)
      prepare_auth
      run_plan
      ;;
    apply)
      prepare_auth
      run_apply
      ;;
    up)
      run_up "$@"
      ;;
    down)
      if [[ $# -gt 0 ]]; then
        echo "ERROR: down は追加引数を取りません。" >&2
        usage
        exit 1
      fi
      run_down
      ;;
    -h | --help | help)
      usage
      ;;
    *)
      echo "ERROR: 不明なサブコマンド: $cmd" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"

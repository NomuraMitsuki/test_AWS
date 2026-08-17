#!/usr/bin/env bash
# aws login（必要時）+ export-credentials のあと、本体（infra/envs/dev）向け terraform を実行する。
# infra/bootstrap は対象外（bootstrap は cd infra/bootstrap して直接 terraform する）。
# 使い方（リポジトリルートから）:
#   ./infra/scripts/tf-dev.sh auth
#   ./infra/scripts/tf-dev.sh plan
#   ./infra/scripts/tf-dev.sh apply
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DEV_DIR="${REPO_ROOT}/infra/envs/dev"
CHECK_AUTH="${SCRIPT_DIR}/check-aws-auth.sh"
PLAN_FILE="${DEV_DIR}/tfplan"

REGION="${AWS_DEFAULT_REGION:-${AWS_REGION:-ap-northeast-1}}"
export AWS_DEFAULT_REGION="$REGION"
export AWS_REGION="$REGION"

usage() {
  cat <<'EOF'
使い方: ./infra/scripts/tf-dev.sh <auth|plan|apply>

  auth   aws login（必要時）と export-credentials、認証確認のみ
  plan   上記のあと terraform init / plan -out=tfplan
  apply  内部で plan し直し、yes 確認のあと terraform apply tfplan

aws login の資格情報は Terraform が直接拾えないことがあるため、
必ず aws configure export-credentials を環境変数へ展開してから実行する。
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
  printf "この plan を apply しますか? [y/N] "
  local answer
  read -r answer
  if [[ ! "$answer" =~ ^[yY]$ ]]; then
    echo "中止しました（apply なし）。"
    exit 1
  fi
  echo "→ terraform apply tfplan"
  terraform apply -input=false "$PLAN_FILE"
  echo "OK: apply 完了。OIDC 用に次を控えてください:"
  terraform output gha_infra_role_arn
  terraform output gha_backend_role_arn
}

main() {
  if [[ $# -lt 1 ]]; then
    usage
    exit 1
  fi

  local cmd="$1"
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

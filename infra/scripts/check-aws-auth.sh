#!/usr/bin/env bash
# AWS 資格情報が terraform plan/apply に使えるか確認する。
set -euo pipefail

REGION="${AWS_DEFAULT_REGION:-${AWS_REGION:-ap-northeast-1}}"
export AWS_DEFAULT_REGION="$REGION"

if ! command -v aws >/dev/null 2>&1; then
  echo "ERROR: aws CLI が見つかりません。AWS CLI v2 をインストールしてください。"
  exit 1
fi

if ! command -v terraform >/dev/null 2>&1; then
  echo "WARN: terraform が見つかりません（認証チェック自体は続行します）。"
fi

echo "→ aws sts get-caller-identity (region=${REGION})"
if ! CALLER="$(aws sts get-caller-identity --output json 2>&1)"; then
  cat <<'EOF'
ERROR: AWS 資格情報がありません、または無効です。

次のいずれかを設定してください（詳細: docs/infra/aws-auth-bootstrap.md）:
  - 環境変数: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY [/ AWS_SESSION_TOKEN]
  - プロファイル: AWS_PROFILE + aws sso login（または aws configure）
EOF
  echo "$CALLER" >&2
  exit 1
fi

echo "$CALLER" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("OK: Account={} Arn={}".format(d["Account"], d["Arn"]))'

echo "→ 簡易権限チェック (ec2:DescribeRegions)"
if ! aws ec2 describe-regions --region-names "$REGION" --output text >/dev/null 2>&1; then
  echo "WARN: ec2:DescribeRegions に失敗しました。Terraform 実行時に権限不足の可能性があります。"
  exit 1
fi

echo "OK: terraform plan/apply 用の認証準備が整っています。"

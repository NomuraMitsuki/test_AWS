# Terraform state bootstrap（W-109）

本体（`infra/envs/dev`）のリモート state 用に、S3 バケットと DynamoDB ロックテーブルだけを作る独立スタック。

- このディレクトリの state は **ローカル**でよい
- **`terraform destroy` しない**（学習終了時も本体だけ destroy し、ここは残すか最後に明示的に消す）
- `./infra/scripts/tf-dev.sh` は使わない（本体専用）
- Cloud Agent では **apply しない**（エフェメラル環境で state を失う）

## 手順（ユーザーの Mac）

認証は `aws login` + `export-credentials`。詳細は [docs/infra/aws-auth-bootstrap.md](../../docs/infra/aws-auth-bootstrap.md)。

```bash
cd infra/bootstrap
eval "$(aws configure export-credentials --format env)"  # aws login 利用時
terraform init
terraform apply
terraform output
```

出力を `infra/envs/dev/backend.hcl` に転記して **コミットする**（gitignore しない。CI が読む）:

```hcl
bucket         = "<bucket_name の出力>"
dynamodb_table = "<dynamodb_table_name の出力>"
```

続けて本体の init / apply は認証手順書の §C 以降を参照。

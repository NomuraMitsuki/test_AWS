# 本体の立ち上げ / 停止を少数コマンドにする（W-281）

**日付**: 2026-08-17  
**ステータス**: Approved（エージェントは apply / destroy / invoke しない）  
**WBS**: W-281

## 1. ゴール

destroy した本体スタックを、Mac から **数コマンド**で再 apply → migrate zip → SQL → 初回 admin → `frontend/.env.local` まで戻せるようにする。停止も同様に 1 コマンド。

## 2. 非ゴール

- エージェントからの apply / destroy / Lambda invoke
- bootstrap（tfstate S3）の destroy
- Amplify GitHub 接続の必須化
- OIDC の信頼ポリシー修正

## 3. 使い方（完成形）

リポジトリルートから:

```bash
./infra/scripts/tf-dev.sh up --admin-email you@example.com
./infra/scripts/tf-dev.sh down
```

`up` は課金リソース作成前に `[y/N]`。`down` は destroy 前に `[y/N]`。bootstrap は触らない。

`up` の流れ:

1. 期限切れ `AWS_*` を捨て、login + `export-credentials`（既存 `tf-dev.sh`）
2. `terraform apply`（本体。既存 apply と同じ確認）
3. `package-migrate.sh`（Linux / Python 3.12 wheel + UpdateFunctionCode）。main に無ければこの PR で追加
4. `invoke-migrate.sh`（SQL 001〜003）
5. `--admin-email` があれば Cognito `AdminCreateUser`（既存ならスキップ）+ グループ `admin` + seed。仮パスワードは生成して画面にだけ出す（コミットしない）
6. `frontend/.env.local` を terraform output から書く（gitignore 済み）

完了後に出す案内: 仮パスワード、`cd frontend && npm run dev`

`AWS_PAGER` は空にして JSON で止まらないようにする。

## 4. 検証

- `bash -n` でスクリプト構文
- `terraform fmt` / `init -backend=false` / `validate`（Terraform 変更があれば）
- apply / destroy / invoke はしない

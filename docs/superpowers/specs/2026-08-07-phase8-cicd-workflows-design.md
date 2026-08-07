# Phase 8 — GitHub Actions CI/CD 完成設計（W-260）

**日付**: 2026-08-07  
**ステータス**: Approved（Secrets 実登録・apply なし）  
**WBS**: W-260  
**CI 正本**: [docs/cicd/github-actions.md](../../cicd/github-actions.md)

## 1. ゴール

GitHub Actions の **backend / frontend / infra** ワークフローを設計どおり「完成」形にし、PR では品質ゲートが必須、main ではデプロイ／apply ジョブが **Secrets があれば実行・無ければスキップ＋注記** となるようにする。ローカルでの terraform apply や GitHub Secrets の実登録は行わない（W-109）。

## 2. 非ゴール

- W-109（再 apply・`AWS_ROLE_ARN_*` 登録・リモート state 運用開始）
- W-270（CloudWatch ダッシュボード／アラーム仕上げ）
- エージェント環境からの AWS 操作・Secrets 書き込み
- Amplify Hosting の GitHub 自動ビルド設定変更（W-250 Terraform 側。本 Phase は Actions の任意 `start-job` のみ）

## 3. 方針（採用案 A）

品質ゲートは常に必須。デプロイ系は OIDC / Amplify 用 Secret・Variable 未設定でも workflow 全体を赤にしない（スキップまたは注記）。W-109 完了後に同じ YAML がそのまま生きる。

## 4. ワークフロー

### 4.1 `backend.yml`（新規）

| トリガー | 内容 | 必須 |
|----------|------|------|
| PR（`backend/**`） | Python 3.12、`pytest` | 必須 |
| push `main`（`backend/**`） | health / attendance / leave / users / exports を zip → OIDC（`AWS_ROLE_ARN_BACKEND`）で `lambda:UpdateFunctionCode` | Secret ありで実行。未設定はスキップ＋注記 |

- 関数名は repository variables（例: `LAMBDA_HEALTH_NAME` 等）または `terraform output` と揃う命名を docs／`.env` 例で固定
- 依存がある関数は `requirements.txt` を含めてパッケージ

### 4.2 `frontend.yml`（拡張）

| トリガー | 内容 | 必須 |
|----------|------|------|
| PR / push（lint/build） | 現状維持（ダミー `NEXT_PUBLIC_*`） | 必須 |
| push `main` | 任意: `aws amplify start-job`（`AMPLIFY_APP_ID`、branch=`main`） | Variable/Secret 未設定ならスキップ |

Hosting の GitHub 接続による自動ビルドを主経路とする。Actions の `start-job` は補助。

### 4.3 `infra.yml`（拡張）

| トリガー | 内容 | 必須 |
|----------|------|------|
| 常時 | `fmt` / `validate` | 必須 |
| PR | `plan`（OIDC。失敗時注記） | validate 必須。plan は Secret 依存 |
| push `main` | `apply` ジョブ骨格（`environment: dev` → OIDC → `terraform apply`） | Secret / state 未整備時はスキップまたは continue-on-error＋注記 |

運用開始（実際に apply を通す）は W-109（Secrets・再 apply・リモート state）後と明記する。

## 5. 必要な GitHub 設定（登録は W-109）

| 種類 | 名前 | 用途 |
|------|------|------|
| Secret | `AWS_ROLE_ARN_INFRA` | infra plan/apply |
| Secret | `AWS_ROLE_ARN_BACKEND` | Lambda 更新 |
| Variable 等 | `AMPLIFY_APP_ID`（任意） | `amplify start-job` |
| Variable 等 | Lambda 関数名（任意） | backend デプロイ |

`AWS_REGION=ap-northeast-1`。Environment `dev` は apply ジョブで使用（reviewers は W-109 以降で必須化してよい）。

## 6. 検証

- backend: ローカル `pytest` グリーン
- ワークフロー: パスフィルタ・条件分岐が意図どおり（可能なら `actionlint`）
- docs: [github-actions.md](../../cicd/github-actions.md) の現状／目標を W-260 実装に合わせて更新
- apply / Secrets 実登録はしない

## 7. 完了後の位置づけ

- WBS W-260 完了（親がステータス更新）
- handoff / README 索引同期
- 次: **W-109**（再 apply → Secrets）または **W-270**

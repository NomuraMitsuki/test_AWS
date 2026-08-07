# Phase 2 — HTTP API + JWT + health Lambda 設計

**日付**: 2026-08-07  
**ステータス**: Approved（チャット合意）  
**WBS**: W-200  
**親スペック**: [2026-08-05-attendance-aws-design.md](2026-08-05-attendance-aws-design.md)

## 1. ゴール

`dev` 向けに API Gateway HTTP API、Cognito JWT authorizer、認証不要の `GET /health`、および health 用 Python Lambda をリポジトリ上で再現可能にする。

本 Phase では **AWS への apply / 実デプロイは行わない**（コード・Terraform・単体テスト・ドキュメントまで）。課金抑制のため、検証は `pytest` と `terraform validate` とする。

## 2. 非ゴール

- 勤怠・休暇・ユーザー・エクスポート API（W-210〜）
- health 以外のルート実装
- Lambda の VPC 配置（RDS 接続は後続ドメイン Lambda）
- GitHub Secrets / OIDC CI 有効化（W-109）
- リモート state 化
- Amplify / フロント

## 3. 構成

```text
backend/
  health/
    handler.py
    requirements.txt      # ランタイム依存なし（空またはコメントのみ可）
  tests/
    test_health.py
infra/modules/api/        # HTTP API / JWT / Lambda / IAM / ルート
infra/envs/dev/           # module.api を cognito 出力に接続
```

## 4. Lambda（health）

| 項目 | 決定 |
|------|------|
| ランタイム | Python 3.12 |
| ハンドラ | `handler.handler` |
| VPC | なし（ヘルスチェックのみ。DB 非接続） |
| 入力 | API Gateway HTTP API（payload format 2.0）イベント |
| 成功応答 | HTTP 200、`{"status":"ok"}`（[OpenAPI](../../api/openapi.yaml) `/health` に準拠） |
| パッケージ | Terraform `archive_file` で `backend/health` を zip |

JWT 検証・グループ判定は行わない（ルート側で authorizer を付けない）。

## 5. API Gateway（HTTP API）

| 項目 | 決定 |
|------|------|
| プロトコル | HTTP API |
| JWT authorizer | Cognito User Pool issuer + App Client ID（audience） |
| ルート | `GET /health` → health Lambda。**authorizer なし**（唯一の JWT 例外） |
| ステージ | `$default`（簡易。学習用） |
| CORS | 本 Phase では未設定（フロント接続時に追加） |

後続ルート（勤怠等）を追加するときは、同一 API に JWT 必須ルートを足す前提とする。ドメイン別 Lambda は親スペックどおり。

## 6. Terraform モジュール境界

`infra/modules/api` が担当する主なリソース:

- IAM role（基本実行ロール）
- `aws_lambda_function`（health）
- `aws_apigatewayv2_api` / stage
- `aws_apigatewayv2_authorizer`（JWT / Cognito）
- `aws_apigatewayv2_integration` / `route`（`GET /health`）
- `aws_lambda_permission`（API からの invoke）

入力（変数）の例:

- `name_prefix`
- `cognito_user_pool_id` / `cognito_client_id` / `cognito_issuer_url`（または pool id + region から構築）
- health ソースパス（または固定相対パス）

出力の例:

- `api_endpoint`
- `health_lambda_function_name`
- `http_api_id`

`infra/envs/dev` で `module.cognito` の出力を渡し、`outputs.tf` に API エンドポイントを露出する。

## 7. 認可モデルとの関係

親スペックの認可:

1. API Gateway で JWT 検証（例外: `GET /health` のみ）← **本 Phase で基盤を置く**
2. Lambda 内の Groups / DB ロール確認 ← 後続 Phase

本 Phase では (1) の JWT authorizer リソースを作成するが、health ルートには紐付けない。authorizer が「存在するが未使用ルート向け」でもよい（後続で紐付け）。未使用 authorizer を避けるなら、コメントと変数で用意し初回はルート無しでも可だが、**学習上は authorizer リソースを作成済みにする**。

## 8. 検証

| 検証 | 内容 |
|------|------|
| 単体テスト | `backend/tests/test_health.py` — ハンドラが 200 と `status=ok` を返す |
| Terraform | `fmt` / `validate`（apply なし） |
| 手動 E2E | 対象外（apply しない） |

## 9. ドキュメント・WBS

- 本スペックを追加
- 実装計画を `docs/superpowers/plans/` または `docs/plans/` に追加
- `docs/wbs.md` の W-200 を進行中→完了（実装 PR 時）
- `docs/handoff.md` / `infra/README.md` を必要最小限更新
- 親スペック §8 フェーズ 3 との対応を明示（本ドキュメントへのリンクで可）

## 10. リスク・注意

- apply 前に Cognito が無いと JWT authorizer は実動作確認できない → 本 Phase では validate まで
- `archive_file` はローカルパス依存。CI の `validate` ではソースがリポジトリにあれば足りる
- 後続で Lambda を VPC に入れる場合、health は VPC 外のまま残してよい（障害時の疎通確認用）

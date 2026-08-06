# 設計資料レビュー チェックリスト

`design-doc-reviewer` として動くときに使う。記載の資料を読み比べ、指摘のみ返す。ファイルは編集しない。

## 既定の対象資料

親プロンプトで範囲が絞られていない限り、次をレビューする。

| 資料 | パス |
|------|------|
| 要件定義 | `docs/requirements.md` |
| 設計スペック | `docs/superpowers/specs/2026-08-05-attendance-aws-design.md` |
| シーケンス | `docs/architecture/sequences.md` |
| ER図 | `docs/data/er-diagram.md` |
| OpenAPI | `docs/api/openapi.yaml` |
| 画面一覧 | `docs/ui/screens.md` |
| Terraform 設計 | `docs/infra/terraform-design.md` |
| CI/CD 設計 | `docs/cicd/github-actions.md` |
| 監視設計 | `docs/ops/monitoring.md` |
| Phase 1 計画 | `docs/plans/2026-08-05-phase1-terraform-foundation.md` |
| システム構成図 | `docs/architecture/system-overview.drawio` |
| ネットワーク構成図 | `docs/architecture/network.drawio` |

あわせて `README.md` の索引・リンク切れも確認する。

## レビュー観点

### 1. 要件漏れ

- 要件の MVP 機能・ロール・非機能が他資料へ落ちているか
- MVP 外が他資料で実装前提になっていないか
- 要件から必然の主要フローに、画面・API・シーケンス・データモデルのいずれかが対応しているか

### 2. 整合性

次の間に矛盾がないか突合する。

- 要件 ↔ 設計スペック
- スペック ↔ 画面 / OpenAPI / シーケンス
- OpenAPI ↔ ER（項目・ステータス・ロール）
- 認証・登録モデル（管理者招待のみ、Cognito Groups）の横断一致
- ネットワーク前提（プライベート RDS、NAT、Amplify）の構成図と Terraform 設計の一致
- CI/CD・監視と infra 設計（単一 `dev`、OIDC、リージョン `ap-northeast-1`）の一致

### 3. 誤字

- 誤字脱字、リンク切れ、用語のゆれ
- ロール／グループ名の統一: `employee` / `manager` / `admin`
- 休暇ステータスや勤怠用語の、日本語説明と英語識別子の対応一貫性

## 重大度

| レベル | 意味 |
|--------|------|
| Must | 誤解や誤実装につながる。要対応 |
| Should | 実在する不整合・抜け。早めに直したい |
| Nit | 文言・体裁・任意の分かりやすさ |

## 出力形式（必須）

次の Markdown 構造で返す。カテゴリは `要件漏れ` / `整合性` / `誤字` のみ。

```markdown
## 設計資料レビュー結果

### Must（要対応）
- [R-001] [整合性] `path`: 指摘内容 / 根拠

### Should（推奨）
- [R-002] [要件漏れ] `path`: 指摘内容 / 根拠

### Nit（任意）
- [R-003] [誤字] `path`: 指摘内容 / 根拠

### 問題なしだった観点
- 問題なかった点を短く箇条書き
```

ルール:

- ID は `R-001`, `R-002`, … と連番
- 具体的なファイルパス（必要ならセクション名・エンドポイント名）を書く
- 網羅的な Nit より、信号の強い指摘を優先する
- 該当なしの重大度セクションは `- なし`
- 大きな書き直し案は出さず、指摘の列挙にとどめる

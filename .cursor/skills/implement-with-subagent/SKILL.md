---
name: implement-with-subagent
description: Use when implementing WBS tasks or multi-step feature/bugfix work so the parent delegates coding to implementation-worker; when the user says 実装を進めて / WBS を実装して / implement with subagent / サブエージェントに実装させて for this repo.
---

# 実装のサブエージェント委譲

## 概要

親エージェントのコンテキストを小さく保つため、複数ステップの実装は writable の **implementation-worker** へ委譲する。設計レビュー（`review-design-docs`）と同型の起動パターン。

手動依頼に加え、ルール [`.cursor/rules/delegate-implementation.mdc`](../../rules/delegate-implementation.mdc) に該当する実装依頼でも実行する。

## 親エージェント向け手順

1. 親自身で `infra/` / `backend/` / `frontend/` を横断読込して実装を始めない（方針・受け入れ条件の把握に必要な最小限のみ）。
2. 作業ブランチを用意する（未作成なら `cursor/<descriptive-name>-a099` などリポジトリ規約に従う）。
3. **implementation-worker** サブエージェントを **フォアグラウンド**（完了待ち）で起動する。
4. Task プロンプトに次をすべて含める:
   - **WBS ID**（あれば）と **ゴール / 非ゴール**
   - 参照すべきスペック・計画・OpenAPI 等の **パス**（親が全文を貼らない）
   - **ブランチ名**
   - **検証コマンド**（例: `pytest`, `cd infra/envs/dev && terraform validate`）
   - **コミット方針**（日本語メッセージ可、秘密情報を含めない）
   - **PR は作成しない**（push まで、または親が指定した範囲まで）
   - 定義ファイル `.cursor/agents/implementation-worker.md` に従うこと
5. サブエージェントの完了報告を受け、ユーザーへ簡潔に要約する。
   - 親が同じ実装をやり直し・上書き拡張しない。
   - サブエージェント失敗時は失敗を報告し、親側の全実装へ黙ってフォールバックしない。
6. その後の **設計資料レビュー**（該当時）と **PR 作成** は親が行う（`pr-design-review` / `review-design-docs`）。

## 使わない場面

- 1 ファイルの文言修正など極小変更（親がそのまま直してよい）
- ユーザーが「親でやって」「サブエージェント不要」と明示した場合
- 設計資料レビューのみ（`review-design-docs` / `design-doc-reviewer` を使う）
- 調査だけ（実装なし）。探索は `explore` 等でよい

## 子にやらせないこと（親が保持）

- `ManagePullRequest` の `create_pr`
- `docs/` 横断の設計資料レビュー
- ユーザーとの方針合意・スコープ変更の最終決定

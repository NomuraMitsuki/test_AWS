---
name: review-design-docs
description: Use when the user asks to review design docs, before creating a PR that touches docs/ or design-related files, check docs consistency, find requirement gaps, or says 設計資料をレビューして / ドキュメントの整合性を確認して for this repo.
---

# 設計資料レビュー

## 概要

このリポジトリの設計資料を構造化レビューする。親エージェントのコンテキストを小さく保つため、横断読込は readonly サブエージェントへ委譲する。

手動依頼に加え、**設計関連ファイルを含む PR を新規作成する直前**にも実行する（ルール: `.cursor/rules/pr-design-review.mdc`）。ファイル変更の都度は実行しない。

## 親エージェント向け手順

1. 親自身で `docs/` 全体を開いたりざっと読んだりしない。
2. 親コンテキストに `.cursor/skills/review-design-docs/references/checklist.md` を読み込まない（サブエージェントが読む）。
3. **design-doc-reviewer** サブエージェントを **フォアグラウンド**（完了待ち）で起動する。
4. Task プロンプトに次をすべて含める:
   - 既定のレビュー対象: `docs/`（変更セットでパスが絞れる場合はそれを優先しつつ、関連資料との突合は維持）
   - **PR に含める変更ファイル一覧**（PR 作成前レビュー時は必須）
   - ユーザー指定の焦点（例: 「API のみ」「認証まわり」）
   - 先に `.cursor/skills/review-design-docs/references/checklist.md` を読むこと
   - チェックリストの重大度・カテゴリ・出力形式に厳密に従うこと
   - readonly: ファイルを編集せず、指摘のみ返すこと
5. サブエージェントの結果をユーザーへ提示する。
   - 見出しの軽い整形は可。
   - 親が docs を再読込してレビューを上書き・拡張しない。
   - サブエージェント失敗時は失敗を報告し、親側の全件レビューへ黙ってフォールバックしない。
6. PR 作成前レビューで Must が出た場合は、ルール `pr-design-review` に従い修正または WBS 転記してから PR を作る。

## 使わない場面

- `infra/` / `backend/` / `frontend/` の実装コードレビュー
- 設計ファイルを触らない PR
- ファイルを1つ編集するたびの自動レビュー（都度実行はしない）
- ユーザーがレビュー不要と明示した場合
- 既知の単一ファイルに関する一行の事実確認で、PR を作らないとき

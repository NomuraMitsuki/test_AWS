---
name: review-design-docs
description: Use when the user asks to review design docs, check docs consistency, find requirement gaps in docs, or says 設計資料をレビューして / ドキュメントの整合性を確認して for this repo.
---

# 設計資料レビュー

## 概要

このリポジトリの設計資料を構造化レビューする。親エージェントのコンテキストを小さく保つため、横断読込は readonly サブエージェントへ委譲する。

## 親エージェント向け手順

1. 親自身で `docs/` 全体を開いたりざっと読んだりしない。
2. 親コンテキストに `.cursor/skills/review-design-docs/references/checklist.md` を読み込まない（サブエージェントが読む）。
3. **design-doc-reviewer** サブエージェントを **フォアグラウンド**（完了待ち）で起動する。
4. Task プロンプトに次をすべて含める:
   - 既定のレビュー対象: `docs/`（ユーザーがパスを指定した場合のみ絞る）
   - ユーザー指定の焦点（例: 「API のみ」「認証まわり」）
   - 先に `.cursor/skills/review-design-docs/references/checklist.md` を読むこと
   - チェックリストの重大度・カテゴリ・出力形式に厳密に従うこと
   - readonly: ファイルを編集せず、指摘のみ返すこと
5. サブエージェントの結果をユーザーへ提示する。
   - 見出しの軽い整形は可。
   - 親が docs を再読込してレビューを上書き・拡張しない。
   - サブエージェント失敗時は失敗を報告し、親側の全件レビューへ黙ってフォールバックしない。

## 使わない場面

- `infra/` / `backend/` / `frontend/` の実装コードレビュー
- 設計資料の新規作成・大幅な書き直し（通常の編集フローで行う）
- 既知の単一ファイルに関する一行の事実確認（レビュー起動は不要）

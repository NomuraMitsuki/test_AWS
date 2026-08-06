# Design docs review checklist

Use this checklist when acting as `design-doc-reviewer`. Read the listed docs, compare them, and return findings only. Do not edit files.

## Default document set

Review these paths unless the parent prompt narrows the scope:

| Doc | Path |
|-----|------|
| Requirements | `docs/requirements.md` |
| Design spec | `docs/superpowers/specs/2026-08-05-attendance-aws-design.md` |
| Sequences | `docs/architecture/sequences.md` |
| ER diagram | `docs/data/er-diagram.md` |
| OpenAPI | `docs/api/openapi.yaml` |
| Screens | `docs/ui/screens.md` |
| Terraform design | `docs/infra/terraform-design.md` |
| CI/CD design | `docs/cicd/github-actions.md` |
| Monitoring | `docs/ops/monitoring.md` |
| Phase 1 plan | `docs/plans/2026-08-05-phase1-terraform-foundation.md` |
| System diagram | `docs/architecture/system-overview.drawio` |
| Network diagram | `docs/architecture/network.drawio` |

Also skim `README.md` for index/link drift against the above.

## Review categories

### 1. 要件漏れ

- MVP features, roles, and non-functionals in requirements are reflected in the other docs
- MVP-out items are not accidentally treated as in-scope elsewhere
- Critical flows implied by requirements have at least one of: screen, API, sequence, or data model coverage

### 2. 整合性

Cross-check for contradictions among:

- Requirements ↔ design spec
- Spec ↔ screens / OpenAPI / sequences
- OpenAPI ↔ ER (fields, statuses, roles)
- Auth/registration model (admin invite only, Cognito groups) across docs
- Network assumptions (private RDS, NAT, Amplify) across architecture + Terraform design
- CI/CD and monitoring notes vs infra design (env = single `dev`, OIDC, region `ap-northeast-1`)

### 3. 誤字

- Typos, broken links, inconsistent product terms
- Role/group naming consistency: `employee` / `manager` / `admin`
- Leave statuses / attendance terms consistent across Japanese and English identifiers

## Severity

| Level | Meaning |
|-------|---------|
| Must | Blocks correct understanding or would cause wrong implementation |
| Should | Real inconsistency or gap; fix soon |
| Nit | Wording, minor polish, optional clarity |

## Output format (required)

Return markdown exactly in this structure. Categories must be one of `要件漏れ` / `整合性` / `誤字`.

```markdown
## 設計資料レビュー結果

### Must（要対応）
- [R-001] [整合性] `path`: finding / evidence

### Should（推奨）
- [R-002] [要件漏れ] `path`: finding / evidence

### Nit（任意）
- [R-003] [誤字] `path`: finding / evidence

### 問題なしだった観点
- Short bullets for areas that looked consistent
```

Rules:

- Use stable IDs `R-001`, `R-002`, …
- Cite concrete file paths (and section/endpoint names when useful)
- Prefer fewer high-signal findings over exhaustive nits
- If a severity section has no items, write `- なし`
- Do not propose large rewrites; list issues only

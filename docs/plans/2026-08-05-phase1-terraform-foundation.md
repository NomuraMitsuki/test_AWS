# Phase 1: Terraform Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `dev` 環境向けに VPC・Cognito・RDS・S3・Secrets Manager・CloudWatch 骨格・GitHub OIDC を Terraform で再現可能な状態にする。

**Architecture:** `infra/modules/*` に責務分割し、`infra/envs/dev` から呼び出す。Lambda / API Gateway の本実装は Phase 2 以降。本 Phase ではプレースホルダ Lambda（health）まで含めてもよい。

**Tech Stack:** Terraform >= 1.5, AWS provider ~> 5.x, region `ap-northeast-1`

## Global Constraints

- Environment: `dev` only
- Region: `ap-northeast-1`
- RDS: `db.t4g.micro`, single-AZ, private subnet, no public access
- NAT Gateway: 1
- Cognito: self-signup disabled; groups `employee` / `manager` / `admin`
- S3: Block Public Access on; exports bucket only
- Auth to AWS from CI: OIDC (no long-lived keys in repo)
- Resource name prefix: `attendance-dev-*`
- Spec: [docs/superpowers/specs/2026-08-05-attendance-aws-design.md](../superpowers/specs/2026-08-05-attendance-aws-design.md)
- Terraform design: [docs/infra/terraform-design.md](../infra/terraform-design.md)

---

## File map (to create)

```text
infra/
  versions.tf                 # shared version constraints (optional root)
  envs/dev/
    backend.tf                # S3 backend (or local for first boot)
    providers.tf
    main.tf
    variables.tf
    outputs.tf
    terraform.tfvars.example
  modules/
    network/
    cognito/
    data/
    storage/
    monitoring/
    github_oidc/
    api/                      # optional in Phase 1: HTTP API + health Lambda stub
```

---

## Task 1: Bootstrap Terraform layout

**Files:**
- Create `infra/envs/dev/providers.tf`
- Create `infra/envs/dev/variables.tf`
- Create `infra/envs/dev/terraform.tfvars.example`
- Create `infra/envs/dev/backend.tf` (commented S3 backend + local default)

- [ ] Create directory tree under `infra/`
- [ ] Add provider with `region = var.aws_region` default `ap-northeast-1`
- [ ] Add variables: `project_name`, `environment`, `aws_region`, `github_org_repo`
- [ ] Run `terraform fmt -recursive` and `terraform init` (local backend)
- [ ] Commit: `chore(infra): bootstrap Terraform layout for dev`

---

## Task 2: Network module

**Files:**
- Create `infra/modules/network/main.tf`
- Create `infra/modules/network/variables.tf`
- Create `infra/modules/network/outputs.tf`
- Wire module in `infra/envs/dev/main.tf`

**Deliverable:** VPC `10.0.0.0/16`, 2 public + 2 private subnets across 2 AZs, IGW, single NAT, route tables, security groups for Lambda and RDS (RDS allows 5432 from Lambda SG only).

- [ ] Implement VPC / subnets / NAT / routes / SGs
- [ ] Export `vpc_id`, subnet IDs, SG IDs
- [ ] `terraform plan` shows expected resources
- [ ] Commit: `feat(infra): add network module with private RDS path`

---

## Task 3: Cognito module

**Files:**
- Create `infra/modules/cognito/*`
- Wire in `envs/dev`

**Deliverable:** User Pool (no self-signup), app client (no secret for SPA), groups `employee`/`manager`/`admin`.

- [ ] Implement pool, client, groups
- [ ] Output `user_pool_id`, `client_id`, `issuer_url`
- [ ] Commit: `feat(infra): add Cognito user pool and groups`

---

## Task 4: Data module (RDS + Secrets)

**Files:**
- Create `infra/modules/data/*`

**Deliverable:** Secrets Manager secret for master password, DB subnet group on private subnets, PostgreSQL `db.t4g.micro`, storage encrypted, publicly_accessible=false, SG from network module.

- [ ] Create random password + secret
- [ ] Create RDS instance
- [ ] Output endpoint, secret ARN, db name
- [ ] Commit: `feat(infra): add private RDS PostgreSQL and Secrets Manager`

---

## Task 5: Storage module (S3 exports)

**Files:**
- Create `infra/modules/storage/*`

**Deliverable:** Private exports bucket with Block Public Access, SSE, deny insecure transport policy.

- [ ] Implement bucket + public access block + encryption
- [ ] Output bucket name / ARN
- [ ] Commit: `feat(infra): add private S3 exports bucket`

---

## Task 6: Monitoring skeleton

**Files:**
- Create `infra/modules/monitoring/*`

**Deliverable:** CloudWatch dashboard shell, SNS topic (email subscription optional via variable), placeholder alarms that reference future Lambda/API names via variables.

- [ ] Dashboard with text/markdown widget describing upcoming metrics
- [ ] SNS topic for alarms
- [ ] Commit: `feat(infra): add CloudWatch monitoring skeleton`

---

## Task 7: GitHub OIDC module

**Files:**
- Create `infra/modules/github_oidc/*`

**Deliverable:** OIDC provider (if not exists), IAM roles for infra/backend deploy scoped to `repo:${github_org_repo}:*`.

- [ ] Implement OIDC provider + roles with least-privilege stubs
- [ ] Output role ARNs for GitHub Environments
- [ ] Commit: `feat(infra): add GitHub Actions OIDC roles`

---

## Task 8: Dev composition + docs sync

**Files:**
- Update `infra/envs/dev/main.tf` to compose all modules
- Update `infra/envs/dev/outputs.tf`
- Update `docs/infra/terraform-design.md` if module outputs differ
- Add stub workflow `.github/workflows/infra.yml` (fmt/validate/plan only; apply gated)

- [ ] Compose modules with consistent tags `Project=attendance`, `Environment=dev`
- [ ] Document apply prerequisites in README (AWS credentials / OIDC)
- [ ] Commit: `feat(infra): compose dev stack and add plan workflow`

---

## Task 9: Verification gate（W-108）

完了条件: fmt / validate / 資格情報付き plan。OIDC 有効化のため初回 apply も含む（認証・state 手順は [aws-auth-bootstrap.md](../infra/aws-auth-bootstrap.md)）。

- [x] `terraform fmt -check -recursive`（コード側は PR #4 時点で済み）
- [x] `terraform validate` in `envs/dev`
- [ ] `terraform plan` against a sandbox account（資格情報＋永続 state 環境）
- [ ] Confirm no public RDS / no public S3 in plan output
- [ ] 初回 `terraform apply`（OIDC ロール作成）と GitHub Secrets 登録
- [ ] Push branch and open/update PR

---

## Out of scope for Phase 1

- Domain Lambda business logic
- Amplify app / Next.js
- Full alarm thresholds tied to real functions (finalize in Phase 9)
- Multi-environment workspaces

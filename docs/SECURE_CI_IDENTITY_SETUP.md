# Secure CI Identity Setup (GitHub OIDC + GCP)

This project is configured to use GitHub OIDC federation for Google Cloud authentication in CI.

## Why this setup

- No long-lived JSON key in GitHub secrets.
- No personal email identity in CI.
- Uses a dedicated user-managed service account with least privilege.

## 1) Create or confirm a runtime/CI service account

Example identity:

- `careertrojansupport@<project>.iam.gserviceaccount.com`

Grant only required roles for CI tasks (build/test/deploy scope).

## 2) Configure Workload Identity Federation

Create:

- Workload Identity Pool
- OIDC Provider for `token.actions.githubusercontent.com`

Use attribute conditions that pin access to your GitHub org/repo/branch.

## 3) Bind the provider principal to the service account

Grant `roles/iam.workloadIdentityUser` on the service account to the GitHub principal set.

## 4) Configure repository variables in GitHub

Add these Repository Variables:

- `GCP_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER` (full provider resource path)
- `GCP_SERVICE_ACCOUNT` (service account email)

For deploy workflows, also add:

- `GCP_IMAGE_REGISTRY` (example: `europe-west2-docker.pkg.dev/<project-id>/images`)
- `GKE_CLUSTER_DEV`
- `GKE_REGION_DEV`
- `K8S_NAMESPACE_DEV` (optional, defaults to `careertrojan`)
- `GKE_CLUSTER_PROD`
- `GKE_REGION_PROD`
- `K8S_NAMESPACE_PROD` (optional, defaults to `careertrojan`)

## 5) Run workflow

Workflow file:

- `.github/workflows/ci-oidc-gcp.yml`

Deploy workflows:

- `.github/workflows/build-and-deploy-dev.yml` (push to `develop`)
- `.github/workflows/build-and-deploy-prod.yml` (push tag `v*`, `production` environment)

The workflow:

- Authenticates with `google-github-actions/auth@v2`
- Verifies active account with `gcloud auth list`
- Runs focused backend unit tests

## Identity guardrails

Do not use:

- Personal email accounts (for example `@gmail.com`) in runtime/CI identity fields.
- Google-managed service agents, such as `service-<project-number>@gs-project-accounts.iam.gserviceaccount.com`.

Use only user-managed service accounts for app/runtime/CI identity.

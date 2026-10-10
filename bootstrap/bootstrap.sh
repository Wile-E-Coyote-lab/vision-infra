#!/usr/bin/env bash
# One-time trust bootstrap. Run with an authenticated gcloud (Owner on the project).
# Usage: PROJECT_ID=my-proj GH_REPO=owner/repo ./bootstrap/bootstrap.sh
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
: "${GH_REPO:?set GH_REPO (owner/repo)}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-us-central1-a}"

OPERATOR="$(gcloud config get-value account 2>/dev/null)"
PN="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
BUCKET="${PROJECT_ID}-tfstate"
CI_SA="tf-ci@${PROJECT_ID}.iam.gserviceaccount.com"
POOL="github-pool"
PROVIDER="github-provider"

echo "Project: $PROJECT_ID ($PN)  Repo: $GH_REPO  Operator: $OPERATOR"
BILLING="$(gcloud billing projects describe "$PROJECT_ID" --format='value(billingEnabled)' 2>/dev/null || echo unknown)"
[ "$BILLING" = "True" ] || echo "WARNING: billing status = $BILLING (Compute needs billing enabled)"

# Run a create command; treat 'already exists' as success, anything else as fatal
create() {
  local out
  if out="$("$@" 2>&1)"; then echo "created: ${*:1:5}"
  elif echo "$out" | grep -qiE 'already exists|ALREADY_EXISTS'; then echo "exists:  ${*:1:5}"
  else echo "$out" >&2; exit 1; fi
}

echo "== Enable APIs"
gcloud services enable --project "$PROJECT_ID" \
  serviceusage.googleapis.com cloudresourcemanager.googleapis.com \
  iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com \
  compute.googleapis.com iap.googleapis.com oslogin.googleapis.com \
  storage.googleapis.com

echo "== State bucket"
create gcloud storage buckets create "gs://${BUCKET}" --project "$PROJECT_ID" \
  --location "$REGION" --uniform-bucket-level-access
gcloud storage buckets update "gs://${BUCKET}" --versioning >/dev/null

echo "== CI service account"
create gcloud iam service-accounts create tf-ci --project "$PROJECT_ID" \
  --display-name "Terraform CI (GitHub Actions)"
sleep 10  # IAM propagation

for r in roles/compute.admin roles/iam.serviceAccountAdmin roles/iam.serviceAccountUser \
         roles/serviceusage.serviceUsageAdmin roles/resourcemanager.projectIamAdmin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:${CI_SA}" --role "$r" --condition=None --quiet >/dev/null
done
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member "serviceAccount:${CI_SA}" --role roles/storage.objectAdmin >/dev/null

# Let the human operator (Codespace login) impersonate the CI account: no key files
gcloud iam service-accounts add-iam-policy-binding "$CI_SA" --project "$PROJECT_ID" \
  --role roles/iam.serviceAccountTokenCreator --member "user:${OPERATOR}" >/dev/null

echo "== Workload Identity Federation (locked to ${GH_REPO})"
create gcloud iam workload-identity-pools create "$POOL" --project "$PROJECT_ID" \
  --location global --display-name "GitHub Actions"
create gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
  --project "$PROJECT_ID" --location global --workload-identity-pool "$POOL" \
  --issuer-uri "https://token.actions.githubusercontent.com" \
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition "assertion.repository=='${GH_REPO}'"

gcloud iam service-accounts add-iam-policy-binding "$CI_SA" --project "$PROJECT_ID" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/${PN}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${GH_REPO}" >/dev/null

cat > vars.env <<EOF
PROJECT_ID=${PROJECT_ID}
REGION=${REGION}
ZONE=${ZONE}
WIF_PROVIDER=projects/${PN}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}
CI_SERVICE_ACCOUNT=${CI_SA}
TF_STATE_BUCKET=${BUCKET}
OPERATOR_MEMBER=user:${OPERATOR}
EOF

echo
echo "== Done. Wrote vars.env:"; cat vars.env
echo "Next: ./termux/set-vars.sh vars.env"

#!/usr/bin/env bash
# Deploy Studio Scout to Google Cloud Run's Always-Free Tier (us-central1)
# using Google AI Studio Free Tier (GEMINI_API_KEY) instead of billed Vertex AI.
#
# Cloud Run Always-Free Tier limits (in us-central1 / us-east1 / us-west1):
# - 2 million requests / month
# - 180,000 vCPU-seconds / month
# - 360,000 GiB-seconds / month
#
# Usage:
#   export GEMINI_API_KEY="AIza..."
#   export PARALLEL_API_KEY="..."   # optional
#   ./scripts/deploy-cloudrun-free.sh

set -euo pipefail

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Error: GEMINI_API_KEY is not set."
  echo "Get a free API key at https://aistudio.google.com/apikey and run:"
  echo "  export GEMINI_API_KEY='your-key'"
  exit 1
fi

SERVICE_NAME="${SERVICE_NAME:-studio-scout}"
# us-central1 is eligible for Cloud Run's monthly Always-Free Tier allowance.
REGION="${REGION:-us-central1}"

echo "Deploying ${SERVICE_NAME} to Cloud Run Always-Free Tier (${REGION}) with Google AI Studio Free Tier..."

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=1 \
  --cpu=1 \
  --memory=512Mi \
  --cpu-throttling \
  --timeout=300 \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=False,GEMINI_MODEL=gemini-2.5-flash,GEMINI_API_KEY=${GEMINI_API_KEY},PARALLEL_API_KEY=${PARALLEL_API_KEY:-}"

# Delete RAG Corpus File

delete-rag-corpus-file is a simple Cloud Run function that deletes a corpus file from the VetexAI RAG Engine.

## Deployment

Clone this repository and deploy it to Cloud Run functions. Example:

```bash
FUNCTION_NAME=delete-rag-corpus-file
REGION=asia-northeast1
PROJECT_ID=$(gcloud config get-value project)
RAG_LOCATION=us-central1
RAG_CORPUS_ID=1111111111111111111

gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --runtime=python312 \
  --region="$REGION" \
  --source=. \
  --entry-point=delete_rag_corpus_file \
  --trigger-http \
  --set-env-vars=PROJECT_ID="$PROJECT_ID" \
  --set-env-vars=RAG_LOCATION="$RAG_LOCATION" \
  --set-env-vars=RAG_CORPUS_ID="$RAG_CORPUS_ID"
```

## Usage

```bash
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --region="$REGION" --format="value(url)")
ACCESS_TOKEN=$(gcloud auth print-identity-token)
curl -X POST "$FUNCTION_URL" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"gcs_source": {"uris": ["gs://backet/path/to/file"]}}'
```

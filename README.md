# Delete RAG Corpus File

delete-rag-corpus-file is a simple Cloud Run function that deletes a corpus file from the VetexAI RAG Engine.

## Required environment variables

| Variable                        | Description                                                                                                           |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `PROJECT_ID`                    | GCP project ID                                                                                                        |
| `RAG_LOCATION`                  | Vertex AI RAG Engine location (e.g. `us-central1`)                                                                    |
| `RAG_CORPUS_ID`                 | RAG Corpus resource ID                                                                                                |
| `RAG_FILE_INDEX_CACHE_GCS_PATH` | GCS path for the internal cache (inverted index) of corpus files.<br>Example: `gs://your-bucket/rag_file_index.json`. |

## Deployment

Clone this repository and deploy it to Cloud Run functions. Example:

```bash
FUNCTION_NAME=delete-rag-corpus-file
REGION=asia-northeast1
PROJECT_ID=$(gcloud config get-value project)
RAG_LOCATION=us-central1
RAG_CORPUS_ID=1111111111111111111
RAG_FILE_INDEX_CACHE_GCS_PATH=gs://your-bucket/rag_file_index.json

gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --runtime=python312 \
  --region="$REGION" \
  --source=. \
  --entry-point=delete_rag_corpus_file \
  --trigger-http \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,RAG_LOCATION=$RAG_LOCATION,RAG_CORPUS_ID=$RAG_CORPUS_ID,RAG_FILE_INDEX_CACHE_GCS_PATH=$RAG_FILE_INDEX_CACHE_GCS_PATH"
```

### Concurrency and Race Conditions

This function uses an **inverted index cache on GCS** with [optimistic concurrency control](https://cloud.google.com/storage/docs/metadata#generation-number) (via ifGenerationMatch) to avoid race conditions during updates.
For most use cases, this mechanism is sufficient, even if the function is triggered by multiple clients at the same time.

If you expect frequent concurrent requests or want to guarantee strict serialization, you can combine this function with Cloud Tasks and set `max-concurrent-dispatches=1` for your queue.
This will ensure only one request is processed at a time and prevent even temporary conflicts.

## Usage

```bash
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --region="$REGION" --format="value(url)")
ACCESS_TOKEN=$(gcloud auth print-identity-token)
curl -X POST "$FUNCTION_URL" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"gcs_source": {"uris": ["gs://backet/path/to/file"]}}'
```

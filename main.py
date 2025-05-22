import os
import json
import gzip
from typing import Dict, List, Optional, Tuple
import functions_framework
from vertexai import rag
import vertexai
from google.cloud import storage

rag_location = os.environ['RAG_LOCATION']
project_id = os.environ['PROJECT_ID']
corpus_id = os.environ['RAG_CORPUS_ID']
index_cache_gcs_path = os.environ['RAG_FILE_INDEX_CACHE_GCS_PATH']

vertexai.init(project=project_id, location=rag_location)
corpus_name = f"projects/{project_id}/locations/{rag_location}/ragCorpora/{corpus_id}"


def load_index_from_gcs(gcs_path: str) -> Tuple[Optional[Dict[str, str]], Optional[int]]:
    """Read the index JSON from GCS. Returns (dict, generation) or (None, None) if not exists."""
    client = storage.Client()
    bucket_name, blob_name = gcs_path.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    if not blob.exists():
        return None, None
    blob.reload()
    data = json.loads(blob.download_as_bytes().decode("utf-8"))
    return data, blob.generation

def write_index_to_gcs(
    gcs_path: str, data: Dict[str, str], if_generation_match: Optional[int] = None
) -> None:
    """Write the index JSON to GCS as gzip, using generation match for locking."""
    client = storage.Client()
    bucket_name, blob_name = gcs_path.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.content_encoding = "gzip"
    compressed = gzip.compress(json.dumps(data).encode('utf-8'))
    blob.upload_from_string(
        compressed,
        if_generation_match=0 if if_generation_match is None else if_generation_match,
        content_type="application/json"
    )

@functions_framework.http
def delete_rag_corpus_file(request) -> str:
    data = request.get_json()
    gcs_uris: List[str] = data.get('gcs_source', {}).get('uris', [])
    deleted: List[str] = []

    # 1. Load index from GCS
    index, generation = load_index_from_gcs(index_cache_gcs_path)
    if index is None:
        index = {}

    needs_refresh = False
    for target_uri in gcs_uris:
        rag_file_name = index.get(target_uri)
        if rag_file_name is not None:
            print(f"Deleting {rag_file_name} (by index)")
            rag.delete_file(rag_file_name)
            deleted.append(target_uri)
            del index[target_uri]
        else:
            needs_refresh = True

    # 2. If any target_uri was not found, refresh the index and retry
    if needs_refresh:
        # Build inverted index: gcs_uri -> rag_file_name
        new_index: Dict[str, str] = {}
        for rag_file in rag.list_files(corpus_name):
            for uri in rag_file.gcs_source.uris:
                new_index[uri] = rag_file.name
        for target_uri in gcs_uris:
            rag_file_name = new_index.get(target_uri)
            if rag_file_name is not None:
                print(f"Deleting {rag_file_name} (after refresh)")
                rag.delete_file(rag_file_name)
                deleted.append(target_uri)
                del new_index[target_uri]
        # 3. Save the updated index to GCS with optimistic locking
        try:
            write_index_to_gcs(index_cache_gcs_path, new_index, if_generation_match=generation)
        except Exception as e:
            print(f"Failed to write index to GCS: {e}")
            # Re-raise the exception to indicate failure
            raise

    return json.dumps({"deleted": deleted})

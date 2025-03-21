import os
import functions_framework
from vertexai import rag
import vertexai

rag_location = os.environ['RAG_LOCATION']
project_id = os.environ['PROJECT_ID']
corpus_id = os.environ['RAG_CORPUS_ID']

vertexai.init(project=project_id, location=rag_location)
corpus_name = f"projects/{project_id}/locations/{rag_location}/ragCorpora/{corpus_id}"

@functions_framework.http
def delete_rag_corpus_file(request):
    data = request.get_json()
    gcs_uris = data.get('gcs_source', {}).get('uris', [])

    for rag_file in list(rag.list_files(corpus_name)):
        for uri in rag_file.gcs_source.uris:
            if uri in gcs_uris:
                print(f"Deleting {rag_file.name}")
                rag.delete_file(rag_file.name)

    return 'OK'

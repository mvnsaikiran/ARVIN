import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_ingest import build
from policies.eap.config import PDF_PATH, POLICY_NAME, COLLECTION, MAX_CHUNK, SKIP_PAGES, MODE
_HERE           = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(_HERE, '..', '..', 'vectorstore')
def run():
    build(PDF_PATH, POLICY_NAME, COLLECTION, VECTORSTORE_DIR, MAX_CHUNK, SKIP_PAGES, mode=MODE)
if __name__ == '__main__':
    run()

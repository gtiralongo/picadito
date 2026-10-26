import os
from firebase_admin import credentials, firestore, initialize_app
from app.config import USE_FIREBASE

_firestore_client = None

def get_firestore():
    global _firestore_client
    if _firestore_client:
        return _firestore_client
    if not USE_FIREBASE:
        raise RuntimeError("Firebase no habilitado")
    try:
        initialize_app()
    except ValueError:
        pass
    _firestore_client = firestore.client()
    return _firestore_client

def collection(name):
    return get_firestore().collection(name)

def doc_ref(collection_name, doc_id):
    return collection(collection_name).document(doc_id)

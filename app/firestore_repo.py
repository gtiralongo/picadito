import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import USE_FIREBASE
from app.firebase_db import collection, doc_ref

def _now():
    return datetime.utcnow()

def _serialize_event(data: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure datetime is ISO
    if isinstance(data.get('date'), datetime):
        data['date'] = data['date'].isoformat()
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    return data

def _deserialize_event(doc) -> Dict[str, Any]:
    data = doc.to_dict()
    if data.get('date'):
        # Firestore stores datetime as datetime
        pass
    return data

class FirestoreRepo:
    @staticmethod
    def create_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        if not USE_FIREBASE:
            raise RuntimeError("Firestore no habilitado")
        event_id = event_data.get('id') or uuid.uuid4().hex
        event_data['id'] = event_id
        event_data.setdefault('created_at', _now())
        event_data.setdefault('status', 'active')
        collection('events').document(event_id).set(_serialize_event(event_data))
        return event_data

    @staticmethod
    def update_event(event_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        if not USE_FIREBASE:
            raise RuntimeError("Firestore no habilitado")
        ref = collection('events').document(event_id)
        ref.update(_serialize_event(update_data))
        return {**update_data, 'id': event_id}

    @staticmethod
    def get_event(event_id: str) -> Optional[Dict[str, Any]]:
        if not USE_FIREBASE:
            raise RuntimeError("Firestore no habilitado")
        doc = collection('events').document(event_id).get()
        if not doc.exists:
            return None
        return _deserialize_event(doc)

    @staticmethod
    def list_events() -> List[Dict[str, Any]]:
        if not USE_FIREBASE:
            raise RuntimeError("Firestore no habilitado")
        docs = collection('events').stream()
        return [d.to_dict() for d in docs]

    @staticmethod
    def create_participant(event_id: str, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        if not USE_FIREBASE:
            raise RuntimeError("Firestore no habilitado")
        pid = participant_data.get('id') or uuid.uuid4().hex
        participant_data['id'] = pid
        participant_data['event_id'] = event_id
        participant_data.setdefault('created_at', _now())
        collection('participants').document(pid).set(participant_data)
        # Add subcollection for quick query
        collection('events').document(event_id).collection('participants').document(pid).set(participant_data)
        return participant_data

    @staticmethod
    def list_participants(event_id: str) -> List[Dict[str, Any]]:
        if not USE_FIREBASE:
            raise RuntimeError("Firestore no habilitado")
        docs = collection('participants').where('event_id', '==', event_id).stream()
        return [d.to_dict() for d in docs]

# Fallback to SQLAlchemy when USE_FIREBASE is false
# The existing routes continue using SQLAlchemy Session
# For full migration, replace Session usage with FirestoreRepo calls

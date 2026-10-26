# Despliegue en Firebase

## Opción recomendada: Firebase App Hosting + Firestore

### 1. Crear proyecto
```bash
firebase login
firebase projects:create picadito-prod
firebase use picadito-prod
```

### 2. Habilitar Firestore
En consola de Firebase → Build → Firestore Database → Create database → Start in test mode

### 3. Configurar variables
Crear `serviceAccountKey.json` y setear en App Hosting:
```
USE_FIREBASE=true
FIREBASE_PROJECT_ID=tu-proyecto
GOOGLE_APPLICATION_CREDENTIALS=/secrets/serviceAccountKey.json
PORT=8080
```

### 4. Archivos de configuración
- `firebase.json` → App Hosting
- `app.yaml` → runtime python311, entrypoint `uvicorn app.main:app --host 0.0.0.0 --port 8080`

### 5. Desplegar
```bash
firebase deploy --only apphosting
```

## Nota sobre la base de datos
Actualmente el app usa SQLite + SQLAlchemy. Para producción con Firebase se recomienda migrar a Firestore.

Se agregó `firebase-admin` y `app/firebase_db.py`, `app/firestore_repo.py` como base para la migración.
El flag `USE_FIREBASE` permite mantener SQLite local y usar Firestore en producción.

Para una migración completa hay que reemplazar los `Session` de SQLAlchemy por `FirestoreRepo` en `app/routers/web.py` y `app/routers/auth.py`.

## Emulador local
```bash
npm install -g firebase-tools
firebase init emulators
firebase emulators:start
```
Setear `USE_FIREBASE=true` y `FIREBASE_PROJECT_ID=demo-picadito` para probar contra el emulador.

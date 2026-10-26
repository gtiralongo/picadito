// Configuración de Firebase - reemplazar con tus valores de Firebase Console
const firebaseConfig = {
  apiKey: "AIzaSyAGb3pg1tTSfmSYXt-zIcR-JtHaCtFBv-A",
  authDomain: "picadito-28f4a.firebaseapp.com",
  projectId: "picadito-28f4a",
  storageBucket: "picadito-28f4a.firebasestorage.app",
  messagingSenderId: "560678362563",
  appId: "1:560678362563:web:e034c0c25996e58650f176"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.database();

// Exportar global
window.firebaseApp = firebase;
window.auth = auth;
window.db = db;

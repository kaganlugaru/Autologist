// Firebase конфигурация для веб-приложения
// Данные получены из Firebase Console для проекта autologist-65cd7

const firebaseConfig = {
  apiKey: "AIzaSyA8q_Dl-rKdm-MUr4226czsIRjioBGEChY",
  authDomain: "autologist-65cd7.firebaseapp.com",
  projectId: "autologist-65cd7",
  storageBucket: "autologist-65cd7.firebasestorage.app",
  messagingSenderId: "742606479823",
  appId: "1:742606479823:web:a08c9f03f4b6838b8f72ba"
};

// Инициализация Firebase
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';
import { getStorage } from 'firebase/storage';

const app = initializeApp(firebaseConfig);

// Экспорт сервисов
export const db = getFirestore(app);
export const auth = getAuth(app);
export const storage = getStorage(app);

export default app;
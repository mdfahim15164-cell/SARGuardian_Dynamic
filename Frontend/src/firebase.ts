import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

const requiredConfig = [
  ['VITE_FIREBASE_API_KEY', config.apiKey],
  ['VITE_FIREBASE_AUTH_DOMAIN', config.authDomain],
  ['VITE_FIREBASE_PROJECT_ID', config.projectId],
  ['VITE_FIREBASE_STORAGE_BUCKET', config.storageBucket],
  ['VITE_FIREBASE_MESSAGING_SENDER_ID', config.messagingSenderId],
  ['VITE_FIREBASE_APP_ID', config.appId],
] as const;

export const missingFirebaseConfig = requiredConfig
  .filter(([, value]) => !value)
  .map(([key]) => key);
export const firebaseConfigured = missingFirebaseConfig.length === 0;

const firebaseApp = firebaseConfigured ? initializeApp(config) : null;
export const auth = firebaseApp ? getAuth(firebaseApp) : null;
export const googleProvider = firebaseConfigured ? new GoogleAuthProvider() : null;
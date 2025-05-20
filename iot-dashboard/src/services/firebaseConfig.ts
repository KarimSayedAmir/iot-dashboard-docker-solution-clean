// Firebase configuration for the IoT Dashboard
// This file sets up the Firebase connection for data storage

import { initializeApp } from 'firebase/app';
import { getDatabase } from 'firebase/database';

// Firebase configuration
// Replace with your own Firebase project configuration
const firebaseConfig = {
  apiKey: "AIzaSyDummyApiKeyForIoTDashboard",
  authDomain: "iot-dashboard-owipex.firebaseapp.com",
  databaseURL: "https://iot-dashboard-owipex.firebaseio.com",
  projectId: "iot-dashboard-owipex",
  storageBucket: "iot-dashboard-owipex.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef1234567890"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

export { database };

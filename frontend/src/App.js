// frontend/src/App.js

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import ProtectedRoute from './components/common/ProtectedRoute';
import Layout from './components/layout/Layout';

// Page Components
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import MealPlanning from './pages/MealPlanning';
import Workouts from './pages/Workouts';
import Chat from './pages/Chat';
import Login from './pages/Login';
import Register from './pages/Register';
import Landing from './pages/Landing';

// Styles
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            
            <Route path="/profile" element={
              <ProtectedRoute>
                <Layout>
                  <Profile />
                </Layout>
              </ProtectedRoute>
            } />
            
            <Route path="/meals/*" element={
              <ProtectedRoute>
                <Layout>
                  <MealPlanning />
                </Layout>
              </ProtectedRoute>
            } />
            
            <Route path="/workouts/*" element={
              <ProtectedRoute>
                <Layout>
                  <Workouts />
                </Layout>
              </ProtectedRoute>
            } />
            
            <Route path="/chat/*" element={
              <ProtectedRoute>
                <Layout>
                  <Chat />
                </Layout>
              </ProtectedRoute>
            } />
            
            {/* Redirect unknown routes */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
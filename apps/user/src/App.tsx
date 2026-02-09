import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Home from './pages/Home';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Dashboard from './pages/Dashboard';
import PaymentPage from './pages/PaymentPage';
import VerificationPage from './pages/VerificationPage';
import ProfilePage from './pages/ProfilePage';
import ResumeUpload from './pages/ResumeUpload';
import UMarketU from './pages/UMarketU';
import CoachingHub from './pages/CoachingHub';
import MentorshipMarketplace from './pages/MentorshipMarketplace';
import MentorApplication from './pages/MentorApplication';
import DualCareer from './pages/DualCareer';
import RewardsPage from './pages/RewardsPage';
import VisualisationsHub from './pages/VisualisationsHub';
import ConsolidationPage from './pages/ConsolidationPage';

function PrivateRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, loading } = useAuth();

    if (loading) return <div className="p-10 text-center">Loading session...</div>;

    return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    {/* Public Routes */}
                    <Route path="/" element={<Home />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />

                    {/* Private Routes (Ordered 04-15) */}
                    <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
                    <Route path="/payment" element={<PrivateRoute><PaymentPage /></PrivateRoute>} />
                    <Route path="/verify" element={<PrivateRoute><VerificationPage /></PrivateRoute>} />
                    <Route path="/profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />
                    <Route path="/resume" element={<PrivateRoute><ResumeUpload /></PrivateRoute>} />
                    <Route path="/umarketu" element={<PrivateRoute><UMarketU /></PrivateRoute>} />
                    <Route path="/coaching" element={<PrivateRoute><CoachingHub /></PrivateRoute>} />
                    <Route path="/mentorship" element={<PrivateRoute><MentorshipMarketplace /></PrivateRoute>} />
                    <Route path="/mentor/apply" element={<PrivateRoute><MentorApplication /></PrivateRoute>} />
                    <Route path="/dual-career" element={<PrivateRoute><DualCareer /></PrivateRoute>} />
                    <Route path="/rewards" element={<PrivateRoute><RewardsPage /></PrivateRoute>} />
                    <Route path="/visuals" element={<PrivateRoute><VisualisationsHub /></PrivateRoute>} />
                    <Route path="/consolidation" element={<PrivateRoute><ConsolidationPage /></PrivateRoute>} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

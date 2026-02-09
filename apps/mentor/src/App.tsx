import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MentorAuthProvider, useMentorAuth } from './context/MentorAuthContext';
import MentorLogin from './pages/MentorLogin';

// Mentor Pages
import Dashboard from './pages/Dashboard';
import MentorDashboard from './pages/MentorDashboard';
import FinancialDashboard from './pages/FinancialDashboard';
import MenteeAgreements from './pages/MenteeAgreements';
import CommunicationCenter from './pages/CommunicationCenter';
import GuardianFeedback from './pages/GuardianFeedback';
import MenteeProgress from './pages/MenteeProgress';
import AIAssistant from './pages/AIAssistant';
import MyAgreements from './pages/MyAgreements';
import ServicePackages from './pages/ServicePackages';
import ServicesAgreement from './pages/ServicesAgreement';
import SessionsCalendar from './pages/SessionsCalendar';

function PrivateRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, loading } = useMentorAuth();

    if (loading) return <div className="p-10 text-center text-white">Loading...</div>;

    return isAuthenticated ? <>{children}</> : <Navigate to="/mentor/login" />;
}

export default function App() {
    return (
        <MentorAuthProvider>
            <BrowserRouter>
                <Routes>
                    {/* Public Route */}
                    <Route path="/mentor/login" element={<MentorLogin />} />

                    {/* Mentor Pages (12 pages) */}
                    <Route path="/mentor" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
                    <Route path="/mentor/dashboard" element={<PrivateRoute><MentorDashboard /></PrivateRoute>} />
                    <Route path="/mentor/financials" element={<PrivateRoute><FinancialDashboard /></PrivateRoute>} />
                    <Route path="/mentor/agreements" element={<PrivateRoute><MenteeAgreements /></PrivateRoute>} />
                    <Route path="/mentor/communication" element={<PrivateRoute><CommunicationCenter /></PrivateRoute>} />
                    <Route path="/mentor/guardian-feedback" element={<PrivateRoute><GuardianFeedback /></PrivateRoute>} />
                    <Route path="/mentor/mentee-progress" element={<PrivateRoute><MenteeProgress /></PrivateRoute>} />
                    <Route path="/mentor/ai-assistant" element={<PrivateRoute><AIAssistant /></PrivateRoute>} />
                    <Route path="/mentor/my-agreements" element={<PrivateRoute><MyAgreements /></PrivateRoute>} />
                    <Route path="/mentor/packages" element={<PrivateRoute><ServicePackages /></PrivateRoute>} />
                    <Route path="/mentor/services" element={<PrivateRoute><ServicesAgreement /></PrivateRoute>} />
                    <Route path="/mentor/calendar" element={<PrivateRoute><SessionsCalendar /></PrivateRoute>} />

                    {/* Fallback */}
                    <Route path="*" element={<Navigate to="/mentor" />} />
                </Routes>
            </BrowserRouter>
        </MentorAuthProvider>
    );
}

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import MobileNav from './components/mobile/MobileNav';
import MobileBottomBar from './components/mobile/MobileBottomBar';
import PWAInstallBanner from './components/mobile/PWAInstallBanner';
import NetworkBanner from './components/mobile/NetworkBanner';
import CookieConsent from './components/CookieConsent';

// ── Eager: public pages (first paint) ────────────────────
import Home from './pages/Home';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// ── Lazy: private pages (code-split) ─────────────────────
const Dashboard              = lazy(() => import('./pages/Dashboard'));
const PaymentPage            = lazy(() => import('./pages/PaymentPage'));
const VerificationPage       = lazy(() => import('./pages/VerificationPage'));
const ProfilePage            = lazy(() => import('./pages/ProfilePage'));
const ResumeUpload           = lazy(() => import('./pages/ResumeUpload'));
const UMarketU               = lazy(() => import('./pages/UMarketU'));
const CoachingHub            = lazy(() => import('./pages/CoachingHub'));
const MentorshipMarketplace  = lazy(() => import('./pages/MentorshipMarketplace'));
const MentorApplication      = lazy(() => import('./pages/MentorApplication'));
const DualCareer             = lazy(() => import('./pages/DualCareer'));
const RewardsPage            = lazy(() => import('./pages/RewardsPage'));
const VisualisationsHub      = lazy(() => import('./pages/VisualisationsHub'));
const ConsolidationPage      = lazy(() => import('./pages/ConsolidationPage'));
const PrivacyPolicy          = lazy(() => import('./pages/PrivacyPolicy'));

// ── Lazy: mobile-only pages ──────────────────────────────
const MobileQuickDash  = lazy(() => import('./components/mobile/MobileQuickDash'));
const JobSwipe         = lazy(() => import('./components/mobile/JobSwipe'));
const MobileCVUpload   = lazy(() => import('./components/mobile/MobileCVUpload'));

// ── Suspense fallback ────────────────────────────────────
function PageLoader() {
    return (
        <div className="flex items-center justify-center min-h-[60vh]">
            <div className="flex flex-col items-center gap-3">
                <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-gray-400">Loading…</span>
            </div>
        </div>
    );
}

function PrivateRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, loading } = useAuth();

    if (loading) return <PageLoader />;

    return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <NetworkBanner />
                <MobileNav />
                <main className="mobile-safe-content">
                    <Suspense fallback={<PageLoader />}>
                        <Routes>
                            {/* Public Routes */}
                            <Route path="/" element={<Home />} />
                            <Route path="/login" element={<LoginPage />} />
                            <Route path="/register" element={<RegisterPage />} />
                            <Route path="/privacy" element={<PrivacyPolicy />} />

                            {/* Mobile-specific routes */}
                            <Route path="/quick" element={<PrivateRoute><MobileQuickDash /></PrivateRoute>} />
                            <Route path="/jobs/swipe" element={<PrivateRoute><JobSwipe /></PrivateRoute>} />
                            <Route path="/mobile/cv" element={<PrivateRoute><MobileCVUpload /></PrivateRoute>} />

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
                    </Suspense>
                </main>
                <MobileBottomBar />
                <PWAInstallBanner />
                <CookieConsent />
            </BrowserRouter>
        </AuthProvider>
    );
}

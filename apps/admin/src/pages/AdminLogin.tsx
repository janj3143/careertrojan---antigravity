import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Mail, Lock, AlertCircle } from 'lucide-react';

export default function AdminLogin() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [twoFactorCode, setTwoFactorCode] = useState('');
    const [showTwoFactor, setShowTwoFactor] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await fetch('/api/auth/v1/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    two_factor_code: showTwoFactor ? twoFactorCode : undefined
                })
            });

            const data = await response.json();

            if (!response.ok) {
                if (data.requires_2fa) {
                    setShowTwoFactor(true);
                    setError('');
                } else {
                    throw new Error(data.detail || 'Login failed');
                }
            } else {
                // Store admin token and navigate
                localStorage.setItem('admin_token', data.access_token);
                navigate('/admin');
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-red-900/20 to-slate-900 flex items-center justify-center p-6">
            <div className="w-full max-w-md">
                {/* Logo & Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex flex-col items-center justify-center mb-4">
                        <img
                            src="/logo.png"
                            alt="CareerTrojan Logo"
                            className="h-16 w-auto mb-2"
                            onError={(e) => {
                                e.currentTarget.style.display = 'none';
                                const icon = document.getElementById('fallback-icon');
                                if (icon) icon.style.display = 'flex';
                            }}
                        />
                        <div id="fallback-icon" className="hidden items-center justify-center w-16 h-16 bg-red-600 rounded-full">
                            <Shield className="text-white" size={32} />
                        </div>
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">Admin Portal</h1>
                    <p className="text-slate-400">Secure administrative access</p>
                </div>

                {/* Login Form */}
                <div className="bg-slate-900 border border-red-700/30 rounded-lg p-8 shadow-2xl">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Error Message */}
                        {error && (
                            <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 flex items-start gap-3">
                                <AlertCircle className="text-red-400 mt-0.5" size={20} />
                                <div className="text-sm text-red-300">{error}</div>
                            </div>
                        )}

                        {/* Email Field */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                                Admin Email
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Mail className="text-slate-500" size={18} />
                                </div>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    disabled={showTwoFactor}
                                    className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition disabled:opacity-50"
                                    placeholder="admin@careertrojan.com"
                                />
                            </div>
                        </div>

                        {/* Password Field */}
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                                Password
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="text-slate-500" size={18} />
                                </div>
                                <input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    disabled={showTwoFactor}
                                    className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition disabled:opacity-50"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        {/* 2FA Field */}
                        {showTwoFactor && (
                            <div>
                                <label htmlFor="twoFactor" className="block text-sm font-medium text-slate-300 mb-2">
                                    Two-Factor Authentication Code
                                </label>
                                <input
                                    id="twoFactor"
                                    type="text"
                                    value={twoFactorCode}
                                    onChange={(e) => setTwoFactorCode(e.target.value)}
                                    required
                                    maxLength={6}
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition text-center text-2xl tracking-widest"
                                    placeholder="000000"
                                />
                                <p className="text-xs text-slate-400 mt-2">Enter the 6-digit code from your authenticator app</p>
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg text-white font-semibold transition flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    Authenticating...
                                </>
                            ) : (
                                <>
                                    <Shield size={18} />
                                    {showTwoFactor ? 'Verify & Sign In' : 'Sign In'}
                                </>
                            )}
                        </button>
                    </form>

                    {/* Security Notice */}
                    <div className="mt-6 p-4 bg-amber-900/20 border border-amber-700/50 rounded-lg">
                        <div className="flex items-start gap-2">
                            <AlertCircle className="text-amber-400 mt-0.5" size={16} />
                            <div className="text-xs text-amber-300">
                                <p className="font-semibold mb-1">Security Notice</p>
                                <p>All admin access is logged and monitored. Unauthorized access attempts will be reported.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="text-center mt-6 text-sm text-slate-500">
                    <p>© 2026 CareerTrojan Admin Portal</p>
                    <p className="mt-1">Secure administrative access with 2FA</p>
                </div>
            </div>
        </div>
    );
}

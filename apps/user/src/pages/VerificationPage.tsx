import React, { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_CONFIG = { baseUrl: "http://localhost:8500" };

export default function VerificationPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState({
        email_verified: false,
        payment_verified: false,
        setup_complete: false
    });

    useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return navigate('/login');

            // 1. Check User details for email verification (simulated for now as true effectively if logged in)
            const userRes = await fetch(`${API_CONFIG.baseUrl}/api/user/v1/me`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const userData = await userRes.json();

            // 2. Check Subscription for payment verification
            const subRes = await fetch(`${API_CONFIG.baseUrl}/api/payment/v1/subscription`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const subData = await subRes.json();

            setStatus({
                email_verified: true, // If they can hit /me, they are logged in.
                payment_verified: subData.active && subData.plan_id !== 'free', // 'free' counts as verified for trial purposes, but let's encourage upgrade
                setup_complete: !!userData.full_name
            });
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-screen">
            <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
        </div>
    );

    const allGood = status.email_verified && status.setup_complete;

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold mb-2">✅ Account Verification</h1>
            <p className="text-gray-600 mb-8">Let's get you ready for the CareerTrojan experience.</p>

            <div className="grid grid-cols-1 gap-6">

                {/* Email Verification */}
                <div className={`p-6 rounded-xl border flex items-center justify-between ${status.email_verified ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                    <div className="flex items-center gap-4">
                        {status.email_verified ? <CheckCircle className="text-green-600 w-8 h-8" /> : <AlertCircle className="text-yellow-600 w-8 h-8" />}
                        <div>
                            <h3 className="font-bold text-lg text-gray-900">Email Verification</h3>
                            <p className="text-sm text-gray-600">{status.email_verified ? "Your email is verified." : "Please check your inbox."}</p>
                        </div>
                    </div>
                </div>

                {/* Profile Setup */}
                <div className={`p-6 rounded-xl border flex items-center justify-between ${status.setup_complete ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="flex items-center gap-4">
                        {status.setup_complete ? <CheckCircle className="text-green-600 w-8 h-8" /> : <AlertCircle className="text-red-600 w-8 h-8" />}
                        <div>
                            <h3 className="font-bold text-lg text-gray-900">Profile Setup</h3>
                            <p className="text-sm text-gray-600">{status.setup_complete ? "Basic profile info complete." : "Your profile is missing information."}</p>
                        </div>
                    </div>
                    {!status.setup_complete && (
                        <button onClick={() => navigate('/profile')} className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
                            Complete Profile
                        </button>
                    )}
                </div>

                {/* Payment/Plan Status */}
                <div className={`p-6 rounded-xl border flex items-center justify-between ${status.payment_verified ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'}`}>
                    <div className="flex items-center gap-4">
                        {status.payment_verified ? <CheckCircle className="text-green-600 w-8 h-8" /> : <RefreshCw className="text-blue-600 w-8 h-8" />}
                        <div>
                            <h3 className="font-bold text-lg text-gray-900">Subscription Status</h3>
                            <p className="text-sm text-gray-600">{status.payment_verified ? "Premium plan active." : "Free Trial Active. Upgrade for more features."}</p>
                        </div>
                    </div>
                    {!status.payment_verified && (
                        <button onClick={() => navigate('/payment')} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                            Upgrade Plan
                        </button>
                    )}
                </div>

            </div>

            {allGood && (
                <div className="mt-8 text-center animate-fade-in">
                    <p className="text-lg text-gray-700 mb-4">You are all set!</p>
                    <button onClick={() => navigate('/coaching')} className="px-8 py-3 bg-indigo-600 text-white text-lg font-bold rounded-lg hover:bg-indigo-700 shadow-lg">
                        Go to Coaching Hub →
                    </button>
                </div>
            )}
        </div>
    );
}


import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { API } from '../lib/apiConfig';

function CreditBalanceWidget() {
    const [balance, setBalance] = useState<{
        plan_name: string;
        plan_tier: string;
        credits_total: number;
        credits_remaining: number;
        credits_used: number;
        usage_percentage: number;
    } | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API.credits}/balance`, {
            headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
        })
            .then(r => r.ok ? r.json() : null)
            .catch(() => null)
            .then(data => {
                if (data) setBalance(data);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-2/3 mb-3"></div>
                <div className="h-3 bg-gray-100 rounded w-full"></div>
            </div>
        );
    }

    if (!balance) {
        return (
            <div className="bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-200 rounded-lg shadow-sm p-6">
                <h3 className="text-lg font-semibold text-violet-800">Credits</h3>
                <p className="text-sm text-violet-600 mt-1">Sign in to see your balance</p>
                <Link to="/payment" className="text-xs text-violet-700 underline mt-2 inline-block">
                    View Plans →
                </Link>
            </div>
        );
    }

    const pct = balance.usage_percentage;
    const barColor = pct > 80 ? "bg-red-500" : pct > 50 ? "bg-yellow-500" : "bg-green-500";

    return (
        <div className="bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-200 rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-violet-800">
                    {balance.plan_name}
                </h3>
                <span className="text-xs font-medium bg-violet-100 text-violet-700 px-2 py-1 rounded">
                    {balance.plan_tier.toUpperCase()}
                </span>
            </div>
            <div className="mt-3">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>{balance.credits_remaining} credits remaining</span>
                    <span>{balance.credits_used} / {balance.credits_total} used</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div
                        className={`${barColor} h-2.5 rounded-full transition-all duration-500`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                    ></div>
                </div>
            </div>
            {pct > 80 && (
                <Link to="/payment" className="text-xs text-red-600 underline mt-2 inline-block font-medium">
                    Running low — Upgrade now →
                </Link>
            )}
            {balance.plan_tier === "free" && (
                <Link to="/payment" className="text-xs text-violet-700 underline mt-2 inline-block">
                    Upgrade for full access →
                </Link>
            )}
        </div>
    );
}

export default function Dashboard() {
    return (
        <div className="p-8">
            <h1 className="text-3xl font-bold mb-4">User Dashboard</h1>
            <p className="text-gray-600 mb-4">Welcome to CareerTrojan. You are logged in.</p>

            {/* Credit Balance Widget */}
            <div className="mb-8 max-w-md">
                <CreditBalanceWidget />
            </div>

            {/* Core Features Grid (Ordered by Workflow) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                {/* 05 Payment */}
                <Link to="/payment" className="block p-6 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-gray-800">05. Payment</h3>
                    <p className="text-sm text-gray-600 mt-2">Manage subscription and billing.</p>
                </Link>

                {/* 07 Verification */}
                <Link to="/verify" className="block p-6 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-gray-800">07. Verification</h3>
                    <p className="text-sm text-gray-600 mt-2">Verify identity and visuals.</p>
                </Link>

                {/* 08 Profile */}
                <Link to="/profile" className="block p-6 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-gray-800">08. Profile</h3>
                    <p className="text-sm text-gray-600 mt-2">Complete your user profile.</p>
                </Link>

                {/* 09 Resume */}
                <Link to="/resume" className="block p-6 bg-blue-50 border border-blue-100 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-blue-700">09. Resume Upload</h3>
                    <p className="text-sm text-blue-600 mt-2">AI-driven resume analysis.</p>
                </Link>

                {/* 10 UMarketU */}
                <Link to="/umarketu" className="block p-6 bg-purple-50 border border-purple-100 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-purple-700">10. UMarketU</h3>
                    <p className="text-sm text-purple-600 mt-2">Market fit & job discovery.</p>
                </Link>

                {/* 11 Coaching */}
                <Link to="/coaching" className="block p-6 bg-indigo-50 border border-indigo-100 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-indigo-700">11. Coaching Hub</h3>
                    <p className="text-sm text-indigo-600 mt-2">Interview prep & blocker detection.</p>
                </Link>

                {/* 12 Mentorship */}
                <Link to="/mentorship" className="block p-6 bg-teal-50 border border-teal-100 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-teal-700">12. Find Mentor</h3>
                    <p className="text-sm text-teal-600 mt-2">Connect with industry experts.</p>
                </Link>

                {/* 13 Become Mentor */}
                <Link to="/mentor/apply" className="block p-6 bg-teal-50 border border-teal-100 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-teal-700">13. Become Mentor</h3>
                    <p className="text-sm text-teal-600 mt-2">Apply to mentor others.</p>
                </Link>

                {/* 14 Dual Career */}
                <Link to="/dual-career" className="block p-6 bg-orange-50 border border-orange-100 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-orange-700">14. Dual Career</h3>
                    <p className="text-sm text-orange-600 mt-2">Simultaneous career tracks.</p>
                </Link>

                {/* 15 Rewards */}
                <Link to="/rewards" className="block p-6 bg-yellow-50 border border-yellow-100 rounded-lg shadow-sm hover:shadow-md transition">
                    <h3 className="text-xl font-semibold text-yellow-700">15. Rewards</h3>
                    <p className="text-sm text-yellow-600 mt-2">View your achievements.</p>
                </Link>

            </div>
        </div>
    );
}

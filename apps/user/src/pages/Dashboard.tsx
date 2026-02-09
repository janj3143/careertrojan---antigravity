
import React from 'react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
    return (
        <div className="p-8">
            <h1 className="text-3xl font-bold mb-4">User Dashboard</h1>
            <p className="text-gray-600 mb-8">Welcome to CareerTrojan. You are logged in.</p>

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
                <Link to="/market-u" className="block p-6 bg-purple-50 border border-purple-100 rounded-lg shadow-sm hover:shadow-md transition">
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

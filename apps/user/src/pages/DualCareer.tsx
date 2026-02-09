import React from 'react';
import { Briefcase, Zap, Target, TrendingUp, Layers } from 'lucide-react';

export default function DualCareer() {
    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">⚖️ Dual Career Suite</h1>
                <p className="text-gray-600 mt-2">Master the art of balancing a corporate career with your entrepreneurial ventures.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Primary Career Card */}
                <div className="bg-white rounded-xl shadow-sm border p-6 border-l-4 border-l-blue-500 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Briefcase className="w-24 h-24" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">Primary Career</h2>
                    <p className="text-gray-500 mb-6">Corporate / Full-time Role</p>

                    <div className="space-y-4">
                        <div className="bg-gray-50 p-4 rounded-lg">
                            <h3 className="text-sm font-bold text-gray-700">Current Role</h3>
                            <p className="text-gray-900">Senior Product Manager</p>
                        </div>
                        <div className="bg-gray-50 p-4 rounded-lg">
                            <h3 className="text-sm font-bold text-gray-700">Performance Goal</h3>
                            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '75%' }}></div>
                            </div>
                            <p className="text-xs text-right mt-1 text-gray-500">75% on track</p>
                        </div>
                    </div>

                    <button className="mt-6 text-blue-600 font-medium hover:underline flex items-center gap-1">
                        Manage Corporate Profile <TrendingUp className="w-4 h-4" />
                    </button>
                </div>

                {/* Secondary Venture Card */}
                <div className="bg-white rounded-xl shadow-sm border p-6 border-l-4 border-l-purple-500 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Zap className="w-24 h-24" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">Venture / Side Hustle</h2>
                    <p className="text-gray-500 mb-6">Startup / Consulting / Freelance</p>

                    <div className="space-y-4">
                        <div className="bg-purple-50 p-4 rounded-lg">
                            <h3 className="text-sm font-bold text-gray-700">Project Name</h3>
                            <p className="text-gray-900">AI Consultancy</p>
                        </div>
                        <div className="bg-purple-50 p-4 rounded-lg">
                            <h3 className="text-sm font-bold text-gray-700">Launch Readiness</h3>
                            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                                <div className="bg-purple-500 h-2 rounded-full" style={{ width: '40%' }}></div>
                            </div>
                            <p className="text-xs text-right mt-1 text-gray-500">40% MVP Built</p>
                        </div>
                    </div>

                    <button className="mt-6 text-purple-600 font-medium hover:underline flex items-center gap-1">
                        Open Venture Dashboard <Layers className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Orbit Shifting */}
            <div className="mt-8 bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl p-8 text-white">
                <div className="flex items-start justify-between">
                    <div>
                        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2"><Target className="w-6 h-6 text-yellow-500" /> Orbit Shifting Strategy</h2>
                        <p className="text-gray-300 max-w-2xl">
                            Plan your transition from employee to entrepreneur. Our AI analyzes your risk tolerance,
                            financial runway, and venture traction to suggest the optimal "shift" moment.
                        </p>
                    </div>
                    <button className="bg-white text-gray-900 px-6 py-2 rounded-lg font-bold hover:bg-gray-100">
                        Analyze My Orbit
                    </button>
                </div>
            </div>
        </div>
    );
}

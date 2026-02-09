
import React, { useState, useEffect } from 'react';
import { ArrowRight, CheckCircle, Zap, Shield, Target } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export default function Home() {
    const navigate = useNavigate();
    const [stats, setStats] = useState({ users: 1200, resumes: 5400 });

    const FEATURES = [
        { icon: <Zap className="w-6 h-6 text-amber-500" />, title: "AI-Powered Analysis", desc: "Instant feedback on your resume tailored to your target role." },
        { icon: <Target className="w-6 h-6 text-indigo-500" />, title: "Precise Job Matching", desc: "Align your skills with market demand using our Match Engine." },
        { icon: <Shield className="w-6 h-6 text-green-500" />, title: "ATS Proofing", desc: "Ensure your application gets past automated filters." }
    ];

    return (
        <div className="min-h-screen bg-white">

            {/* Hero Section */}
            <div className="relative bg-gradient-to-br from-indigo-900 via-indigo-800 to-purple-900 text-white overflow-hidden">
                <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-10"></div>
                <div className="max-w-7xl mx-auto px-6 py-24 relative z-10">
                    <div className="grid md:grid-cols-2 gap-12 items-center">
                        <div className="space-y-6 animate-fade-in-up">
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-700/50 border border-indigo-500/30 text-indigo-200 text-sm font-medium">
                                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                                Now with vLLM Intelligence
                            </div>
                            <h1 className="text-5xl md:text-6xl font-bold leading-tight">
                                Build a Smarter, <br />
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Stronger Career.</span>
                            </h1>
                            <p className="text-xl text-indigo-100 max-w-lg">
                                Your resume. Your journey. AI-enhanced insights that help you stand out and get hired faster.
                            </p>
                            <div className="flex flex-col sm:flex-row gap-4 pt-4">
                                <Link to="/register" className="px-8 py-4 bg-white text-indigo-900 rounded-lg font-bold text-lg hover:bg-gray-50 transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2">
                                    Get Started Free <ArrowRight className="w-5 h-5" />
                                </Link>
                                <Link to="/login" className="px-8 py-4 bg-indigo-800/50 border border-indigo-600/50 text-white rounded-lg font-medium text-lg hover:bg-indigo-700/50 transition-all flex items-center justify-center">
                                    Sign In
                                </Link>
                            </div>
                            <p className="text-sm text-indigo-300/80 mt-4">
                                No credit card required · {stats.users.toLocaleString()}+ professionals trust us
                            </p>
                        </div>

                        {/* Hero Graphic */}
                        <div className="relative hidden md:block animate-fade-in">
                            <div className="absolute -inset-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur-2xl opacity-30 animate-pulse-slow"></div>
                            <div className="relative bg-indigo-950/80 backdrop-blur-sm border border-indigo-500/30 rounded-2xl p-6 shadow-2xl">
                                <div className="flex items-center gap-4 mb-6 border-b border-indigo-500/20 pb-4">
                                    <div className="w-3 h-3 rounded-full bg-red-400"></div>
                                    <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                                    <div className="w-3 h-3 rounded-full bg-green-400"></div>
                                    <div className="ml-auto text-xs text-indigo-300 font-mono">analysis_v2.json</div>
                                </div>
                                <div className="space-y-4 font-mono text-sm">
                                    <div className="flex justify-between items-center text-green-400">
                                        <span>✓ Skills Alignment</span>
                                        <span>94%</span>
                                    </div>
                                    <div className="w-full bg-indigo-900/50 rounded-full h-2">
                                        <div className="bg-green-400 h-2 rounded-full" style={{ width: '94%' }}></div>
                                    </div>

                                    <div className="flex justify-between items-center text-amber-400 mt-4">
                                        <span>⚠ Impact Gaps Detected</span>
                                        <span>3</span>
                                    </div>
                                    <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded text-amber-200 text-xs">
                                        "Led project team" -> "Spearheaded cross-functional team of 12..."
                                    </div>

                                    <div className="flex justify-between items-center text-blue-400 mt-4">
                                        <span>ℹ Market Demand</span>
                                        <span>High</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Features Section */}
            <div className="py-24 bg-gray-50">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="text-center max-w-2xl mx-auto mb-16">
                        <h2 className="text-3xl font-bold text-gray-900 mb-4">Why IntelliCV?</h2>
                        <p className="text-gray-600 text-lg">We combine advanced LLMs with real-time market data to give you an unfair advantage.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {FEATURES.map((f, i) => (
                            <div key={i} className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow border border-gray-100">
                                <div className="mb-4 bg-indigo-50 w-12 h-12 rounded-lg flex items-center justify-center">
                                    {f.icon}
                                </div>
                                <h3 className="text-xl font-bold text-gray-900 mb-2">{f.title}</h3>
                                <p className="text-gray-600 leading-relaxed">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

        </div>
    );
}

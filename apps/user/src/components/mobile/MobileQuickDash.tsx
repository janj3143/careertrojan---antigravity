import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    Briefcase, FileText, Brain, TrendingUp, AlertCircle,
    ChevronRight, Sparkles, Upload, Clock, CheckCircle2
} from 'lucide-react';

const API_BASE = '/api';

interface QuickStat {
    label: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    to: string;
}

interface ActivityItem {
    id: string;
    type: string;
    message: string;
    time: string;
}

/**
 * MobileQuickDash — Phase 3 at-a-glance dashboard.
 * Designed for the "3 minutes on the bus" use case.
 * Route: /quick
 */
export default function MobileQuickDash() {
    const { user } = useAuth();
    const [stats, setStats] = useState<QuickStat[]>([]);
    const [activity, setActivity] = useState<ActivityItem[]>([]);
    const [tip, setTip] = useState<string>('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashData();
    }, []);

    const loadDashData = async () => {
        try {
            const token = localStorage.getItem('token');
            const headers: any = token ? { Authorization: `Bearer ${token}` } : {};

            // Parallel fetch — stats + activity + AI tip
            const [statsRes, activityRes] = await Promise.all([
                fetch(`${API_BASE}/user/v1/stats`, { headers }).catch(() => null),
                fetch(`${API_BASE}/user/v1/activity`, { headers }).catch(() => null),
            ]);

            if (statsRes?.ok) {
                const data = await statsRes.json();
                setStats(buildStats(data));
            } else {
                setStats(buildStats({}));
            }

            if (activityRes?.ok) {
                const data = await activityRes.json();
                setActivity(Array.isArray(data) ? data.slice(0, 5) : []);
            }

            // AI daily tip
            setTip(getDailyTip());
        } catch (e) {
            console.error('Quick dash load failed', e);
            setStats(buildStats({}));
        } finally {
            setLoading(false);
        }
    };

    const buildStats = (data: any): QuickStat[] => [
        {
            label: 'Job Matches',
            value: data.job_matches ?? 0,
            icon: <Briefcase className="w-5 h-5" />,
            color: 'bg-indigo-50 text-indigo-600',
            to: '/umarketu',
        },
        {
            label: 'CV Score',
            value: data.cv_score ? `${data.cv_score}%` : '—',
            icon: <FileText className="w-5 h-5" />,
            color: 'bg-emerald-50 text-emerald-600',
            to: '/resume',
        },
        {
            label: 'Coaching',
            value: data.coaching_sessions ?? 0,
            icon: <Brain className="w-5 h-5" />,
            color: 'bg-purple-50 text-purple-600',
            to: '/coaching',
        },
        {
            label: 'Rewards',
            value: data.reward_points ?? 0,
            icon: <TrendingUp className="w-5 h-5" />,
            color: 'bg-amber-50 text-amber-600',
            to: '/rewards',
        },
    ];

    const getDailyTip = (): string => {
        const tips = [
            "Tailor your CV for each application — ATS systems rank keyword matches.",
            "Use the STAR method in interviews: Situation, Task, Action, Result.",
            "Your LinkedIn headline is 120 characters of prime real estate — make it count.",
            "Follow up within 24 hours after an interview to stay top of mind.",
            "Quantify achievements: '£500K revenue' beats 'increased sales'.",
            "Network before you need it — 80% of jobs are filled through connections.",
            "Update your CV every 3 months even when not job hunting.",
        ];
        const dayIndex = new Date().getDate() % tips.length;
        return tips[dayIndex];
    };

    if (loading) {
        return (
            <div className="px-4 py-6 space-y-4">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="skeleton h-20 rounded-xl" />
                ))}
            </div>
        );
    }

    return (
        <div className="px-4 py-4 max-w-lg mx-auto">
            {/* Greeting */}
            <div className="mb-5">
                <h1 className="text-2xl font-bold text-gray-900">
                    {getGreeting()}, {user?.full_name?.split(' ')[0] || 'there'}
                </h1>
                <p className="text-sm text-gray-500 mt-1">Here's your career snapshot</p>
            </div>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-2 gap-3 mb-6">
                {stats.map((stat) => (
                    <Link
                        key={stat.label}
                        to={stat.to}
                        className={`${stat.color} rounded-xl p-4 transition-transform active:scale-[0.97]`}
                    >
                        <div className="flex items-center gap-2 mb-2">
                            {stat.icon}
                            <span className="text-xs font-medium opacity-80">{stat.label}</span>
                        </div>
                        <p className="text-2xl font-bold">{stat.value}</p>
                    </Link>
                ))}
            </div>

            {/* AI Daily Tip */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-4 mb-6 text-white">
                <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-4 h-4" />
                    <span className="text-xs font-semibold uppercase tracking-wide opacity-80">AI Career Tip</span>
                </div>
                <p className="text-sm leading-relaxed">{tip}</p>
            </div>

            {/* Quick Actions */}
            <div className="mb-6">
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Quick Actions</h2>
                <div className="space-y-2">
                    <QuickAction to="/resume" icon={<Upload className="w-5 h-5" />} label="Upload CV" color="text-blue-600 bg-blue-50" />
                    <QuickAction to="/jobs/swipe" icon={<Briefcase className="w-5 h-5" />} label="Browse Jobs" color="text-indigo-600 bg-indigo-50" />
                    <QuickAction to="/coaching" icon={<Brain className="w-5 h-5" />} label="Start Coaching" color="text-purple-600 bg-purple-50" />
                </div>
            </div>

            {/* Recent Activity */}
            {activity.length > 0 && (
                <div>
                    <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Recent Activity</h2>
                    <div className="space-y-2">
                        {activity.map((item) => (
                            <div key={item.id} className="flex items-start gap-3 p-3 bg-white border border-gray-100 rounded-lg">
                                <div className="mt-0.5">
                                    {item.type === 'success' ? (
                                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                                    ) : (
                                        <Clock className="w-4 h-4 text-gray-400" />
                                    )}
                                </div>
                                <div className="min-w-0 flex-1">
                                    <p className="text-sm text-gray-800 truncate">{item.message}</p>
                                    <p className="text-xs text-gray-400 mt-0.5">{item.time}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function QuickAction({ to, icon, label, color }: { to: string; icon: React.ReactNode; label: string; color: string }) {
    return (
        <Link
            to={to}
            className="flex items-center justify-between p-3 bg-white border border-gray-100 rounded-xl hover:border-gray-200 transition-colors active:bg-gray-50 touch-target"
        >
            <div className="flex items-center gap-3">
                <span className={`p-2 rounded-lg ${color}`}>{icon}</span>
                <span className="text-sm font-medium text-gray-900">{label}</span>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400" />
        </Link>
    );
}

function getGreeting(): string {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 18) return 'Good afternoon';
    return 'Good evening';
}

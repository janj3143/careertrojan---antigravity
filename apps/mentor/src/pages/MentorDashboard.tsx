import React, { useState, useEffect } from 'react';
import MentorLayout from '../components/MentorLayout';
import { useMentorAuth } from '../context/MentorAuthContext';
import { DollarSign, Users, Calendar, Star, TrendingUp, AlertCircle } from 'lucide-react';

interface DashboardStats {
    display_name: string;
    total_packages: number;
    active_packages: number;
    total_sessions: number;
    rating: number;
    availability_status: string;
    earnings_this_month: number;
    earnings_total: number;
    pending_sessions: number;
    active_mentees: number;
}

export default function MentorDashboard() {
    const { user } = useMentorAuth();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (user?.id) {
            fetchDashboardStats();
        }
    }, [user]);

    const fetchDashboardStats = async () => {
        try {
            setLoading(true);
            // First get mentor profile ID from user ID
            const profileRes = await fetch(`/api/mentor/profile-by-user/${user?.id}`);
            if (!profileRes.ok) throw new Error('Failed to fetch mentor profile');
            const profile = await profileRes.json();

            // Then get dashboard stats
            const statsRes = await fetch(`/api/mentor/${profile.mentor_profile_id}/dashboard-stats`);
            if (!statsRes.ok) throw new Error('Failed to fetch dashboard stats');
            const data = await statsRes.json();
            setStats(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <MentorLayout>
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400">Loading dashboard...</div>
                </div>
            </MentorLayout>
        );
    }

    if (error) {
        return (
            <MentorLayout>
                <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
                    <p className="text-red-400">Error loading dashboard: {error}</p>
                </div>
            </MentorLayout>
        );
    }

    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">📊 Mentor Dashboard</h1>
                    <p className="text-slate-400">
                        Welcome back, <span className="text-green-400 font-semibold">{stats?.display_name || user?.full_name}</span>!
                        Here's your professional overview.
                    </p>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <button className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 text-left transition">
                        <div className="text-sm text-slate-400 mb-1">📦 Service Packages</div>
                        <div className="text-lg font-semibold text-white">{stats?.active_packages || 0} Active</div>
                    </button>
                    <button className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 text-left transition">
                        <div className="text-sm text-slate-400 mb-1">📨 Message Center</div>
                        <div className="text-lg font-semibold text-white">0 Unread</div>
                    </button>
                    <button className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 text-left transition">
                        <div className="text-sm text-slate-400 mb-1">💰 Financials</div>
                        <div className="text-lg font-semibold text-green-400">View Details</div>
                    </button>
                    <button className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 text-left transition">
                        <div className="text-sm text-slate-400 mb-1">🛡 Guardian Feedback</div>
                        <div className="text-lg font-semibold text-white">Review</div>
                    </button>
                </div>

                {/* Performance Metrics */}
                <div>
                    <h2 className="text-xl font-bold text-white mb-4">📈 Performance Metrics</h2>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                        <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 border border-green-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <DollarSign className="text-green-400" size={24} />
                                <div className="text-sm text-green-300">Total Earnings</div>
                            </div>
                            <div className="text-2xl font-bold text-white">
                                £{stats?.earnings_total?.toFixed(2) || '0.00'}
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border border-blue-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <Calendar className="text-blue-400" size={24} />
                                <div className="text-sm text-blue-300">Sessions Done</div>
                            </div>
                            <div className="text-2xl font-bold text-white">{stats?.total_sessions || 0}</div>
                        </div>

                        <div className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border border-amber-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <Star className="text-amber-400" size={24} />
                                <div className="text-sm text-amber-300">Avg Rating</div>
                            </div>
                            <div className="text-2xl font-bold text-white">
                                {stats?.rating ? `${stats.rating.toFixed(1)}/5` : 'N/A'}
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 border border-purple-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <Users className="text-purple-400" size={24} />
                                <div className="text-sm text-purple-300">Active Mentees</div>
                            </div>
                            <div className="text-2xl font-bold text-white">{stats?.active_mentees || 0}</div>
                        </div>

                        <div className="bg-gradient-to-br from-teal-900/40 to-teal-800/20 border border-teal-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <TrendingUp className="text-teal-400" size={24} />
                                <div className="text-sm text-teal-300">Rebooking</div>
                            </div>
                            <div className="text-2xl font-bold text-white">N/A</div>
                        </div>
                    </div>
                </div>

                {/* Charts & Analytics */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Earnings Trend */}
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <h3 className="text-lg font-bold text-white mb-4">💵 Earnings Trend</h3>
                        <div className="h-64 flex items-center justify-center text-slate-400">
                            <div className="text-center">
                                <TrendingUp size={48} className="mx-auto mb-2 text-slate-600" />
                                <p>No earnings history available yet</p>
                                <p className="text-sm mt-2">Complete sessions to see your earnings trend</p>
                            </div>
                        </div>
                    </div>

                    {/* Mentee Status */}
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <h3 className="text-lg font-bold text-white mb-4">📊 Mentee Status</h3>
                        <div className="h-64 flex items-center justify-center text-slate-400">
                            <div className="text-center">
                                <Users size={48} className="mx-auto mb-2 text-slate-600" />
                                <p>No mentee connections found</p>
                                <p className="text-sm mt-2">Start accepting mentees to see distribution</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Upcoming Sessions & Action Items */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Upcoming Sessions */}
                    <div className="md:col-span-2 bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <h3 className="text-lg font-bold text-white mb-4">📅 Upcoming Sessions</h3>
                        <div className="space-y-3">
                            {stats?.active_mentees === 0 ? (
                                <div className="text-center py-8 text-slate-400">
                                    <Calendar size={48} className="mx-auto mb-2 text-slate-600" />
                                    <p>No active sessions scheduled</p>
                                    <p className="text-sm mt-2">Calendar integration is being finalized</p>
                                </div>
                            ) : (
                                <div className="bg-slate-800 rounded-lg p-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="font-semibold text-white">👤 Mentee Connection</div>
                                            <div className="text-sm text-slate-400">Active</div>
                                        </div>
                                        <button className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm transition">
                                            View Progress
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Action Items */}
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <h3 className="text-lg font-bold text-white mb-4">✅ Action Items</h3>
                        <div className="space-y-3">
                            {stats?.earnings_total && stats.earnings_total > 0 ? (
                                <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-3">
                                    <div className="flex items-start gap-2">
                                        <AlertCircle className="text-amber-400 mt-0.5" size={16} />
                                        <div>
                                            <div className="text-sm font-semibold text-amber-300">Pending Payout</div>
                                            <div className="text-xs text-amber-400">£{stats.earnings_total.toFixed(2)}</div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-3">
                                    <div className="text-sm text-green-300">💰 All payouts up to date</div>
                                </div>
                            )}

                            <div className="bg-slate-800 rounded-lg p-3">
                                <div className="text-sm text-slate-300">📋 No pending document signatures</div>
                            </div>

                            <div className="bg-slate-800 rounded-lg p-3">
                                <div className="text-sm text-slate-300">⭐ No new reviews to moderate</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="text-center text-sm text-slate-500 pt-4 border-t border-slate-700">
                    📊 CareerTrojan Mentor Portal | Business Performance Overview
                </div>
            </div>
        </MentorLayout>
    );
}

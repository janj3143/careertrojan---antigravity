import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Users, Briefcase, DollarSign, Activity, TrendingUp, AlertCircle } from 'lucide-react';

interface DashboardStats {
    total_users: number;
    active_users: number;
    total_mentors: number;
    active_mentors: number;
    total_revenue: number;
    monthly_revenue: number;
    active_sessions: number;
    pending_reviews: number;
}

export default function AdminHome() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardStats();
    }, []);

    const fetchDashboardStats = async () => {
        try {
            const response = await fetch('/api/admin/v1/dashboard/snapshot');
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Error fetching dashboard stats:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🏠 Admin Dashboard</h1>
                    <p className="text-slate-400">CareerTrojan platform overview and key metrics</p>
                </div>

                {loading ? (
                    <div className="text-center py-12 text-slate-400">Loading dashboard...</div>
                ) : (
                    <>
                        {/* Key Metrics */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border border-blue-700/50 rounded-lg p-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <Users className="text-blue-400" size={24} />
                                    <div className="text-sm text-blue-300">Total Users</div>
                                </div>
                                <div className="text-3xl font-bold text-white">{stats?.total_users || 0}</div>
                                <div className="text-xs text-blue-400 mt-1">{stats?.active_users || 0} active</div>
                            </div>

                            <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 border border-green-700/50 rounded-lg p-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <Briefcase className="text-green-400" size={24} />
                                    <div className="text-sm text-green-300">Total Mentors</div>
                                </div>
                                <div className="text-3xl font-bold text-white">{stats?.total_mentors || 0}</div>
                                <div className="text-xs text-green-400 mt-1">{stats?.active_mentors || 0} active</div>
                            </div>

                            <div className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border border-amber-700/50 rounded-lg p-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <DollarSign className="text-amber-400" size={24} />
                                    <div className="text-sm text-amber-300">Total Revenue</div>
                                </div>
                                <div className="text-3xl font-bold text-white">£{stats?.total_revenue?.toFixed(0) || 0}</div>
                                <div className="text-xs text-amber-400 mt-1">£{stats?.monthly_revenue?.toFixed(0) || 0} this month</div>
                            </div>

                            <div className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 border border-purple-700/50 rounded-lg p-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <Activity className="text-purple-400" size={24} />
                                    <div className="text-sm text-purple-300">Active Sessions</div>
                                </div>
                                <div className="text-3xl font-bold text-white">{stats?.active_sessions || 0}</div>
                                <div className="text-xs text-purple-400 mt-1">Live mentorship</div>
                            </div>
                        </div>

                        {/* Quick Actions */}
                        <div>
                            <h2 className="text-xl font-bold text-white mb-4">⚡ Quick Actions</h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <a href="/admin/users" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 transition">
                                    <div className="text-lg font-semibold text-white mb-1">👥 User Management</div>
                                    <div className="text-sm text-slate-400">Manage user accounts and permissions</div>
                                </a>
                                <a href="/admin/mentors" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 transition">
                                    <div className="text-lg font-semibold text-white mb-1">🎓 Mentor Management</div>
                                    <div className="text-sm text-slate-400">Review and approve mentor applications</div>
                                </a>
                                <a href="/admin/tokens" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 transition">
                                    <div className="text-lg font-semibold text-white mb-1">🔑 Token Management</div>
                                    <div className="text-sm text-slate-400">Configure API tokens and credits</div>
                                </a>
                                <a href="/admin/analytics" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 transition">
                                    <div className="text-lg font-semibold text-white mb-1">📊 Analytics</div>
                                    <div className="text-sm text-slate-400">View platform analytics and insights</div>
                                </a>
                                <a href="/admin/service-status" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 transition">
                                    <div className="text-lg font-semibold text-white mb-1">🔧 Service Status</div>
                                    <div className="text-sm text-slate-400">Monitor system health and services</div>
                                </a>
                                <a href="/admin/ai-enrichment" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 transition">
                                    <div className="text-lg font-semibold text-white mb-1">🤖 AI Enrichment</div>
                                    <div className="text-sm text-slate-400">Manage AI data enrichment pipeline</div>
                                </a>
                            </div>
                        </div>

                        {/* Alerts */}
                        {stats?.pending_reviews && stats.pending_reviews > 0 && (
                            <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <AlertCircle className="text-amber-400 mt-0.5" size={20} />
                                    <div>
                                        <div className="font-semibold text-amber-300 mb-1">Pending Reviews</div>
                                        <div className="text-sm text-amber-400">
                                            {stats.pending_reviews} mentor applications awaiting review
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* System Health */}
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-white mb-4">🔧 System Health</h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                    <div>
                                        <div className="text-sm font-semibold text-white">Backend API</div>
                                        <div className="text-xs text-slate-400">Operational</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                    <div>
                                        <div className="text-sm font-semibold text-white">Database</div>
                                        <div className="text-xs text-slate-400">Operational</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                    <div>
                                        <div className="text-sm font-semibold text-white">AI Engine</div>
                                        <div className="text-xs text-slate-400">Operational</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </AdminLayout>
    );
}

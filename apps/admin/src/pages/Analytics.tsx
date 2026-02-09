import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { BarChart3, TrendingUp, Users, DollarSign, Activity } from 'lucide-react';

interface AnalyticsData {
    user_growth: { month: string; count: number }[];
    revenue_trend: { month: string; amount: number }[];
    session_stats: { total: number; completed: number; cancelled: number };
    top_mentors: { name: string; sessions: number; revenue: number }[];
}

export default function Analytics() {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('30d');

    useEffect(() => {
        fetchAnalytics();
    }, [timeRange]);

    const fetchAnalytics = async () => {
        try {
            const response = await fetch(`/api/admin/analytics?range=${timeRange}`);
            if (response.ok) {
                const analyticsData = await response.json();
                setData(analyticsData);
            }
        } catch (err) {
            console.error('Error fetching analytics:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">📊 Analytics</h1>
                        <p className="text-slate-400">Platform analytics and insights</p>
                    </div>
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value)}
                        className="px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                    >
                        <option value="7d">Last 7 days</option>
                        <option value="30d">Last 30 days</option>
                        <option value="90d">Last 90 days</option>
                        <option value="1y">Last year</option>
                    </select>
                </div>

                {loading ? (
                    <div className="text-center py-12 text-slate-400">Loading analytics...</div>
                ) : (
                    <>
                        {/* Key Metrics */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border border-blue-700/50 rounded-lg p-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <Activity className="text-blue-400" size={24} />
                                    <div className="text-sm text-blue-300">Total Sessions</div>
                                </div>
                                <div className="text-3xl font-bold text-white">{data?.session_stats.total || 0}</div>
                                <div className="text-xs text-blue-400 mt-1">
                                    {data?.session_stats.completed || 0} completed
                                </div>
                            </div>

                            <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 border border-green-700/50 rounded-lg p-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <TrendingUp className="text-green-400" size={24} />
                                    <div className="text-sm text-green-300">Completion Rate</div>
                                </div>
                                <div className="text-3xl font-bold text-white">
                                    {data?.session_stats.total
                                        ? Math.round((data.session_stats.completed / data.session_stats.total) * 100)
                                        : 0}%
                                </div>
                                <div className="text-xs text-green-400 mt-1">
                                    {data?.session_stats.cancelled || 0} cancelled
                                </div>
                            </div>

                            <div className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border border-amber-700/50 rounded-lg p-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <DollarSign className="text-amber-400" size={24} />
                                    <div className="text-sm text-amber-300">Revenue</div>
                                </div>
                                <div className="text-3xl font-bold text-white">
                                    £{data?.revenue_trend.reduce((sum, item) => sum + item.amount, 0).toFixed(0) || 0}
                                </div>
                                <div className="text-xs text-amber-400 mt-1">Total for period</div>
                            </div>
                        </div>

                        {/* User Growth Chart */}
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-white mb-4">👥 User Growth</h2>
                            <div className="h-64 flex items-end gap-2">
                                {data?.user_growth.map((item, idx) => {
                                    const maxCount = Math.max(...(data.user_growth.map(d => d.count) || [1]));
                                    const height = (item.count / maxCount) * 100;
                                    return (
                                        <div key={idx} className="flex-1 flex flex-col items-center">
                                            <div
                                                className="w-full bg-blue-600 rounded-t transition-all hover:bg-blue-500"
                                                style={{ height: `${height}%` }}
                                                title={`${item.month}: ${item.count} users`}
                                            />
                                            <div className="text-xs text-slate-400 mt-2 rotate-45 origin-left">
                                                {item.month}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Top Mentors */}
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-white mb-4">🏆 Top Mentors</h2>
                            <div className="space-y-3">
                                {data?.top_mentors.map((mentor, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                                        <div className="flex items-center gap-4">
                                            <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center font-bold">
                                                {idx + 1}
                                            </div>
                                            <div>
                                                <div className="font-semibold text-white">{mentor.name}</div>
                                                <div className="text-sm text-slate-400">{mentor.sessions} sessions</div>
                                            </div>
                                        </div>
                                        <div className="text-lg font-bold text-green-400">
                                            £{mentor.revenue.toFixed(0)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </>
                )}
            </div>
        </AdminLayout>
    );
}

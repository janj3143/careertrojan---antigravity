import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Key, Plus, Edit, Trash2, TrendingUp } from 'lucide-react';

interface TokenPlan {
    plan_id: string;
    plan_name: string;
    credits_per_month: number;
    price_monthly: number;
    price_annual: number;
    features: string[];
    is_active: boolean;
}

interface TokenUsage {
    total_allocated: number;
    total_used: number;
    total_remaining: number;
    usage_this_month: number;
}

export default function TokenManagement() {
    const [plans, setPlans] = useState<TokenPlan[]>([]);
    const [usage, setUsage] = useState<TokenUsage | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [plansRes, usageRes] = await Promise.all([
                fetch('/api/admin/v1/tokens/config'),
                fetch('/api/admin/v1/tokens/usage')
            ]);

            if (plansRes.ok) {
                const plansData = await plansRes.json();
                setPlans(plansData.plans || []);
            }

            if (usageRes.ok) {
                const usageData = await usageRes.json();
                setUsage(usageData);
            }
        } catch (err) {
            console.error('Error fetching token data:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">🔑 Token Management</h1>
                        <p className="text-slate-400">Configure API tokens and credit plans</p>
                    </div>
                    <button className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition">
                        <Plus size={20} />
                        Create Plan
                    </button>
                </div>

                {/* Usage Overview */}
                {usage && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border border-blue-700/50 rounded-lg p-6">
                            <div className="text-sm text-blue-300 mb-2">Total Allocated</div>
                            <div className="text-3xl font-bold text-white">{usage.total_allocated.toLocaleString()}</div>
                        </div>
                        <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 border border-green-700/50 rounded-lg p-6">
                            <div className="text-sm text-green-300 mb-2">Total Used</div>
                            <div className="text-3xl font-bold text-white">{usage.total_used.toLocaleString()}</div>
                        </div>
                        <div className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border border-amber-700/50 rounded-lg p-6">
                            <div className="text-sm text-amber-300 mb-2">Remaining</div>
                            <div className="text-3xl font-bold text-white">{usage.total_remaining.toLocaleString()}</div>
                        </div>
                        <div className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 border border-purple-700/50 rounded-lg p-6">
                            <div className="text-sm text-purple-300 mb-2">This Month</div>
                            <div className="text-3xl font-bold text-white">{usage.usage_this_month.toLocaleString()}</div>
                        </div>
                    </div>
                )}

                {/* Token Plans */}
                <div>
                    <h2 className="text-xl font-bold text-white mb-4">Credit Plans</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {loading ? (
                            <div className="col-span-3 text-center py-12 text-slate-400">Loading plans...</div>
                        ) : plans.length === 0 ? (
                            <div className="col-span-3 text-center py-12">
                                <Key size={48} className="mx-auto mb-4 text-slate-600" />
                                <p className="text-slate-400">No token plans configured</p>
                            </div>
                        ) : (
                            plans.map(plan => (
                                <div key={plan.plan_id} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                                    <div className="flex items-start justify-between mb-4">
                                        <div>
                                            <h3 className="text-xl font-bold text-white mb-1">{plan.plan_name}</h3>
                                            <span className={`inline-block px-2 py-1 rounded text-xs ${plan.is_active ? 'bg-green-900/30 text-green-400' : 'bg-slate-700 text-slate-400'
                                                }`}>
                                                {plan.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </div>
                                        <div className="flex gap-2">
                                            <button className="p-2 hover:bg-slate-800 rounded transition">
                                                <Edit size={16} className="text-slate-400" />
                                            </button>
                                            <button className="p-2 hover:bg-slate-800 rounded transition">
                                                <Trash2 size={16} className="text-red-400" />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="mb-4">
                                        <div className="text-3xl font-bold text-white mb-1">
                                            {plan.credits_per_month.toLocaleString()}
                                        </div>
                                        <div className="text-sm text-slate-400">credits per month</div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 mb-4">
                                        <div>
                                            <div className="text-sm text-slate-400">Monthly</div>
                                            <div className="text-lg font-bold text-white">£{plan.price_monthly}</div>
                                        </div>
                                        <div>
                                            <div className="text-sm text-slate-400">Annual</div>
                                            <div className="text-lg font-bold text-green-400">£{plan.price_annual}</div>
                                        </div>
                                    </div>

                                    <div className="border-t border-slate-700 pt-4">
                                        <div className="text-sm text-slate-400 mb-2">Features</div>
                                        <ul className="space-y-1">
                                            {plan.features.map((feature, idx) => (
                                                <li key={idx} className="text-sm text-slate-300 flex items-start gap-2">
                                                    <span className="text-green-400 mt-0.5">✓</span>
                                                    {feature}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
}

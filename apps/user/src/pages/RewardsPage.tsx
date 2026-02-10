import React, { useEffect, useState } from 'react';
import { Gift, Award, TrendingUp, CheckCircle, Lock } from 'lucide-react';
import { API } from '../lib/apiConfig';

export default function RewardsPage() {
    const [rewards, setRewards] = useState<any>(null);
    const [available, setAvailable] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const token = localStorage.getItem("token");
            const headers: any = {};
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const [rewRes, availRes] = await Promise.all([
                fetch(`${API.rewards}/rewards`, { headers }),
                fetch(`${API.rewards}/rewards/available`, { headers })
            ]);

            if (rewRes.ok) setRewards(await rewRes.json());
            if (availRes.ok) setAvailable(await availRes.json());

        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-10 text-center">Loading rewards...</div>;

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">🎁 User Rewards</h1>
                <p className="text-gray-600 mt-2">Earn tokens, unlock premium features, and own a piece of the platform.</p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl p-6 text-white shadow-lg">
                    <h3 className="font-bold text-white/90">Total Tokens</h3>
                    <p className="text-4xl font-bold mt-2">{rewards?.total_tokens || 0}</p>
                    <p className="text-sm mt-1 opacity-80">Lifetime Earned</p>
                </div>
                <div className="bg-white border rounded-xl p-6 shadow-sm">
                    <h3 className="font-bold text-gray-500 text-sm">Available to Redeem</h3>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{rewards?.available_tokens || 0}</p>
                </div>
                <div className="bg-white border rounded-xl p-6 shadow-sm">
                    <h3 className="font-bold text-gray-500 text-sm">Current Tier</h3>
                    <div className="flex items-center gap-2 mt-2">
                        <Award className="w-6 h-6 text-indigo-600" />
                        <span className="text-2xl font-bold text-gray-900">{rewards?.current_tier || "Bronze"}</span>
                    </div>
                    <div className="w-full bg-gray-100 h-1.5 rounded-full mt-3">
                        <div className="bg-indigo-600 h-1.5 rounded-full" style={{ width: `${rewards?.tier_progress || 0}%` }}></div>
                    </div>
                </div>
                <div className="bg-white border rounded-xl p-6 shadow-sm">
                    <h3 className="font-bold text-gray-500 text-sm">Ownership Stake</h3>
                    <p className="text-2xl font-bold text-green-600 mt-2">{rewards?.ownership_percentage || 0}%</p>
                    <p className="text-xs text-gray-400 mt-1">Fractional platform equity</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Available Actions */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                        <ZapIcon className="w-5 h-5 text-yellow-500" /> Ways to Earn
                    </h2>
                    <div className="space-y-4">
                        {available?.available_actions.map((action: any) => (
                            <div key={action.action} className={`flex items-center justify-between p-4 rounded-lg border ${action.completed ? 'bg-gray-50 border-gray-100' : 'bg-white border-indigo-100 hover:border-indigo-300'}`}>
                                <div className="flex items-center gap-3">
                                    {action.completed ? (
                                        <CheckCircle className="w-5 h-5 text-green-500" />
                                    ) : (
                                        <div className="w-5 h-5 rounded-full border-2 border-indigo-200"></div>
                                    )}
                                    <div>
                                        <p className={`font-medium ${action.completed ? 'text-gray-500 line-through' : 'text-gray-900'}`}>{action.description}</p>
                                        <p className="text-xs text-indigo-600 font-bold">+{action.tokens} Tokens</p>
                                    </div>
                                </div>
                                {!action.completed && (
                                    <button className="text-sm bg-indigo-50 text-indigo-700 px-3 py-1 rounded hover:bg-indigo-100">
                                        Do it
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Redemption Center */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                        <Gift className="w-5 h-5 text-purple-500" /> Redeem Rewards
                    </h2>
                    <div className="grid grid-cols-1 gap-4">
                        <RedeemCard
                            title="24h Premium Access"
                            cost={50}
                            icon={<Award className="w-6 h-6 text-orange-500" />}
                            canAfford={(rewards?.available_tokens || 0) >= 50}
                        />
                        <RedeemCard
                            title="10 AI Analysis Boosts"
                            cost={25}
                            icon={<TrendingUp className="w-6 h-6 text-blue-500" />}
                            canAfford={(rewards?.available_tokens || 0) >= 25}
                        />
                        <RedeemCard
                            title="30-min Mentor Session"
                            cost={200}
                            icon={<UserIcon className="w-6 h-6 text-green-500" />}
                            canAfford={(rewards?.available_tokens || 0) >= 200}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

function RedeemCard({ title, cost, icon, canAfford }: any) {
    return (
        <div className={`p-4 rounded-xl border flex items-center justify-between ${canAfford ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-100 opacity-70'}`}>
            <div className="flex items-center gap-4">
                <div className="p-2 bg-gray-100 rounded-lg">{icon}</div>
                <div>
                    <h3 className="font-bold text-gray-900">{title}</h3>
                    <p className="text-sm text-gray-500">{cost} Tokens</p>
                </div>
            </div>
            <button
                disabled={!canAfford}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${canAfford ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}
            >
                {canAfford ? 'Redeem' : 'Locked'}
            </button>
        </div>
    )
}

function ZapIcon(props: any) {
    return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>
}

function UserIcon(props: any) {
    return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
}

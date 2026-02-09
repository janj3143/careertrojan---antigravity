import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Target, Search, TrendingUp } from 'lucide-react';

interface Competitor {
    name: string;
    market_share: number;
    pricing: string;
    strengths: string[];
    weaknesses: string[];
}

export default function CompetitiveIntel() {
    const [competitors] = useState<Competitor[]>([
        {
            name: 'LinkedIn Learning',
            market_share: 35,
            pricing: '£24.99/month',
            strengths: ['Large network', 'Brand recognition', 'Content library'],
            weaknesses: ['Generic content', 'Limited personalization']
        },
        {
            name: 'MentorCruise',
            market_share: 15,
            pricing: '£99-299/month',
            strengths: ['1-on-1 mentorship', 'Tech focus'],
            weaknesses: ['High cost', 'Limited industries']
        }
    ]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🎯 Competitive Intelligence</h1>
                    <p className="text-slate-400">Competitor analysis and market positioning</p>
                </div>

                <div className="grid grid-cols-1 gap-6">
                    {competitors.map((comp, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className="text-2xl font-bold text-white mb-2">{comp.name}</h3>
                                    <div className="text-lg text-green-400 font-semibold">{comp.pricing}</div>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm text-slate-400 mb-1">Market Share</div>
                                    <div className="text-3xl font-bold text-white">{comp.market_share}%</div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <div className="text-sm font-semibold text-green-400 mb-2">✓ Strengths</div>
                                    <ul className="space-y-1">
                                        {comp.strengths.map((s, i) => (
                                            <li key={i} className="text-sm text-slate-300">• {s}</li>
                                        ))}
                                    </ul>
                                </div>
                                <div>
                                    <div className="text-sm font-semibold text-red-400 mb-2">✗ Weaknesses</div>
                                    <ul className="space-y-1">
                                        {comp.weaknesses.map((w, i) => (
                                            <li key={i} className="text-sm text-slate-300">• {w}</li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AdminLayout>
    );
}

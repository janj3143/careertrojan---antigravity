import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { TrendingUp, Building2, DollarSign, Users } from 'lucide-react';

interface MarketData {
    industry: string;
    avg_salary: number;
    job_openings: number;
    growth_rate: number;
    demand_level: 'high' | 'medium' | 'low';
}

export default function MarketIntelligence() {
    const [data, setData] = useState<MarketData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchMarketData();
    }, []);

    const fetchMarketData = async () => {
        try {
            const response = await fetch('/api/intelligence/v1/market');
            if (response.ok) {
                const marketData = await response.json();
                setData(marketData.industries || []);
            }
        } catch (err) {
            console.error('Error fetching market data:', err);
        } finally {
            setLoading(false);
        }
    };

    const getDemandColor = (level: string) => {
        switch (level) {
            case 'high': return 'text-green-400 bg-green-900/30';
            case 'medium': return 'text-amber-400 bg-amber-900/30';
            case 'low': return 'text-slate-400 bg-slate-700';
            default: return 'text-slate-400 bg-slate-700';
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">📈 Market Intelligence</h1>
                    <p className="text-slate-400">Industry trends and market analysis</p>
                </div>

                {loading ? (
                    <div className="text-center py-12 text-slate-400">Loading market data...</div>
                ) : (
                    <div className="grid grid-cols-1 gap-4">
                        {data.map((industry, idx) => (
                            <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1">{industry.industry}</h3>
                                        <span className={`inline-flex px-3 py-1 rounded text-xs font-medium ${getDemandColor(industry.demand_level)}`}>
                                            {industry.demand_level.toUpperCase()} DEMAND
                                        </span>
                                    </div>
                                    <TrendingUp className={industry.growth_rate > 0 ? 'text-green-400' : 'text-red-400'} size={24} />
                                </div>

                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
                                            <DollarSign size={16} />
                                            Avg Salary
                                        </div>
                                        <div className="text-2xl font-bold text-white">
                                            £{industry.avg_salary.toLocaleString()}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
                                            <Building2 size={16} />
                                            Job Openings
                                        </div>
                                        <div className="text-2xl font-bold text-white">
                                            {industry.job_openings.toLocaleString()}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
                                            <TrendingUp size={16} />
                                            Growth Rate
                                        </div>
                                        <div className={`text-2xl font-bold ${industry.growth_rate > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {industry.growth_rate > 0 ? '+' : ''}{industry.growth_rate}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </AdminLayout>
    );
}

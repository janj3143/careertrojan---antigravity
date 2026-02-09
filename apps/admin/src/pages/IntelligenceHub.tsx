import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { Brain, Database, TrendingUp, Users } from 'lucide-react';

export default function IntelligenceHub() {
    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🧠 Intelligence Hub</h1>
                    <p className="text-slate-400">Centralized intelligence and insights dashboard</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <a href="/admin/market-intelligence" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-6 transition">
                        <TrendingUp className="text-blue-400 mb-3" size={32} />
                        <h3 className="text-xl font-bold text-white mb-2">Market Intelligence</h3>
                        <p className="text-sm text-slate-400">Industry trends and market analysis</p>
                    </a>

                    <a href="/admin/competitive-intel" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-6 transition">
                        <Users className="text-green-400 mb-3" size={32} />
                        <h3 className="text-xl font-bold text-white mb-2">Competitive Intel</h3>
                        <p className="text-sm text-slate-400">Competitor analysis and positioning</p>
                    </a>

                    <a href="/admin/web-company-intel" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-6 transition">
                        <Database className="text-amber-400 mb-3" size={32} />
                        <h3 className="text-xl font-bold text-white mb-2">Company Intelligence</h3>
                        <p className="text-sm text-slate-400">Company data and hiring insights</p>
                    </a>

                    <a href="/admin/career-patterns" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-6 transition">
                        <Brain className="text-purple-400 mb-3" size={32} />
                        <h3 className="text-xl font-bold text-white mb-2">Career Patterns</h3>
                        <p className="text-sm text-slate-400">Career progression insights</p>
                    </a>
                </div>
            </div>
        </AdminLayout>
    );
}

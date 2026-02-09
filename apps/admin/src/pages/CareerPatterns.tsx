import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { TrendingUp, ArrowRight } from 'lucide-react';

interface CareerPath {
    from: string;
    to: string;
    frequency: number;
    avg_time_years: number;
}

export default function CareerPatterns() {
    const patterns: CareerPath[] = [
        {
            from: 'Software Engineer',
            to: 'Senior Software Engineer',
            frequency: 85,
            avg_time_years: 3
        },
        {
            from: 'Product Manager',
            to: 'Senior Product Manager',
            frequency: 72,
            avg_time_years: 4
        }
    ];

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">📊 Career Patterns</h1>
                    <p className="text-slate-400">Common career progression paths</p>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {patterns.map((pattern, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center gap-4">
                                <div className="flex-1 text-center">
                                    <div className="text-lg font-semibold text-white">{pattern.from}</div>
                                </div>
                                <ArrowRight className="text-green-400" size={32} />
                                <div className="flex-1 text-center">
                                    <div className="text-lg font-semibold text-white">{pattern.to}</div>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-700">
                                <div className="text-center">
                                    <div className="text-sm text-slate-400">Frequency</div>
                                    <div className="text-2xl font-bold text-green-400">{pattern.frequency}%</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-sm text-slate-400">Avg Time</div>
                                    <div className="text-2xl font-bold text-white">{pattern.avg_time_years} years</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AdminLayout>
    );
}

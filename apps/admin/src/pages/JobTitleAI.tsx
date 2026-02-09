import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Briefcase, Brain, TrendingUp } from 'lucide-react';

interface JobTitle {
    title: string;
    category: string;
    avg_salary: number;
    demand_score: number;
    ai_generated: boolean;
}

export default function JobTitleAI() {
    const [titles] = useState<JobTitle[]>([
        {
            title: 'AI Product Manager',
            category: 'Product Management',
            avg_salary: 95000,
            demand_score: 92,
            ai_generated: true
        },
        {
            title: 'Senior Software Engineer',
            category: 'Engineering',
            avg_salary: 85000,
            demand_score: 88,
            ai_generated: false
        }
    ]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">💼 Job Title AI</h1>
                    <p className="text-slate-400">AI-powered job title analysis and generation</p>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {titles.map((job, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="text-xl font-bold text-white">{job.title}</h3>
                                        {job.ai_generated && (
                                            <span className="px-2 py-0.5 bg-purple-900/30 text-purple-400 rounded text-xs">
                                                AI Generated
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-sm text-slate-400">{job.category}</div>
                                </div>
                                <Brain className="text-purple-400" size={24} />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <div className="text-sm text-slate-400 mb-1">Avg Salary</div>
                                    <div className="text-2xl font-bold text-green-400">
                                        £{job.avg_salary.toLocaleString()}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-sm text-slate-400 mb-1">Demand Score</div>
                                    <div className="text-2xl font-bold text-white">{job.demand_score}/100</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AdminLayout>
    );
}

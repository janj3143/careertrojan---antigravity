import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { Cloud } from 'lucide-react';

export default function JobTitleCloud() {
    const jobTitles = [
        { text: 'Product Manager', size: 32, color: 'text-blue-400' },
        { text: 'Software Engineer', size: 28, color: 'text-green-400' },
        { text: 'Data Scientist', size: 24, color: 'text-purple-400' },
        { text: 'UX Designer', size: 20, color: 'text-amber-400' },
        { text: 'DevOps Engineer', size: 18, color: 'text-red-400' },
        { text: 'Marketing Manager', size: 16, color: 'text-pink-400' },
        { text: 'Sales Director', size: 14, color: 'text-cyan-400' }
    ];

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">☁️ Job Title Cloud</h1>
                    <p className="text-slate-400">Visual representation of trending job titles</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-12">
                    <div className="flex flex-wrap items-center justify-center gap-6">
                        {jobTitles.map((job, idx) => (
                            <span
                                key={idx}
                                className={`${job.color} font-bold cursor-pointer hover:opacity-80 transition`}
                                style={{ fontSize: `${job.size}px` }}
                            >
                                {job.text}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
}

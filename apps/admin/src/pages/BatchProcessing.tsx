import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Layers, Play, Clock } from 'lucide-react';

interface BatchJob {
    job_id: string;
    type: string;
    status: 'queued' | 'running' | 'completed';
    progress: number;
}

export default function BatchProcessing() {
    const [jobs] = useState<BatchJob[]>([
        { job_id: 'batch-001', type: 'Data Import', status: 'running', progress: 45 }
    ]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">⚙️ Batch Processing</h1>
                    <p className="text-slate-400">Manage batch jobs and processing</p>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {jobs.map(job => (
                        <div key={job.job_id} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <h3 className="text-lg font-bold text-white">{job.type}</h3>
                                    <div className="text-sm text-slate-400">{job.job_id}</div>
                                </div>
                                <span className="px-3 py-1 bg-blue-900/30 text-blue-400 rounded text-sm">
                                    {job.status.toUpperCase()}
                                </span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-2">
                                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${job.progress}%` }} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AdminLayout>
    );
}

import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Brain, Play, Square, TrendingUp } from 'lucide-react';

interface TrainingJob {
    model_name: string;
    status: 'training' | 'completed' | 'failed';
    progress: number;
    accuracy: number;
    started_at: string;
}

export default function ModelTraining() {
    const [jobs] = useState<TrainingJob[]>([
        {
            model_name: 'Resume Parser v2',
            status: 'training',
            progress: 65,
            accuracy: 0.89,
            started_at: new Date().toISOString()
        }
    ]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">🤖 Model Training</h1>
                        <p className="text-slate-400">AI model training and management</p>
                    </div>
                    <button className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition">
                        <Play size={18} />
                        Start Training
                    </button>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {jobs.map((job, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-1">{job.model_name}</h3>
                                    <div className="text-sm text-slate-400">
                                        Started {new Date(job.started_at).toLocaleString()}
                                    </div>
                                </div>
                                <span className={`px-3 py-1 rounded text-sm ${job.status === 'training' ? 'bg-blue-900/30 text-blue-400' :
                                        job.status === 'completed' ? 'bg-green-900/30 text-green-400' :
                                            'bg-red-900/30 text-red-400'
                                    }`}>
                                    {job.status.toUpperCase()}
                                </span>
                            </div>

                            <div className="mb-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm text-slate-400">Training Progress</span>
                                    <span className="text-sm font-semibold text-white">{job.progress}%</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-3">
                                    <div
                                        className="bg-blue-600 h-3 rounded-full transition-all"
                                        style={{ width: `${job.progress}%` }}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <div className="text-sm text-slate-400">Accuracy</div>
                                    <div className="text-2xl font-bold text-green-400">
                                        {(job.accuracy * 100).toFixed(1)}%
                                    </div>
                                </div>
                                <div className="flex justify-end">
                                    <button className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition flex items-center gap-2">
                                        <Square size={16} />
                                        Stop
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AdminLayout>
    );
}

import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Brain, Upload, Database, TrendingUp, RefreshCw, CheckCircle } from 'lucide-react';

interface EnrichmentJob {
    job_id: string;
    type: 'resume' | 'profile' | 'company';
    status: 'pending' | 'processing' | 'completed' | 'failed';
    records_processed: number;
    records_total: number;
    started_at: string;
    completed_at?: string;
}

interface EnrichmentStats {
    total_enriched: number;
    enriched_today: number;
    success_rate: number;
    avg_processing_time: number;
}

export default function AIEnrichment() {
    const [jobs, setJobs] = useState<EnrichmentJob[]>([]);
    const [stats, setStats] = useState<EnrichmentStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [jobsRes, statsRes] = await Promise.all([
                fetch('/api/admin/v1/ai/enrichment/jobs'),
                fetch('/api/admin/v1/ai/enrichment/status')
            ]);

            if (jobsRes.ok) {
                const data = await jobsRes.json();
                setJobs(data.jobs || []);
            }

            if (statsRes.ok) {
                const data = await statsRes.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Error fetching enrichment data:', err);
        } finally {
            setLoading(false);
        }
    };

    const triggerEnrichment = async (type: string) => {
        try {
            await fetch('/api/admin/v1/ai/enrichment/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type })
            });
            await fetchData();
        } catch (err) {
            console.error('Error triggering enrichment:', err);
        }
    };

    const getStatusBadge = (status: string) => {
        const styles = {
            pending: 'bg-amber-900/30 text-amber-400 border-amber-700',
            processing: 'bg-blue-900/30 text-blue-400 border-blue-700',
            completed: 'bg-green-900/30 text-green-400 border-green-700',
            failed: 'bg-red-900/30 text-red-400 border-red-700'
        };
        return styles[status as keyof typeof styles];
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🤖 AI Enrichment</h1>
                    <p className="text-slate-400">Manage AI data enrichment pipeline</p>
                </div>

                {/* Stats */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border border-blue-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <Database className="text-blue-400" size={24} />
                                <div className="text-sm text-blue-300">Total Enriched</div>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.total_enriched.toLocaleString()}</div>
                        </div>

                        <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 border border-green-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <TrendingUp className="text-green-400" size={24} />
                                <div className="text-sm text-green-300">Today</div>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.enriched_today}</div>
                        </div>

                        <div className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border border-amber-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <CheckCircle className="text-amber-400" size={24} />
                                <div className="text-sm text-amber-300">Success Rate</div>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.success_rate}%</div>
                        </div>

                        <div className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 border border-purple-700/50 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <Brain className="text-purple-400" size={24} />
                                <div className="text-sm text-purple-300">Avg Time</div>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.avg_processing_time}s</div>
                        </div>
                    </div>
                )}

                {/* Trigger Actions */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <h2 className="text-xl font-bold text-white mb-4">Trigger Enrichment</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <button
                            onClick={() => triggerEnrichment('resume')}
                            className="flex items-center gap-3 p-4 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg transition"
                        >
                            <Upload className="text-blue-400" size={24} />
                            <div className="text-left">
                                <div className="font-semibold text-white">Resume Enrichment</div>
                                <div className="text-xs text-slate-400">Process uploaded resumes</div>
                            </div>
                        </button>

                        <button
                            onClick={() => triggerEnrichment('profile')}
                            className="flex items-center gap-3 p-4 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg transition"
                        >
                            <Brain className="text-green-400" size={24} />
                            <div className="text-left">
                                <div className="font-semibold text-white">Profile Enrichment</div>
                                <div className="text-xs text-slate-400">Enhance user profiles</div>
                            </div>
                        </button>

                        <button
                            onClick={() => triggerEnrichment('company')}
                            className="flex items-center gap-3 p-4 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg transition"
                        >
                            <Database className="text-amber-400" size={24} />
                            <div className="text-left">
                                <div className="font-semibold text-white">Company Data</div>
                                <div className="text-xs text-slate-400">Update company info</div>
                            </div>
                        </button>
                    </div>
                </div>

                {/* Jobs Table */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white">Enrichment Jobs</h2>
                        <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition">
                            <RefreshCw size={16} />
                            Refresh
                        </button>
                    </div>
                    {loading ? (
                        <div className="text-center py-12 text-slate-400">Loading jobs...</div>
                    ) : (
                        <table className="w-full">
                            <thead className="bg-slate-800 border-b border-slate-700">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Job ID</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Progress</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Started</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {jobs.length === 0 ? (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                                            No enrichment jobs
                                        </td>
                                    </tr>
                                ) : (
                                    jobs.map(job => (
                                        <tr key={job.job_id} className="hover:bg-slate-800/50 transition">
                                            <td className="px-6 py-4 text-sm font-mono text-slate-300">{job.job_id.slice(0, 8)}</td>
                                            <td className="px-6 py-4 text-sm text-white capitalize">{job.type}</td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex px-2.5 py-0.5 rounded border text-xs font-medium ${getStatusBadge(job.status)}`}>
                                                    {job.status.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="flex-1 bg-slate-800 rounded-full h-2">
                                                        <div
                                                            className="bg-blue-600 h-2 rounded-full transition-all"
                                                            style={{ width: `${(job.records_processed / job.records_total) * 100}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-xs text-slate-400 w-16">
                                                        {job.records_processed}/{job.records_total}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                {new Date(job.started_at).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </AdminLayout>
    );
}

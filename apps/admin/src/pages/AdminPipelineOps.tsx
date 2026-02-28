import { useEffect, useMemo, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Activity, Loader2, Database } from 'lucide-react';

interface PipelineOpsResponse {
    status: string;
    summary: {
        ingest: {
            log_path: string;
            last_run: Record<string, unknown> | null;
        };
        enhancement: {
            report_path: string;
            report: Record<string, unknown>;
        };
        models: {
            root: string;
            count: number;
            items: Array<{ path: string; size_bytes: number; modified_at: number }>;
        };
    };
}

async function fetchPipelineOps(): Promise<PipelineOpsResponse> {
    const response = await fetch('/api/intelligence/v1/pipeline/ops-summary', {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
        throw new Error(await response.text());
    }
    return response.json() as Promise<PipelineOpsResponse>;
}

function formatBytes(size: number): string {
    if (!size) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let value = size;
    let idx = 0;
    while (value >= 1024 && idx < units.length - 1) {
        value /= 1024;
        idx += 1;
    }
    return `${value.toFixed(idx === 0 ? 0 : 2)} ${units[idx]}`;
}

export default function AdminPipelineOps() {
    const [payload, setPayload] = useState<PipelineOpsResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string>('');

    const load = async () => {
        try {
            setLoading(true);
            setError('');
            setPayload(await fetchPipelineOps());
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to load pipeline ops summary');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, []);

    const modelRows = useMemo(() => payload?.summary.models.items ?? [], [payload]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">⚙️ Admin AI Pipeline Ops</h1>
                    <p className="text-slate-400">Ingest/enhancement run status and model artefact inventory</p>
                </div>

                {loading ? (
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 flex items-center gap-3 text-slate-300">
                        <Loader2 size={18} className="animate-spin" /> Loading pipeline summary...
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                                <div className="text-xs text-slate-400">Last Ingest Run</div>
                                <div className="text-sm text-white mt-2 break-words">
                                    {payload?.summary.ingest.last_run ? JSON.stringify(payload.summary.ingest.last_run) : 'none'}
                                </div>
                            </div>
                            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                                <div className="text-xs text-slate-400">Enhancement Report</div>
                                <div className="text-sm text-white mt-2 break-words">
                                    {payload?.summary.enhancement.report_path || 'missing'}
                                </div>
                            </div>
                            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                                <div className="text-xs text-slate-400">Model Artefacts</div>
                                <div className="text-2xl font-semibold text-white mt-1 inline-flex items-center gap-2">
                                    <Database size={16} className="text-amber-400" /> {payload?.summary.models.count ?? 0}
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="text-sm font-semibold text-white inline-flex items-center gap-2">
                                    <Activity size={16} className="text-blue-400" /> Model Inventory
                                </div>
                                <button
                                    type="button"
                                    onClick={load}
                                    className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-sm text-white"
                                >
                                    Refresh
                                </button>
                            </div>
                            <div className="overflow-x-auto border border-slate-700 rounded-lg">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-slate-800 text-slate-300">
                                        <tr>
                                            <th className="p-3">Path</th>
                                            <th className="p-3">Size</th>
                                            <th className="p-3">Modified</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {modelRows.map((row) => (
                                            <tr key={`${row.path}-${row.modified_at}`} className="border-t border-slate-700 text-slate-200">
                                                <td className="p-3 break-words">{row.path}</td>
                                                <td className="p-3">{formatBytes(row.size_bytes)}</td>
                                                <td className="p-3">{new Date(row.modified_at * 1000).toISOString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}

                {error && <div className="bg-red-950 border border-red-700 rounded-lg p-3 text-red-200 text-sm">{error}</div>}
            </div>
        </AdminLayout>
    );
}

import { useEffect, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Headphones, Link as LinkIcon, Loader2, ShieldCheck } from 'lucide-react';

interface SupportStatusResponse {
    status: string;
    support: {
        provider: string;
        widget_enabled: boolean;
        sso_enabled: boolean;
        links: {
            queue_url: string;
            macros_url: string;
        };
    };
}

async function fetchSupportStatus(): Promise<SupportStatusResponse> {
    const response = await fetch('/api/intelligence/v1/support/status', {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
        throw new Error(await response.text());
    }
    return response.json() as Promise<SupportStatusResponse>;
}

export default function AdminSupportOps() {
    const [payload, setPayload] = useState<SupportStatusResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string>('');

    const load = async () => {
        try {
            setLoading(true);
            setError('');
            setPayload(await fetchSupportStatus());
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to load support status');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, []);

    const queueUrl = payload?.support.links.queue_url || 'https://support.careertrojan.com';
    const macrosUrl = payload?.support.links.macros_url || 'https://support.careertrojan.com/agent/macros';

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🎫 Admin Support Ops</h1>
                    <p className="text-slate-400">Helpdesk provider status and support workflow entry points</p>
                </div>

                {loading ? (
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 flex items-center gap-3 text-slate-300">
                        <Loader2 size={18} className="animate-spin" /> Loading support status...
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                            <div className="text-xs text-slate-400">Provider</div>
                            <div className="text-xl font-semibold text-white mt-1 inline-flex items-center gap-2">
                                <Headphones size={16} className="text-blue-400" /> {payload?.support.provider ?? 'pending'}
                            </div>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                            <div className="text-xs text-slate-400">Widget State</div>
                            <div className="text-xl font-semibold mt-1 text-white">{payload?.support.widget_enabled ? 'enabled' : 'disabled'}</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                            <div className="text-xs text-slate-400">SSO State</div>
                            <div className="text-xl font-semibold mt-1 inline-flex items-center gap-2 text-white">
                                <ShieldCheck size={16} className="text-emerald-400" /> {payload?.support.sso_enabled ? 'enabled' : 'disabled'}
                            </div>
                        </div>
                    </div>
                )}

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
                    <div className="text-sm font-semibold text-white">Queue & Macro Links</div>
                    <div className="flex flex-wrap gap-3">
                        <a
                            href={queueUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
                        >
                            <LinkIcon size={16} /> Open Support Queue
                        </a>
                        <a
                            href={macrosUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white"
                        >
                            <LinkIcon size={16} /> Open Macros
                        </a>
                        <button
                            type="button"
                            onClick={load}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                {error && <div className="bg-red-950 border border-red-700 rounded-lg p-3 text-red-200 text-sm">{error}</div>}
            </div>
        </AdminLayout>
    );
}

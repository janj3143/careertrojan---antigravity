import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { Mail, Send, RefreshCw } from 'lucide-react';

export default function EmailIntegration() {
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);
    const [summary, setSummary] = React.useState<any>(null);
    const [providerPayload, setProviderPayload] = React.useState<any>(null);
    const [selectedType, setSelectedType] = React.useState<'verified' | 'inferred'>('verified');
    const [selectedTier, setSelectedTier] = React.useState<'A' | 'B' | 'C'>('A');
    const [trackingSummary, setTrackingSummary] = React.useState<any>(null);
    const [trackingRecords, setTrackingRecords] = React.useState<any[]>([]);
    const [trackingFilter, setTrackingFilter] = React.useState<string>('all');
    const [trackingForm, setTrackingForm] = React.useState({
        to_email: '',
        to_name: '',
        sent_at: new Date().toISOString().slice(0, 16),
        campaign: '',
        result: 'sent',
        bounce_reason: '',
        response_excerpt: '',
        notes: '',
    });

    const loadSummary = React.useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch('/api/ai-data/v1/emails/summary');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setSummary(data?.data || null);
        } catch (err: any) {
            setError(err?.message || 'Failed to load email summary');
        } finally {
            setLoading(false);
        }
    }, []);

    const loadProviderPayload = React.useCallback(async (
        provider: 'sendgrid' | 'klaviyo',
        emailType: 'verified' | 'inferred',
        trustTier: 'A' | 'B' | 'C',
    ) => {
        setError(null);
        try {
            const res = await fetch(`/api/ai-data/v1/emails/providers/${provider}?limit=2000&email_type=${emailType}&trust_tier=${trustTier}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setProviderPayload(data?.data || null);
        } catch (err: any) {
            setError(err?.message || `Failed to build ${provider} payload`);
        }
    }, []);

    React.useEffect(() => {
        loadSummary();
    }, [loadSummary]);

    const loadTrackingSummary = React.useCallback(async () => {
        try {
            const res = await fetch('/api/ai-data/v1/emails/tracking/summary');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setTrackingSummary(data?.data || null);
        } catch (err: any) {
            setError(err?.message || 'Failed to load email tracking summary');
        }
    }, []);

    const loadTrackingRecords = React.useCallback(async (result: string = trackingFilter) => {
        try {
            const query = result && result !== 'all' ? `?limit=200&result=${encodeURIComponent(result)}` : '?limit=200';
            const res = await fetch(`/api/ai-data/v1/emails/tracking${query}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setTrackingRecords(data?.records || []);
        } catch (err: any) {
            setError(err?.message || 'Failed to load email tracking records');
        }
    }, [trackingFilter]);

    const saveTracking = React.useCallback(async () => {
        setError(null);
        try {
            const payload = {
                ...trackingForm,
                sent_at: trackingForm.sent_at ? new Date(trackingForm.sent_at).toISOString() : undefined,
            };
            const res = await fetch('/api/ai-data/v1/emails/tracking', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!res.ok) {
                const msg = await res.text();
                throw new Error(msg || `HTTP ${res.status}`);
            }
            setTrackingForm((prev) => ({
                ...prev,
                to_email: '',
                to_name: '',
                campaign: '',
                bounce_reason: '',
                response_excerpt: '',
                notes: '',
            }));
            await Promise.all([loadTrackingSummary(), loadTrackingRecords()]);
        } catch (err: any) {
            setError(err?.message || 'Failed to save tracking event');
        }
    }, [trackingForm, loadTrackingSummary, loadTrackingRecords]);

    React.useEffect(() => {
        loadTrackingSummary();
        loadTrackingRecords();
    }, [loadTrackingSummary, loadTrackingRecords]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <h1 className="text-3xl font-bold text-white mb-2">📧 Email Integration</h1>
                    <button
                        onClick={loadSummary}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded transition"
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>
                <p className="text-slate-400">Unified email dataset + provider payload bridge (SendGrid/Klaviyo).</p>

                {error && (
                    <div className="bg-red-900/40 border border-red-700 text-red-200 px-4 py-3 rounded">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Email Records</p>
                        <p className="text-2xl font-bold text-white">{summary?.email_records ?? '-'}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Verified (Observed)</p>
                        <p className="text-2xl font-bold text-emerald-300">{summary?.verified_records ?? '-'}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Inferred (Educated Guess)</p>
                        <p className="text-2xl font-bold text-amber-300">{summary?.inferred_records ?? '-'}</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Unique Domains</p>
                        <p className="text-2xl font-bold text-white">{summary?.unique_domains ?? '-'}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Legacy Files to Merge</p>
                        <p className="text-2xl font-bold text-white">{summary?.folders?.legacy_file_count ?? '-'}</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Tier A (High Trust)</p>
                        <p className="text-2xl font-bold text-emerald-300">{summary?.trust_tier_counts?.A ?? '-'}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Tier B (Medium Trust)</p>
                        <p className="text-2xl font-bold text-amber-300">{summary?.trust_tier_counts?.B ?? '-'}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Tier C (Risk)</p>
                        <p className="text-2xl font-bold text-red-300">{summary?.trust_tier_counts?.C ?? '-'}</p>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                    <p className="text-slate-400 text-sm">Five-level invalidated emails (annotated false)</p>
                    <p className="text-2xl font-bold text-red-300">{summary?.invalidated_by_five_level_test ?? '-'}</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <Mail className="text-blue-400" size={32} />
                        <div>
                            <h3 className="text-lg font-bold text-white">Provider Payload Builder</h3>
                            <div className="text-sm text-green-400">Ready</div>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-3 mb-4">
                        <button
                            onClick={() => setSelectedType('verified')}
                            className={`px-3 py-2 rounded transition ${selectedType === 'verified' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-300 border border-slate-600'}`}
                        >
                            Use Verified
                        </button>
                        <button
                            onClick={() => setSelectedType('inferred')}
                            className={`px-3 py-2 rounded transition ${selectedType === 'inferred' ? 'bg-amber-600 text-white' : 'bg-slate-800 text-slate-300 border border-slate-600'}`}
                        >
                            Use Inferred
                        </button>
                    </div>

                    <div className="flex flex-wrap gap-3 mb-4">
                        <button
                            onClick={() => setSelectedTier('A')}
                            className={`px-3 py-2 rounded transition ${selectedTier === 'A' ? 'bg-emerald-700 text-white' : 'bg-slate-800 text-slate-300 border border-slate-600'}`}
                        >
                            Tier A (High Trust)
                        </button>
                        <button
                            onClick={() => setSelectedTier('B')}
                            className={`px-3 py-2 rounded transition ${selectedTier === 'B' ? 'bg-amber-700 text-white' : 'bg-slate-800 text-slate-300 border border-slate-600'}`}
                        >
                            Tier B (Medium Trust)
                        </button>
                        <button
                            onClick={() => setSelectedTier('C')}
                            className={`px-3 py-2 rounded transition ${selectedTier === 'C' ? 'bg-red-700 text-white' : 'bg-slate-800 text-slate-300 border border-slate-600'}`}
                        >
                            Tier C (Risk)
                        </button>
                    </div>

                    <div className="text-xs text-slate-400 mb-4">
                        Outreach defaults to <span className="text-emerald-300 font-semibold">Tier A only</span>.
                    </div>

                    <div className="flex flex-wrap gap-3 mb-4">
                        <button
                            onClick={() => loadProviderPayload('sendgrid', selectedType, selectedTier)}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
                        >
                            <Send size={16} />
                            Build SendGrid Payload ({selectedType}, Tier {selectedTier})
                        </button>
                        <button
                            onClick={() => loadProviderPayload('klaviyo', selectedType, selectedTier)}
                            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 rounded transition"
                        >
                            <Send size={16} />
                            Build Klaviyo Payload ({selectedType}, Tier {selectedTier})
                        </button>
                    </div>

                    <pre className="text-xs text-slate-300 overflow-auto max-h-[360px] bg-slate-950 rounded p-3">
                        {JSON.stringify(providerPayload || summary || { note: 'No data yet' }, null, 2)}
                    </pre>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white">Email Send Tracking</h3>
                    <p className="text-sm text-slate-400">Track who was sent to, when, outcome status, bounce retry guidance, and reroute/holiday discovered emails.</p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-950 border border-slate-700 rounded p-3">
                            <p className="text-slate-400 text-xs">Total Events</p>
                            <p className="text-xl text-white font-bold">{trackingSummary?.total_events ?? 0}</p>
                        </div>
                        <div className="bg-slate-950 border border-slate-700 rounded p-3">
                            <p className="text-slate-400 text-xs">Bounces</p>
                            <p className="text-xl text-amber-300 font-bold">{trackingSummary?.result_counts?.bounce ?? 0}</p>
                        </div>
                        <div className="bg-slate-950 border border-slate-700 rounded p-3">
                            <p className="text-slate-400 text-xs">Converted Paid</p>
                            <p className="text-xl text-emerald-300 font-bold">{trackingSummary?.result_counts?.converted_paid ?? 0}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-950 border border-slate-700 rounded p-3">
                            <p className="text-slate-400 text-xs">Reroute Events</p>
                            <p className="text-xl text-blue-300 font-bold">{trackingSummary?.reroute_intelligence?.reroute_events ?? 0}</p>
                        </div>
                        <div className="bg-slate-950 border border-slate-700 rounded p-3">
                            <p className="text-slate-400 text-xs">Holiday/OOO Events</p>
                            <p className="text-xl text-amber-300 font-bold">{trackingSummary?.reroute_intelligence?.holiday_events ?? 0}</p>
                        </div>
                        <div className="bg-slate-950 border border-slate-700 rounded p-3">
                            <p className="text-slate-400 text-xs">New Discovered Emails</p>
                            <p className="text-xl text-emerald-300 font-bold">{trackingSummary?.reroute_intelligence?.discovered_targets_count ?? 0}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <input
                            value={trackingForm.to_email}
                            onChange={(e) => setTrackingForm((p) => ({ ...p, to_email: e.target.value }))}
                            className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                            placeholder="To email (required)"
                        />
                        <input
                            value={trackingForm.to_name}
                            onChange={(e) => setTrackingForm((p) => ({ ...p, to_name: e.target.value }))}
                            className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                            placeholder="To name"
                        />
                        <input
                            type="datetime-local"
                            aria-label="Sent at"
                            title="Sent at"
                            value={trackingForm.sent_at}
                            onChange={(e) => setTrackingForm((p) => ({ ...p, sent_at: e.target.value }))}
                            className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                        />
                        <input
                            value={trackingForm.campaign}
                            onChange={(e) => setTrackingForm((p) => ({ ...p, campaign: e.target.value }))}
                            className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                            placeholder="Campaign"
                        />
                        <select
                            aria-label="Result status"
                            title="Result status"
                            value={trackingForm.result}
                            onChange={(e) => setTrackingForm((p) => ({ ...p, result: e.target.value }))}
                            className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                        >
                            <option value="sent">Sent</option>
                            <option value="bounce">Bounce</option>
                            <option value="response">Response</option>
                            <option value="freemium_user">Freemium user</option>
                            <option value="converted_paid">Converted to paid</option>
                        </select>
                        <input
                            value={trackingForm.response_excerpt}
                            onChange={(e) => setTrackingForm((p) => ({ ...p, response_excerpt: e.target.value }))}
                            className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                            placeholder="Response excerpt"
                        />
                    </div>

                    {trackingForm.result === 'bounce' && (
                        <textarea
                            value={trackingForm.bounce_reason}
                            onChange={(e) => setTrackingForm((p) => ({ ...p, bounce_reason: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white min-h-[80px]"
                            placeholder="Bounce reason (e.g. user unknown / mailbox full / blocked)"
                        />
                    )}

                    <textarea
                        value={trackingForm.notes}
                        onChange={(e) => setTrackingForm((p) => ({ ...p, notes: e.target.value }))}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white min-h-[80px]"
                        placeholder="Notes"
                    />

                    <div className="flex flex-wrap items-center gap-3">
                        <button
                            onClick={saveTracking}
                            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded text-white"
                        >
                            Save Tracking Event
                        </button>
                        <select
                            aria-label="Filter tracking outcomes"
                            title="Filter tracking outcomes"
                            value={trackingFilter}
                            onChange={(e) => {
                                setTrackingFilter(e.target.value);
                                loadTrackingRecords(e.target.value);
                            }}
                            className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                        >
                            <option value="all">All outcomes</option>
                            <option value="sent">Sent</option>
                            <option value="bounce">Bounce</option>
                            <option value="response">Response</option>
                            <option value="freemium_user">Freemium user</option>
                            <option value="converted_paid">Converted to paid</option>
                        </select>
                        <button
                            onClick={() => {
                                loadTrackingSummary();
                                loadTrackingRecords();
                            }}
                            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white"
                        >
                            Refresh Tracking
                        </button>
                    </div>

                    <div className="overflow-auto max-h-[360px] border border-slate-700 rounded">
                        <table className="min-w-full text-sm text-slate-200">
                            <thead className="bg-slate-950 text-slate-400">
                                <tr>
                                    <th className="text-left px-3 py-2">To</th>
                                    <th className="text-left px-3 py-2">When</th>
                                    <th className="text-left px-3 py-2">Result</th>
                                    <th className="text-left px-3 py-2">Campaign</th>
                                    <th className="text-left px-3 py-2">Bounce Suggestion</th>
                                </tr>
                            </thead>
                            <tbody>
                                {trackingRecords.length === 0 && (
                                    <tr>
                                        <td className="px-3 py-3 text-slate-500" colSpan={5}>No tracking events yet.</td>
                                    </tr>
                                )}
                                {trackingRecords.map((row: any) => (
                                    <tr key={row.id || `${row.to_email}-${row.sent_at}`} className="border-t border-slate-800">
                                        <td className="px-3 py-2">
                                            <div className="font-medium text-white">{row.to_email}</div>
                                            <div className="text-xs text-slate-400">{row.to_name || '-'}</div>
                                        </td>
                                        <td className="px-3 py-2 text-slate-300">{row.sent_at || '-'}</td>
                                        <td className="px-3 py-2 text-slate-200">{row.result || '-'}</td>
                                        <td className="px-3 py-2 text-slate-300">{row.campaign || '-'}</td>
                                        <td className="px-3 py-2 text-amber-200">{row.bounce_attempt_suggestion || '-'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
}

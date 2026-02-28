import React, { useEffect, useState, useCallback } from 'react';
import AdminLayout from '../components/AdminLayout';
import {
    Mail, Send, Users, Search, RefreshCw, Download, Upload,
    AlertTriangle, CheckCircle, XCircle, Globe, Brain,
    BarChart3, ChevronLeft, ChevronRight, Zap, Target
} from 'lucide-react';
import API from '../lib/apiConfig';

/* ───── Types ────────────────────────────────────────────────────────── */
interface Contact {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    company: string;
    domain: string;
    source_type: 'verified' | 'guessed';
    confidence: number;
    pattern_used?: string;
    tags: string[];
    created_at: string;
    conversion_status: string;
}

interface Analytics {
    total_contacts: number;
    verified_count: number;
    guessed_count: number;
    avg_confidence: number;
    sends_total: number;
    delivered: number;
    bounced: number;
    opened: number;
    clicked: number;
    open_rate: number;
    click_rate: number;
    bounce_rate: number;
    top_domains: { domain: string; count: number }[];
    top_companies: { company: string; count: number }[];
    conversion_funnel: Record<string, number>;
}

interface DomainStats {
    total_domains: number;
    total_verified_contacts: number;
    corporate_contacts: number;
    domains: {
        domain: string;
        company: string;
        patterns: Record<string, number>;
        total_emails: number;
        primary_pattern: string;
    }[];
}

interface ProviderStatus {
    connected: boolean;
    error?: string;
    from_email?: string;
}

/* ───── Helpers ──────────────────────────────────────────────────────── */
const BASE = API.admin;
const fetcher = async (path: string, opts?: RequestInit) => {
    const token = localStorage.getItem('admin_token');
    const res = await fetch(`${BASE}${path}`, {
        ...opts,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...opts?.headers,
        },
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
};

/* ───── Sub-components ───────────────────────────────────────────────── */
function TabBtn({ active, label, onClick, icon: Icon }: {
    active: boolean; label: string; onClick: () => void; icon: React.ElementType;
}) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-colors text-sm font-medium
                ${active ? 'border-cyan-400 text-cyan-300' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
        >
            <Icon size={16} />
            {label}
        </button>
    );
}

function SummaryCard({ label, value, sub, color = 'cyan' }: {
    label: string; value: string | number; sub?: string; color?: string;
}) {
    const colors: Record<string, string> = {
        cyan: 'from-cyan-900/30 to-cyan-800/10 border-cyan-800/40',
        green: 'from-green-900/30 to-green-800/10 border-green-800/40',
        yellow: 'from-yellow-900/30 to-yellow-800/10 border-yellow-800/40',
        red: 'from-red-900/30 to-red-800/10 border-red-800/40',
        blue: 'from-blue-900/30 to-blue-800/10 border-blue-800/40',
        purple: 'from-purple-900/30 to-purple-800/10 border-purple-800/40',
    };
    return (
        <div className={`bg-gradient-to-br ${colors[color] || colors.cyan} border rounded-lg p-4`}>
            <div className="text-slate-400 text-xs uppercase tracking-wider">{label}</div>
            <div className="text-2xl font-bold text-white mt-1">{typeof value === 'number' ? value.toLocaleString() : value}</div>
            {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════
   Main Page Component
   ═══════════════════════════════════════════════════════════════════════ */
export default function EmailIntegration() {
    const [tab, setTab] = useState<'overview' | 'contacts' | 'intelligence' | 'campaigns' | 'logs'>('overview');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // ── Data state
    const [analytics, setAnalytics] = useState<Analytics | null>(null);
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [contactsMeta, setContactsMeta] = useState({ total: 0, page: 1, pages: 1 });
    const [domainStats, setDomainStats] = useState<DomainStats | null>(null);
    const [providers, setProviders] = useState<Record<string, ProviderStatus>>({});
    const [campaigns, setCampaigns] = useState<any[]>([]);
    const [logs, setLogs] = useState<any[]>([]);

    // ── Filter state
    const [searchQuery, setSearchQuery] = useState('');
    const [sourceFilter, setSourceFilter] = useState<string | null>(null);
    const [companyFilter, setCompanyFilter] = useState('');
    const [page, setPage] = useState(1);

    // ── Guess form
    const [guessFirst, setGuessFirst] = useState('');
    const [guessLast, setGuessLast] = useState('');
    const [guessCompany, setGuessCompany] = useState('');
    const [guessResults, setGuessResults] = useState<any[]>([]);
    const [guessing, setGuessing] = useState(false);

    /* ── Loaders ──────────────────────────────────────────────────────── */
    const loadOverview = useCallback(async () => {
        try {
            setLoading(true);
            const [statusRes, analyticsRes] = await Promise.all([
                fetcher('/email/status'),
                fetcher('/email/analytics?days=30'),
            ]);
            setProviders(statusRes?.providers || {});
            setAnalytics(analyticsRes);
            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadContacts = useCallback(async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams({ page: String(page), per_page: '50' });
            if (sourceFilter) params.set('source_type', sourceFilter);
            if (searchQuery) params.set('search', searchQuery);
            if (companyFilter) params.set('company', companyFilter);
            const res = await fetcher(`/contacts?${params}`);
            setContacts(res.contacts || []);
            setContactsMeta({ total: res.total, page: res.page, pages: res.pages });
            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [page, sourceFilter, searchQuery, companyFilter]);

    const loadDomains = useCallback(async () => {
        try {
            setLoading(true);
            const res = await fetcher('/intelligence/domains');
            setDomainStats(res);
            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadCampaigns = useCallback(async () => {
        try {
            setLoading(true);
            const res = await fetcher('/campaigns');
            setCampaigns(res.campaigns || []);
            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadLogs = useCallback(async () => {
        try {
            setLoading(true);
            const res = await fetcher('/email/logs?days=30');
            setLogs(res.logs || []);
            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (tab === 'overview') loadOverview();
        else if (tab === 'contacts') loadContacts();
        else if (tab === 'intelligence') loadDomains();
        else if (tab === 'campaigns') loadCampaigns();
        else if (tab === 'logs') loadLogs();
    }, [tab, loadOverview, loadContacts, loadDomains, loadCampaigns, loadLogs]);

    // Reload contacts when filters change
    useEffect(() => {
        if (tab === 'contacts') loadContacts();
    }, [page, sourceFilter, searchQuery, companyFilter]);

    /* ── Actions ──────────────────────────────────────────────────────── */
    const handleGuess = async () => {
        if (!guessFirst || !guessLast || !guessCompany) return;
        setGuessing(true);
        try {
            const res = await fetcher('/intelligence/guess', {
                method: 'POST',
                body: JSON.stringify({
                    first_name: guessFirst,
                    last_name: guessLast,
                    company: guessCompany,
                }),
            });
            setGuessResults(res.guesses || []);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setGuessing(false);
        }
    };

    const handleExport = () => {
        window.open(`${BASE}/contacts/export`, '_blank');
    };

    const handleImportIntelligence = async () => {
        try {
            setLoading(true);
            const res = await fetcher('/intelligence/import', { method: 'POST' });
            alert(`Imported: ${res.imported}, Skipped: ${res.skipped}, Upgraded: ${res.upgraded}`);
            loadOverview();
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    /* ═══════════════════════════════════════════════════════════════════
       Render
       ═══════════════════════════════════════════════════════════════════ */
    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-1">📧 Email Intelligence & Campaigns</h1>
                        <p className="text-slate-400">
                            {analytics ? `${analytics.total_contacts.toLocaleString()} contacts` : 'Loading...'} · Pattern guessing · SendGrid / Klaviyo / Resend
                        </p>
                    </div>
                    <button
                        onClick={() => {
                            if (tab === 'overview') loadOverview();
                            else if (tab === 'contacts') loadContacts();
                            else if (tab === 'intelligence') loadDomains();
                            else if (tab === 'campaigns') loadCampaigns();
                            else if (tab === 'logs') loadLogs();
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 text-sm transition"
                    >
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-700 gap-1 overflow-x-auto">
                    <TabBtn active={tab === 'overview'} label="Overview" onClick={() => setTab('overview')} icon={BarChart3} />
                    <TabBtn active={tab === 'contacts'} label="Contacts" onClick={() => setTab('contacts')} icon={Users} />
                    <TabBtn active={tab === 'intelligence'} label="Intelligence" onClick={() => setTab('intelligence')} icon={Brain} />
                    <TabBtn active={tab === 'campaigns'} label="Campaigns" onClick={() => setTab('campaigns')} icon={Send} />
                    <TabBtn active={tab === 'logs'} label="Send Logs" onClick={() => setTab('logs')} icon={Mail} />
                </div>

                {/* Error */}
                {error && (
                    <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 flex items-center gap-2">
                        <AlertTriangle size={16} />
                        {error}
                        <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-white text-sm">×</button>
                    </div>
                )}

                {/* Loading */}
                {loading && (
                    <div className="text-center py-8 text-slate-400">Loading...</div>
                )}

                {/* ══════════  OVERVIEW  ══════════ */}
                {tab === 'overview' && !loading && analytics && (
                    <div className="space-y-6">
                        {/* Summary cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                            <SummaryCard label="Total Contacts" value={analytics.total_contacts} color="cyan" />
                            <SummaryCard label="Verified" value={analytics.verified_count} color="green" />
                            <SummaryCard label="Guessed" value={analytics.guessed_count} sub={`Avg conf: ${(analytics.avg_confidence * 100).toFixed(1)}%`} color="yellow" />
                            <SummaryCard label="Emails Sent" value={analytics.sends_total} color="blue" />
                            <SummaryCard label="Bounce Rate" value={`${(analytics.bounce_rate * 100).toFixed(1)}%`} color="red" />
                            <SummaryCard label="Open Rate" value={`${(analytics.open_rate * 100).toFixed(1)}%`} color="purple" />
                        </div>

                        {/* Provider Status */}
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Zap size={18} className="text-yellow-400" />
                                Provider Integrations
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {Object.entries(providers).map(([name, status]) => (
                                    <div key={name} className="bg-slate-800/50 rounded-lg p-4 flex items-center gap-3">
                                        {status.connected
                                            ? <CheckCircle size={20} className="text-green-400" />
                                            : <XCircle size={20} className="text-red-400" />
                                        }
                                        <div>
                                            <div className="text-white font-medium capitalize">{name}</div>
                                            <div className={`text-xs ${status.connected ? 'text-green-400' : 'text-red-400'}`}>
                                                {status.connected ? 'Connected' : (status.error || 'Not configured')}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Top Domains + Companies side-by-side */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                                <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Top Domains</h3>
                                {analytics.top_domains.slice(0, 10).map((d, i) => (
                                    <div key={d.domain} className="flex items-center justify-between py-1.5 border-b border-slate-800 last:border-0">
                                        <span className="text-slate-300 text-sm">{i + 1}. {d.domain}</span>
                                        <span className="text-cyan-400 text-sm font-mono">{d.count}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                                <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Top Companies</h3>
                                {analytics.top_companies.slice(0, 10).map((c, i) => (
                                    <div key={c.company} className="flex items-center justify-between py-1.5 border-b border-slate-800 last:border-0">
                                        <span className="text-slate-300 text-sm">{i + 1}. {c.company}</span>
                                        <span className="text-cyan-400 text-sm font-mono">{c.count}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Conversion Funnel */}
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                                <Target size={16} className="text-purple-400" />
                                Conversion Funnel
                            </h3>
                            <div className="flex gap-4 items-end h-32">
                                {['none', 'freemium', 'trial', 'paid', 'churned'].map(stage => {
                                    const count = analytics.conversion_funnel?.[stage] || 0;
                                    const max = Math.max(...Object.values(analytics.conversion_funnel || { x: 1 }));
                                    const pct = max > 0 ? (count / max) * 100 : 0;
                                    const colors: Record<string, string> = {
                                        none: 'bg-slate-600', freemium: 'bg-blue-500',
                                        trial: 'bg-cyan-500', paid: 'bg-green-500', churned: 'bg-red-500',
                                    };
                                    return (
                                        <div key={stage} className="flex-1 flex flex-col items-center gap-1">
                                            <span className="text-white text-xs font-mono">{count}</span>
                                            <div className={`w-full rounded-t ${colors[stage] || 'bg-slate-600'}`} style={{ height: `${Math.max(pct, 4)}%` }} />
                                            <span className="text-slate-400 text-xs capitalize">{stage}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {/* ══════════  CONTACTS  ══════════ */}
                {tab === 'contacts' && !loading && (
                    <div className="space-y-4">
                        {/* Filters */}
                        <div className="flex flex-wrap gap-3 items-center">
                            <div className="relative flex-1 min-w-[200px]">
                                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                                <input
                                    value={searchQuery}
                                    onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
                                    placeholder="Search name, email, company..."
                                    className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                                />
                            </div>
                            <input
                                value={companyFilter}
                                onChange={e => { setCompanyFilter(e.target.value); setPage(1); }}
                                placeholder="Company filter"
                                className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-40"
                            />
                            {[null, 'verified', 'guessed'].map(f => (
                                <button
                                    key={f || 'all'}
                                    onClick={() => { setSourceFilter(f); setPage(1); }}
                                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition
                                        ${sourceFilter === f ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                                >
                                    {f === null ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                                </button>
                            ))}
                            <button onClick={handleExport} className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-xs hover:bg-slate-700">
                                <Download size={12} /> Export CSV
                            </button>
                        </div>

                        {/* Table */}
                        <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-slate-800/60 text-slate-400 text-xs uppercase tracking-wider">
                                        <th className="px-4 py-3 text-left">Name</th>
                                        <th className="px-4 py-3 text-left">Email</th>
                                        <th className="px-4 py-3 text-left">Company</th>
                                        <th className="px-4 py-3 text-left">Domain</th>
                                        <th className="px-4 py-3 text-center">Type</th>
                                        <th className="px-4 py-3 text-center">Confidence</th>
                                        <th className="px-4 py-3 text-left">Pattern</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {contacts.length === 0 ? (
                                        <tr><td colSpan={7} className="text-center py-8 text-slate-500">No contacts found</td></tr>
                                    ) : contacts.map(c => (
                                        <tr key={c.id} className="border-t border-slate-800 hover:bg-slate-800/40 transition">
                                            <td className="px-4 py-2.5 text-white">
                                                {c.first_name} {c.last_name}
                                            </td>
                                            <td className="px-4 py-2.5 text-cyan-300 font-mono text-xs">{c.email}</td>
                                            <td className="px-4 py-2.5 text-slate-300">{c.company || '—'}</td>
                                            <td className="px-4 py-2.5 text-slate-400 text-xs font-mono">{c.domain || '—'}</td>
                                            <td className="px-4 py-2.5 text-center">
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                                                    ${c.source_type === 'verified' ? 'bg-green-900/40 text-green-400 border border-green-700/40' : 'bg-yellow-900/40 text-yellow-400 border border-yellow-700/40'}`}>
                                                    {c.source_type}
                                                </span>
                                            </td>
                                            <td className="px-4 py-2.5 text-center">
                                                <span className={`font-mono text-xs ${c.confidence >= 0.8 ? 'text-green-400' : c.confidence >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>
                                                    {(c.confidence * 100).toFixed(0)}%
                                                </span>
                                            </td>
                                            <td className="px-4 py-2.5 text-slate-400 text-xs">{c.pattern_used || '—'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        <div className="flex items-center justify-between text-slate-400 text-sm">
                            <span>{contactsMeta.total.toLocaleString()} contacts · Page {contactsMeta.page} of {contactsMeta.pages}</span>
                            <div className="flex gap-2">
                                <button
                                    disabled={page <= 1}
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    title="Previous page"
                                    className="px-3 py-1 bg-slate-800 rounded disabled:opacity-30 hover:bg-slate-700 transition"
                                >
                                    <ChevronLeft size={14} />
                                </button>
                                <button
                                    disabled={page >= contactsMeta.pages}
                                    onClick={() => setPage(p => p + 1)}
                                    title="Next page"
                                    className="px-3 py-1 bg-slate-800 rounded disabled:opacity-30 hover:bg-slate-700 transition"
                                >
                                    <ChevronRight size={14} />
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* ══════════  INTELLIGENCE  ══════════ */}
                {tab === 'intelligence' && !loading && (
                    <div className="space-y-6">
                        {/* Guess form */}
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Brain size={18} className="text-purple-400" />
                                Email Pattern Guesser
                            </h3>
                            <div className="flex flex-wrap gap-3 items-end">
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">First Name</label>
                                    <input value={guessFirst} onChange={e => setGuessFirst(e.target.value)} placeholder="e.g. Tony"
                                        className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm w-40 focus:outline-none focus:border-purple-500" />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">Last Name</label>
                                    <input value={guessLast} onChange={e => setGuessLast(e.target.value)} placeholder="e.g. Ryan"
                                        className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm w-40 focus:outline-none focus:border-purple-500" />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">Company</label>
                                    <input value={guessCompany} onChange={e => setGuessCompany(e.target.value)} placeholder="e.g. Amgen"
                                        className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm w-48 focus:outline-none focus:border-purple-500" />
                                </div>
                                <button
                                    onClick={handleGuess}
                                    disabled={guessing || !guessFirst || !guessLast || !guessCompany}
                                    className="px-5 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white rounded-lg text-sm transition flex items-center gap-2"
                                >
                                    <Brain size={14} />
                                    {guessing ? 'Guessing...' : 'Guess Email'}
                                </button>
                            </div>

                            {/* Guess results */}
                            {guessResults.length > 0 && (
                                <div className="mt-4 bg-slate-800/50 rounded-lg p-4">
                                    <h4 className="text-sm text-slate-300 font-medium mb-2">
                                        {guessResults.length} possible email{guessResults.length !== 1 && 's'} generated:
                                    </h4>
                                    <div className="space-y-1">
                                        {guessResults.map((g: any, i: number) => (
                                            <div key={i} className="flex items-center gap-3 py-1">
                                                <span className="text-cyan-300 font-mono text-sm flex-1">{g.email}</span>
                                                <span className="text-xs text-slate-400">{g.pattern}</span>
                                                <span className={`text-xs font-mono ${g.confidence >= 0.8 ? 'text-green-400' : g.confidence >= 0.5 ? 'text-yellow-400' : 'text-slate-500'}`}>
                                                    {(g.confidence * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Actions */}
                        <div className="flex gap-3">
                            <button
                                onClick={handleImportIntelligence}
                                className="flex items-center gap-2 px-4 py-2 bg-green-700 hover:bg-green-600 text-white rounded-lg text-sm transition"
                            >
                                <Upload size={14} />
                                Import Verified from Intelligence
                            </button>
                        </div>

                        {/* Domain patterns */}
                        {domainStats && (
                            <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                                <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-2">
                                    <Globe size={14} className="text-cyan-400" />
                                    Corporate Domain Patterns
                                </h3>
                                <p className="text-xs text-slate-500 mb-4">
                                    {domainStats.total_domains} domains · {domainStats.corporate_contacts.toLocaleString()} corporate contacts · {domainStats.total_verified_contacts.toLocaleString()} total verified
                                </p>
                                <div className="overflow-hidden rounded-lg">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="bg-slate-800/60 text-slate-400 text-xs uppercase tracking-wider">
                                                <th className="px-4 py-2 text-left">Domain</th>
                                                <th className="px-4 py-2 text-left">Company</th>
                                                <th className="px-4 py-2 text-center">Emails</th>
                                                <th className="px-4 py-2 text-center">Primary Pattern</th>
                                                <th className="px-4 py-2 text-left">All Patterns</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {domainStats.domains.slice(0, 30).map(d => (
                                                <tr key={d.domain} className="border-t border-slate-800 hover:bg-slate-800/40 transition">
                                                    <td className="px-4 py-2 text-cyan-300 font-mono text-xs">{d.domain}</td>
                                                    <td className="px-4 py-2 text-white">{d.company || '—'}</td>
                                                    <td className="px-4 py-2 text-center text-slate-300">{d.total_emails}</td>
                                                    <td className="px-4 py-2 text-center">
                                                        <span className="px-2 py-0.5 bg-purple-900/40 text-purple-300 border border-purple-700/40 rounded-full text-xs">
                                                            {d.primary_pattern}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2 text-slate-400 text-xs">
                                                        {Object.entries(d.patterns).map(([p, n]) => `${p}(${n})`).join(', ')}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ══════════  CAMPAIGNS  ══════════ */}
                {tab === 'campaigns' && !loading && (
                    <div className="space-y-4">
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Send size={18} className="text-blue-400" />
                                Email Campaigns
                            </h3>
                            {campaigns.length === 0 ? (
                                <div className="text-center py-12 text-slate-500">
                                    <Send size={32} className="mx-auto mb-3 opacity-30" />
                                    <p>No campaigns yet. Create one to get started.</p>
                                </div>
                            ) : (
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="bg-slate-800/60 text-slate-400 text-xs uppercase tracking-wider">
                                            <th className="px-4 py-2 text-left">Name</th>
                                            <th className="px-4 py-2 text-left">Subject</th>
                                            <th className="px-4 py-2 text-center">Provider</th>
                                            <th className="px-4 py-2 text-center">Status</th>
                                            <th className="px-4 py-2 text-center">Recipients</th>
                                            <th className="px-4 py-2 text-left">Created</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {campaigns.map((c: any) => (
                                            <tr key={c.id} className="border-t border-slate-800 hover:bg-slate-800/40">
                                                <td className="px-4 py-2 text-white">{c.name}</td>
                                                <td className="px-4 py-2 text-slate-300">{c.subject}</td>
                                                <td className="px-4 py-2 text-center text-slate-400 text-xs">{c.provider}</td>
                                                <td className="px-4 py-2 text-center">
                                                    <span className={`px-2 py-0.5 rounded-full text-xs
                                                        ${c.status === 'sent' ? 'bg-green-900/40 text-green-400' : 'bg-slate-700 text-slate-300'}`}>
                                                        {c.status}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-2 text-center text-slate-300">{c.recipients?.length || 0}</td>
                                                <td className="px-4 py-2 text-slate-400 text-xs">{c.created_at?.slice(0, 16)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                )}

                {/* ══════════  LOGS  ══════════ */}
                {tab === 'logs' && !loading && (
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Mail size={18} className="text-slate-400" />
                            Send Logs (Last 30 Days)
                        </h3>
                        {logs.length === 0 ? (
                            <div className="text-center py-12 text-slate-500">
                                <Mail size={32} className="mx-auto mb-3 opacity-30" />
                                <p>No send logs yet.</p>
                            </div>
                        ) : (
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-slate-800/60 text-slate-400 text-xs uppercase tracking-wider">
                                        <th className="px-4 py-2 text-left">Recipient</th>
                                        <th className="px-4 py-2 text-left">Subject</th>
                                        <th className="px-4 py-2 text-center">Provider</th>
                                        <th className="px-4 py-2 text-center">Status</th>
                                        <th className="px-4 py-2 text-left">Timestamp</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.map((l: any, i: number) => (
                                        <tr key={i} className="border-t border-slate-800 hover:bg-slate-800/40">
                                            <td className="px-4 py-2 text-cyan-300 font-mono text-xs">{l.to}</td>
                                            <td className="px-4 py-2 text-slate-300">{l.subject}</td>
                                            <td className="px-4 py-2 text-center text-slate-400 text-xs">{l.provider}</td>
                                            <td className="px-4 py-2 text-center">
                                                {l.success
                                                    ? <CheckCircle size={14} className="text-green-400 mx-auto" />
                                                    : <XCircle size={14} className="text-red-400 mx-auto" />
                                                }
                                            </td>
                                            <td className="px-4 py-2 text-slate-400 text-xs">{l.timestamp?.slice(0, 19)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </div>
        </AdminLayout>
    );
}

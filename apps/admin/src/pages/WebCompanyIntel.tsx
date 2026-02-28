import React, { useEffect, useMemo, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Building2, Search, Loader2, RefreshCw, Wand2 } from 'lucide-react';

interface CompanyRegistrySummary {
    total_companies: number;
    total_seen_events: number;
}

interface CompanyRegistryItem {
    company: string;
    first_seen: string;
    last_seen: string;
    seen_count: number;
    sources: string[];
    users: string[];
}

interface CompanyRegistryResponse {
    summary: CompanyRegistrySummary;
    count: number;
    items: CompanyRegistryItem[];
}

interface CompanyExtractSummary {
    companies_found: number;
    companies_added: number;
    companies_updated: number;
}

interface CompanyExtractResponse {
    status: string;
    summary: CompanyExtractSummary;
    registry: CompanyRegistrySummary;
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
    const response = await fetch(url, {
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...(init?.headers ?? {}),
        },
        ...init,
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `HTTP ${response.status}`);
    }

    return response.json() as Promise<T>;
}

export default function WebCompanyIntel() {
    const [searchTerm, setSearchTerm] = useState('');
    const [registry, setRegistry] = useState<CompanyRegistryResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>('');
    const [extractText, setExtractText] = useState<string>('');
    const [extracting, setExtracting] = useState<boolean>(false);
    const [extractResult, setExtractResult] = useState<CompanyExtractSummary | null>(null);

    const loadRegistry = async (query = '') => {
        try {
            setLoading(true);
            setError('');
            const params = new URLSearchParams();
            params.set('limit', '200');
            if (query.trim()) {
                params.set('q', query.trim());
            }
            const data = await fetchJson<CompanyRegistryResponse>(`/api/intelligence/v1/company/registry?${params.toString()}`);
            setRegistry(data);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : 'Failed to load company registry');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadRegistry();
    }, []);

    const filteredItems = useMemo(() => {
        const items = registry?.items ?? [];
        const q = searchTerm.trim().toLowerCase();
        if (!q) {
            return items;
        }
        return items.filter((row) => row.company.toLowerCase().includes(q));
    }, [registry, searchTerm]);

    const onRunExtract = async () => {
        if (!extractText.trim()) {
            setError('Paste resume or company text before running extraction.');
            return;
        }
        try {
            setExtracting(true);
            setError('');
            setExtractResult(null);

            const data = await fetchJson<CompanyExtractResponse>('/api/intelligence/v1/company/extract', {
                method: 'POST',
                body: JSON.stringify({
                    text: extractText,
                    source: 'admin_company_intel_panel',
                }),
            });

            setExtractResult(data.summary);
            await loadRegistry(searchTerm);
        } catch (extractError) {
            setError(extractError instanceof Error ? extractError.message : 'Extraction failed');
        } finally {
            setExtracting(false);
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🏢 Admin Company Intel</h1>
                    <p className="text-slate-400">Registry view and manual extraction workflow</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <div className="text-xs text-slate-400">Total Companies</div>
                        <div className="text-2xl font-bold text-white mt-1">{registry?.summary.total_companies ?? 0}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <div className="text-xs text-slate-400">Total Seen Events</div>
                        <div className="text-2xl font-bold text-white mt-1">{registry?.summary.total_seen_events ?? 0}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                        <div className="text-xs text-slate-400">Rows (Current View)</div>
                        <div className="text-2xl font-bold text-white mt-1">{filteredItems.length}</div>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                    <div className="flex items-center gap-3">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search by company name..."
                                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500"
                            />
                        </div>
                        <button
                            type="button"
                            onClick={() => loadRegistry(searchTerm)}
                            className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-white"
                        >
                            <RefreshCw size={16} />
                            Refresh
                        </button>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-2 text-white font-semibold">
                        <Wand2 size={16} className="text-amber-400" />
                        Trigger Company Extraction
                    </div>
                    <textarea
                        value={extractText}
                        onChange={(e) => setExtractText(e.target.value)}
                        placeholder="Paste resume text or notes to extract company names..."
                        className="w-full min-h-[120px] p-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500"
                    />
                    <div className="flex items-center gap-3">
                        <button
                            type="button"
                            disabled={extracting}
                            onClick={onRunExtract}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed rounded-lg text-white"
                        >
                            {extracting ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
                            Run Extract
                        </button>
                        {extractResult && (
                            <div className="text-sm text-slate-300">
                                Found {extractResult.companies_found} • Added {extractResult.companies_added} • Updated {extractResult.companies_updated}
                            </div>
                        )}
                    </div>
                </div>

                {error && (
                    <div className="bg-red-950 border border-red-700 rounded-lg p-3 text-red-200 text-sm">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 gap-4">
                    {loading ? (
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 flex items-center gap-3 text-slate-300">
                            <Loader2 size={18} className="animate-spin" />
                            Loading company registry...
                        </div>
                    ) : (
                        filteredItems.map((company) => (
                            <div key={`${company.company}-${company.last_seen}`} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                                <div className="flex items-start justify-between gap-4">
                                    <div className="min-w-0">
                                        <h3 className="text-xl font-bold text-white mb-1 break-words">{company.company}</h3>
                                        <div className="text-sm text-slate-400">Seen {company.seen_count} times</div>
                                    </div>
                                    <div className="text-right text-xs text-slate-400 whitespace-nowrap">
                                        <div>First: {company.first_seen || 'n/a'}</div>
                                        <div>Last: {company.last_seen || 'n/a'}</div>
                                    </div>
                                </div>
                                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                                    <span className="text-slate-400">Sources:</span>
                                    {(company.sources || []).length > 0 ? (
                                        company.sources.map((source) => (
                                            <span key={source} className="px-2 py-1 rounded bg-slate-800 text-slate-200 border border-slate-700">
                                                {source}
                                            </span>
                                        ))
                                    ) : (
                                        <span className="text-slate-500">none</span>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                    {!loading && filteredItems.length === 0 && (
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 text-slate-400">
                            No companies found for the current filter.
                        </div>
                    )}
                </div>
            </div>
        </AdminLayout>
    );
}

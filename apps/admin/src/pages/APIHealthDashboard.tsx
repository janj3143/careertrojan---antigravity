import React, { useState, useCallback } from 'react';
import AdminLayout from '../components/AdminLayout';
import {
  Activity, CheckCircle, XCircle, AlertTriangle, Clock,
  Play, RefreshCw, ChevronDown, ChevronRight, Search, Filter,
  Zap, Shield, Server,
} from 'lucide-react';

/* ─────────────────── Types ─────────────────── */
interface EndpointResult {
  path: string;
  status_code: number;
  status: string;   // pass | auth-required | missing-params | not-found | error | exception
  response_time_ms: number;
  excerpt: string;
}

interface RouteInfo {
  method: string;
  path: string;
  name: string;
  tags: string[];
}

interface RunAllResponse {
  run_at: string;
  total_endpoints: number;
  probed: number;
  passed: number;
  failed: number;
  skipped: number;
  pass_rate: number;
  avg_response_ms: number;
  results: EndpointResult[];
  all_endpoints: RouteInfo[];
}

/* ─────────────── Status helpers ────────────── */
const statusIcon = (s: string) => {
  switch (s) {
    case 'pass': return <CheckCircle className="text-green-400" size={16} />;
    case 'auth-required': return <Shield className="text-blue-400" size={16} />;
    case 'missing-params': return <AlertTriangle className="text-amber-400" size={16} />;
    case 'not-found': return <XCircle className="text-red-400" size={16} />;
    case 'error': return <XCircle className="text-red-500" size={16} />;
    case 'exception': return <XCircle className="text-rose-600" size={16} />;
    default: return <AlertTriangle className="text-slate-400" size={16} />;
  }
};

const statusBadge = (s: string) => {
  const map: Record<string, string> = {
    pass: 'bg-green-900/40 text-green-400 border-green-700',
    'auth-required': 'bg-blue-900/40 text-blue-400 border-blue-700',
    'missing-params': 'bg-amber-900/40 text-amber-400 border-amber-700',
    'not-found': 'bg-red-900/40 text-red-400 border-red-700',
    error: 'bg-red-900/40 text-red-500 border-red-700',
    exception: 'bg-rose-900/40 text-rose-500 border-rose-700',
  };
  return map[s] || 'bg-slate-800 text-slate-400 border-slate-600';
};

const methodColor = (m: string) => {
  const map: Record<string, string> = {
    GET: 'text-green-400', POST: 'text-blue-400', PUT: 'text-amber-400',
    DELETE: 'text-red-400', PATCH: 'text-purple-400',
  };
  return map[m] || 'text-slate-400';
};

/* ─────────────────── Component ─────────────── */
export default function APIHealthDashboard() {
  const [data, setData] = useState<RunAllResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'pass' | 'fail' | 'slow'>('all');
  const [search, setSearch] = useState('');
  const [expandedTags, setExpandedTags] = useState<Set<string>>(new Set());
  const [tab, setTab] = useState<'results' | 'registry'>('results');
  const [error, setError] = useState<string | null>(null);

  /* ── Run All ── */
  const runAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/admin/v1/api-health/run-all', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: RunAllResponse = await res.json();
      setData(json);
      setTab('results');
    } catch (e: any) {
      setError(e.message || 'Failed to run health checks');
    } finally {
      setLoading(false);
    }
  }, []);

  /* ── Load last summary ── */
  const loadSummary = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/v1/api-health/summary');
      if (!res.ok) return;
      const json = await res.json();
      if (json.results) setData(json as RunAllResponse);
    } catch { /* ignore */ }
  }, []);

  React.useEffect(() => { loadSummary(); }, [loadSummary]);

  /* ── Filtered results ── */
  const filtered = (data?.results || []).filter(r => {
    if (filter === 'pass') return ['pass', 'auth-required', 'missing-params'].includes(r.status);
    if (filter === 'fail') return !['pass', 'auth-required', 'missing-params'].includes(r.status);
    if (filter === 'slow') return r.response_time_ms > 500;
    return true;
  }).filter(r => !search || r.path.toLowerCase().includes(search.toLowerCase()));

  /* ── Group by tag ── */
  const tagGroups: Record<string, RouteInfo[]> = {};
  (data?.all_endpoints || []).forEach(e => {
    const tag = e.tags[0] || 'untagged';
    (tagGroups[tag] ??= []).push(e);
  });

  const toggleTag = (tag: string) => {
    setExpandedTags(prev => {
      const next = new Set(prev);
      next.has(tag) ? next.delete(tag) : next.add(tag);
      return next;
    });
  };

  return (
    <AdminLayout>
      <div className="max-w-[1400px] mx-auto space-y-6">
        {/* ── Header ── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-1">⚡ API Health Dashboard</h1>
            <p className="text-slate-400">
              Probe all {data?.total_endpoints ?? '…'} endpoints — full trace, status &amp; timing
            </p>
          </div>
          <button
            onClick={runAll}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-3 bg-green-600 hover:bg-green-500 disabled:bg-slate-700 text-white font-bold rounded-lg transition-colors shadow-lg"
          >
            {loading
              ? <><RefreshCw className="animate-spin" size={18} /> Running…</>
              : <><Play size={18} /> Run All</>}
          </button>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* ── Summary Cards ── */}
        {data && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            <SummaryCard label="Total" value={data.total_endpoints} icon={<Server size={18} />} color="text-slate-300" />
            <SummaryCard label="Probed" value={data.probed} icon={<Zap size={18} />} color="text-cyan-400" />
            <SummaryCard label="Passed" value={data.passed} icon={<CheckCircle size={18} />} color="text-green-400" />
            <SummaryCard label="Failed" value={data.failed} icon={<XCircle size={18} />} color={data.failed > 0 ? 'text-red-400' : 'text-green-400'} />
            <SummaryCard label="Skipped" value={data.skipped} icon={<AlertTriangle size={18} />} color="text-slate-400" />
            <SummaryCard label="Pass Rate" value={`${data.pass_rate}%`} icon={<Activity size={18} />} color={data.pass_rate >= 90 ? 'text-green-400' : data.pass_rate >= 70 ? 'text-amber-400' : 'text-red-400'} />
            <SummaryCard label="Avg MS" value={`${data.avg_response_ms}`} icon={<Clock size={18} />} color={data.avg_response_ms < 200 ? 'text-green-400' : 'text-amber-400'} />
          </div>
        )}

        {data && (
          <p className="text-xs text-slate-500">
            Last run: {new Date(data.run_at).toLocaleString()}
          </p>
        )}

        {/* ── Tabs ── */}
        {data && (
          <div className="flex gap-4 border-b border-slate-700 pb-1">
            <TabBtn active={tab === 'results'} onClick={() => setTab('results')}>
              Probe Results ({data.results.length})
            </TabBtn>
            <TabBtn active={tab === 'registry'} onClick={() => setTab('registry')}>
              Full Registry ({data.all_endpoints.length})
            </TabBtn>
          </div>
        )}

        {/* ── Results Tab ── */}
        {data && tab === 'results' && (
          <>
            {/* Filter bar */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500"
                  placeholder="Search endpoints…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <div className="flex gap-1">
                {(['all', 'pass', 'fail', 'slow'] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                      filter === f
                        ? 'bg-cyan-600 text-white'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    {f === 'all' ? `All (${data.results.length})`
                      : f === 'pass' ? `Pass (${data.passed})`
                      : f === 'fail' ? `Fail (${data.failed})`
                      : `Slow (${data.results.filter(r => r.response_time_ms > 500).length})`}
                  </button>
                ))}
              </div>
            </div>

            {/* Results table */}
            <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-800/60 text-slate-400 text-left">
                    <th className="px-4 py-2.5 w-8"></th>
                    <th className="px-4 py-2.5">Endpoint</th>
                    <th className="px-4 py-2.5 w-28">Status</th>
                    <th className="px-4 py-2.5 w-20 text-right">Code</th>
                    <th className="px-4 py-2.5 w-24 text-right">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r, i) => (
                    <tr key={i} className="border-t border-slate-800 hover:bg-slate-800/40">
                      <td className="px-4 py-2">{statusIcon(r.status)}</td>
                      <td className="px-4 py-2 font-mono text-xs text-white">{r.path}</td>
                      <td className="px-4 py-2">
                        <span className={`inline-block px-2 py-0.5 rounded border text-xs font-medium ${statusBadge(r.status)}`}>
                          {r.status}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-xs text-slate-300">{r.status_code}</td>
                      <td className={`px-4 py-2 text-right font-mono text-xs ${r.response_time_ms > 500 ? 'text-amber-400' : 'text-slate-300'}`}>
                        {r.response_time_ms}ms
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filtered.length === 0 && (
                <div className="text-center py-8 text-slate-500">No matching endpoints</div>
              )}
            </div>
          </>
        )}

        {/* ── Registry Tab ── */}
        {data && tab === 'registry' && (
          <div className="space-y-2">
            {Object.entries(tagGroups).sort().map(([tag, routes]) => (
              <div key={tag} className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                <button
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-800/50 transition-colors"
                  onClick={() => toggleTag(tag)}
                >
                  <span className="font-medium text-white flex items-center gap-2">
                    {expandedTags.has(tag) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    {tag}
                    <span className="text-xs text-slate-500 font-normal">({routes.length} endpoints)</span>
                  </span>
                </button>
                {expandedTags.has(tag) && (
                  <div className="border-t border-slate-800">
                    {routes.map((r, i) => (
                      <div key={i} className="flex items-center gap-3 px-6 py-2 border-b border-slate-800/50 last:border-0">
                        <span className={`font-mono text-xs font-bold w-14 ${methodColor(r.method)}`}>{r.method}</span>
                        <span className="font-mono text-xs text-slate-300 flex-1">{r.path}</span>
                        <span className="text-xs text-slate-500">{r.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ── Empty state ── */}
        {!data && !loading && !error && (
          <div className="text-center py-20 space-y-4">
            <Activity className="mx-auto text-slate-600" size={48} />
            <p className="text-slate-400 text-lg">No health check data yet</p>
            <p className="text-slate-500 text-sm">Click <strong>Run All</strong> to probe every endpoint</p>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

/* ─────────────── Sub-components ────────────── */
function SummaryCard({ label, value, icon, color }: { label: string; value: string | number; icon: React.ReactNode; color: string }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 text-center">
      <div className={`flex items-center justify-center gap-1 mb-1 ${color}`}>{icon}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? 'text-cyan-400 border-b-2 border-cyan-400'
          : 'text-slate-400 hover:text-white'
      }`}
    >
      {children}
    </button>
  );
}

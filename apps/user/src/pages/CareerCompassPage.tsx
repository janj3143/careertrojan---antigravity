import React, { useState, useEffect, useCallback } from 'react';
import { Compass, Map, Target, TrendingUp, Users, AlertTriangle, Bookmark, ChevronRight, Info } from 'lucide-react';
import { API } from '../lib/apiConfig';

/* ── Types ─────────────────────────────────────────────────────── */
interface CareerMapNode {
    cluster_id: string;
    label: string;
    route_type?: string;
    x: number;
    y: number;
}
interface SpiderOverlay {
    user_vector: Record<string, number>;
    target_vector: Record<string, number>;
    gap_vector: Record<string, number>;
    strengths: string[];
    gaps: string[];
}
interface RunwayStep {
    step_number: number;
    title: string;
    detail: string;
}

type Panel = 'map' | 'cluster' | 'spider' | 'routes' | 'culdesac' | 'runway' | 'mentors' | 'market';

const ROUTE_COLOURS: Record<string, string> = {
    natural_next_step: 'bg-emerald-500',
    strategic_stretch: 'bg-amber-500',
    too_far_for_now: 'bg-red-400',
};

const HELP_TEXT: Record<Panel, string> = {
    map: 'Your career map shows all peer clusters positioned by similarity. Closer nodes = more natural transitions.',
    cluster: 'Deep dive into a single cluster — who works there, typical titles, and the skill profile.',
    spider: 'Overlay your 10-axis skill vector against the cluster target to see strengths and gaps.',
    routes: 'Routes classify each cluster: Natural Next Step, Strategic Stretch, or Too Far For Now.',
    culdesac: 'Cul-de-sac check warns if a cluster has limited onward mobility.',
    runway: 'Runway gives you a concrete step-by-step plan to close the gap to your target cluster.',
    mentors: 'Mentor matching finds people whose strengths complement your gaps.',
    market: 'Market signals show live demand metrics for your chosen cluster and region.',
};

/* ── API helpers ────────────────────────────────────────────────── */
function authHeaders() {
    const token = localStorage.getItem('token');
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}
async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
    const res = await fetch(url, { ...init, headers: { ...authHeaders(), ...init?.headers } });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return res.json();
}

/* ── Main Page ──────────────────────────────────────────────────── */
export default function CareerCompassPage() {
    const [panel, setPanel] = useState<Panel>('map');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Data slices
    const [mapNodes, setMapNodes] = useState<CareerMapNode[]>([]);
    const [selectedCluster, setSelectedCluster] = useState<string | null>(null);
    const [clusterProfile, setClusterProfile] = useState<any>(null);
    const [spider, setSpider] = useState<SpiderOverlay | null>(null);
    const [routes, setRoutes] = useState<any>(null);
    const [culdesac, setCuldesac] = useState<any>(null);
    const [runway, setRunway] = useState<RunwayStep[]>([]);
    const [mentors, setMentors] = useState<any[]>([]);
    const [market, setMarket] = useState<any>(null);

    // User context
    const userId = 'current'; // resolved server-side from token
    const resumeId = 'latest';

    /* ── Load career map on mount ─────────────────────────── */
    useEffect(() => {
        loadMap();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const loadMap = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await apiFetch<any>(`${API.careerCompass}/map?user_id=${userId}&resume_id=${resumeId}`);
            setMapNodes(data.nodes ?? []);
            if (data.status !== 'ok') setError(data.message ?? 'Map data unavailable.');
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [userId, resumeId]);

    const loadCluster = useCallback(async (clusterId: string) => {
        setSelectedCluster(clusterId);
        setPanel('cluster');
        setLoading(true);
        try {
            const data = await apiFetch<any>(`${API.careerCompass}/cluster/${clusterId}`);
            setClusterProfile(data);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadSpider = useCallback(async () => {
        if (!selectedCluster) return;
        setPanel('spider');
        setLoading(true);
        try {
            const data = await apiFetch<any>(`${API.careerCompass}/spider-overlay`, {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, resume_id: resumeId, cluster_id: selectedCluster }),
            });
            setSpider(data);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [selectedCluster, userId, resumeId]);

    const loadRoutes = useCallback(async () => {
        setPanel('routes');
        setLoading(true);
        try {
            const data = await apiFetch<any>(`${API.careerCompass}/routes?user_id=${userId}&resume_id=${resumeId}`);
            setRoutes(data);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [userId, resumeId]);

    const loadCuldesac = useCallback(async () => {
        if (!selectedCluster) return;
        setPanel('culdesac');
        setLoading(true);
        try {
            const data = await apiFetch<any>(`${API.careerCompass}/culdesac-check`, {
                method: 'POST',
                body: JSON.stringify({ cluster_id: selectedCluster }),
            });
            setCuldesac(data);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [selectedCluster]);

    const loadRunway = useCallback(async () => {
        if (!selectedCluster) return;
        setPanel('runway');
        setLoading(true);
        try {
            const data = await apiFetch<any>(`${API.careerCompass}/runway`, {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, resume_id: resumeId, cluster_id: selectedCluster }),
            });
            setRunway(data.steps ?? []);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [selectedCluster, userId, resumeId]);

    const loadMentors = useCallback(async () => {
        if (!selectedCluster) return;
        setPanel('mentors');
        setLoading(true);
        try {
            const data = await apiFetch<any>(`${API.careerCompass}/mentor-match`, {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, resume_id: resumeId, cluster_id: selectedCluster }),
            });
            setMentors(data.mentors ?? []);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [selectedCluster, userId, resumeId]);

    const loadMarket = useCallback(async () => {
        if (!selectedCluster) return;
        setPanel('market');
        setLoading(true);
        try {
            const data = await apiFetch<any>(`${API.market}/signal`, {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, cluster_id: selectedCluster }),
            });
            setMarket(data);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [selectedCluster, userId]);

    const saveScenario = useCallback(async () => {
        if (!selectedCluster) return;
        try {
            await apiFetch<any>(`${API.careerCompass}/save-scenario`, {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, resume_id: resumeId, cluster_id: selectedCluster }),
            });
            alert('Scenario saved!');
        } catch (e: any) {
            setError(e.message);
        }
    }, [selectedCluster, userId, resumeId]);

    /* ── Render helpers ───────────────────────────────────── */
    const HelpBubble = ({ text }: { text: string }) => (
        <div className="group relative inline-block ml-2">
            <Info size={16} className="text-gray-400 hover:text-indigo-400 cursor-help" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-gray-800 text-gray-200 text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                {text}
            </div>
        </div>
    );

    const NavBtn = ({ p, icon, label }: { p: Panel; icon: React.ReactNode; label: string }) => (
        <button
            onClick={() => {
                if (p === 'map') { setPanel('map'); loadMap(); }
                else if (p === 'spider') loadSpider();
                else if (p === 'routes') loadRoutes();
                else if (p === 'culdesac') loadCuldesac();
                else if (p === 'runway') loadRunway();
                else if (p === 'mentors') loadMentors();
                else if (p === 'market') loadMarket();
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                panel === p ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
        >
            {icon} {label}
        </button>
    );

    return (
        <div className="min-h-screen bg-gray-950 text-white p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <Compass size={28} className="text-indigo-400" />
                <h1 className="text-2xl font-bold">🧭 Career Compass</h1>
                <HelpBubble text="Career Compass maps your career landscape, compares your skills against target clusters, and plans your runway." />
            </div>

            {/* Navigation */}
            <div className="flex flex-wrap gap-2">
                <NavBtn p="map" icon={<Map size={16} />} label="Career Map" />
                <NavBtn p="spider" icon={<Target size={16} />} label="Spider Overlay" />
                <NavBtn p="routes" icon={<ChevronRight size={16} />} label="Routes" />
                <NavBtn p="culdesac" icon={<AlertTriangle size={16} />} label="Cul-de-sac" />
                <NavBtn p="runway" icon={<TrendingUp size={16} />} label="Runway" />
                <NavBtn p="mentors" icon={<Users size={16} />} label="Mentors" />
                <NavBtn p="market" icon={<TrendingUp size={16} />} label="Market" />
                {selectedCluster && (
                    <button onClick={saveScenario} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-emerald-700 text-white hover:bg-emerald-600 transition">
                        <Bookmark size={16} /> Save Scenario
                    </button>
                )}
            </div>

            {/* Error banner */}
            {error && (
                <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-200 flex items-center gap-2">
                    <AlertTriangle size={18} /> {error}
                </div>
            )}

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-12">
                    <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                </div>
            )}

            {/* ── Panel: Map ──────────────────────────────── */}
            {!loading && panel === 'map' && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold">Career Map</h2>
                        <HelpBubble text={HELP_TEXT.map} />
                    </div>
                    {mapNodes.length === 0 ? (
                        <p className="text-gray-400">No cluster data available. Upload your CV and wait for processing.</p>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {mapNodes.map(n => (
                                <button
                                    key={n.cluster_id}
                                    onClick={() => loadCluster(n.cluster_id)}
                                    className={`p-4 rounded-xl border border-gray-700 bg-gray-900 hover:border-indigo-500 transition text-left`}
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium">{n.label}</span>
                                        {n.route_type && (
                                            <span className={`px-2 py-0.5 rounded text-xs text-white ${ROUTE_COLOURS[n.route_type] ?? 'bg-gray-600'}`}>
                                                {n.route_type.replace(/_/g, ' ')}
                                            </span>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* ── Panel: Cluster Profile ──────────────────── */}
            {!loading && panel === 'cluster' && clusterProfile && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold">{clusterProfile.title ?? clusterProfile.cluster_id}</h2>
                        <HelpBubble text={HELP_TEXT.cluster} />
                    </div>
                    {clusterProfile.summary && (
                        <div className="bg-gray-900 rounded-xl p-4 space-y-2">
                            {Object.entries(clusterProfile.summary).map(([k, v]) => (
                                <div key={k}><span className="text-gray-400 capitalize">{k}:</span> <span>{String(v)}</span></div>
                            ))}
                        </div>
                    )}
                    {clusterProfile.vector && (
                        <div className="bg-gray-900 rounded-xl p-4">
                            <h3 className="text-sm font-medium text-gray-400 mb-2">Cluster Vector</h3>
                            <div className="grid grid-cols-2 gap-2">
                                {Object.entries(clusterProfile.vector).map(([axis, val]) => (
                                    <div key={axis} className="flex items-center gap-2">
                                        <span className="text-xs text-gray-400 w-32 truncate">{axis}</span>
                                        <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                                            <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${(Number(val) * 100)}%` }} />
                                        </div>
                                        <span className="text-xs text-gray-500 w-8 text-right">{(Number(val) * 100).toFixed(0)}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    <div className="flex gap-2">
                        <button onClick={loadSpider} className="px-4 py-2 bg-indigo-600 rounded-lg text-sm hover:bg-indigo-500">Compare (Spider)</button>
                        <button onClick={loadCuldesac} className="px-4 py-2 bg-amber-700 rounded-lg text-sm hover:bg-amber-600">Cul-de-sac Check</button>
                        <button onClick={loadRunway} className="px-4 py-2 bg-emerald-700 rounded-lg text-sm hover:bg-emerald-600">Plan Runway</button>
                    </div>
                </div>
            )}

            {/* ── Panel: Spider Overlay ───────────────────── */}
            {!loading && panel === 'spider' && spider && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold">Spider Overlay — {selectedCluster}</h2>
                        <HelpBubble text={HELP_TEXT.spider} />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Vector bars */}
                        <div className="bg-gray-900 rounded-xl p-4">
                            <h3 className="text-sm font-medium text-gray-400 mb-3">Your Vector vs Target</h3>
                            {spider.user_vector && Object.keys(spider.user_vector).map(axis => (
                                <div key={axis} className="mb-2">
                                    <div className="text-xs text-gray-400 mb-1">{axis}</div>
                                    <div className="flex items-center gap-2">
                                        <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden relative">
                                            <div className="h-full bg-indigo-500 rounded-full absolute" style={{ width: `${(spider.user_vector[axis] ?? 0) * 100}%` }} />
                                        </div>
                                        <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                                            <div className="h-full bg-amber-500 rounded-full" style={{ width: `${(spider.target_vector?.[axis] ?? 0) * 100}%` }} />
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <div className="flex gap-4 mt-3 text-xs text-gray-400">
                                <span className="flex items-center gap-1"><span className="w-3 h-2 bg-indigo-500 rounded" /> You</span>
                                <span className="flex items-center gap-1"><span className="w-3 h-2 bg-amber-500 rounded" /> Target</span>
                            </div>
                        </div>
                        {/* Strengths / Gaps */}
                        <div className="space-y-4">
                            <div className="bg-gray-900 rounded-xl p-4">
                                <h3 className="text-sm font-medium text-emerald-400 mb-2">Strengths</h3>
                                {spider.strengths.length ? spider.strengths.map((s, i) => <div key={i} className="text-sm text-gray-300">✓ {s}</div>) : <p className="text-gray-500 text-sm">No clear strengths detected yet.</p>}
                            </div>
                            <div className="bg-gray-900 rounded-xl p-4">
                                <h3 className="text-sm font-medium text-red-400 mb-2">Gaps</h3>
                                {spider.gaps.length ? spider.gaps.map((g, i) => <div key={i} className="text-sm text-gray-300">✗ {g}</div>) : <p className="text-gray-500 text-sm">No major gaps detected.</p>}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Panel: Routes ───────────────────────────── */}
            {!loading && panel === 'routes' && routes && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold">Career Routes</h2>
                        <HelpBubble text={HELP_TEXT.routes} />
                    </div>
                    {['natural_next_steps', 'strategic_stretch', 'too_far_for_now'].map(bucket => (
                        <div key={bucket} className="bg-gray-900 rounded-xl p-4">
                            <h3 className="text-sm font-medium capitalize mb-2">{bucket.replace(/_/g, ' ')}</h3>
                            {(routes[bucket] ?? []).length === 0 ? (
                                <p className="text-gray-500 text-sm">None</p>
                            ) : (
                                <div className="flex flex-wrap gap-2">
                                    {routes[bucket].map((id: string) => (
                                        <button key={id} onClick={() => loadCluster(id)} className="px-3 py-1 bg-gray-800 rounded-lg text-sm hover:bg-gray-700">{id}</button>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* ── Panel: Cul-de-sac ──────────────────────── */}
            {!loading && panel === 'culdesac' && culdesac && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold">Cul-de-sac Check — {selectedCluster}</h2>
                        <HelpBubble text={HELP_TEXT.culdesac} />
                    </div>
                    <div className={`bg-gray-900 rounded-xl p-6 border-l-4 ${
                        culdesac.risk_level === 'high_mobility' ? 'border-emerald-500' :
                        culdesac.risk_level === 'moderate_mobility' ? 'border-amber-500' :
                        'border-red-500'
                    }`}>
                        <div className="text-lg font-semibold capitalize">{(culdesac.risk_level ?? '').replace(/_/g, ' ')}</div>
                        <ul className="mt-3 space-y-1">
                            {culdesac.reasons?.map((r: string, i: number) => <li key={i} className="text-sm text-gray-300">• {r}</li>)}
                        </ul>
                    </div>
                </div>
            )}

            {/* ── Panel: Runway ───────────────────────────── */}
            {!loading && panel === 'runway' && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold">Runway Plan — {selectedCluster}</h2>
                        <HelpBubble text={HELP_TEXT.runway} />
                    </div>
                    {runway.length === 0 ? (
                        <p className="text-gray-400">No runway steps available.</p>
                    ) : (
                        <div className="space-y-3">
                            {runway.map(step => (
                                <div key={step.step_number} className="bg-gray-900 rounded-xl p-4 flex items-start gap-4">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-sm font-bold">
                                        {step.step_number}
                                    </div>
                                    <div>
                                        <div className="font-medium">{step.title}</div>
                                        <p className="text-sm text-gray-400 mt-1">{step.detail}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* ── Panel: Mentors ──────────────────────────── */}
            {!loading && panel === 'mentors' && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold">Mentor Matches — {selectedCluster}</h2>
                        <HelpBubble text={HELP_TEXT.mentors} />
                    </div>
                    {mentors.length === 0 ? (
                        <p className="text-gray-400">No mentors matched yet.</p>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {mentors.map(m => (
                                <div key={m.mentor_id} className="bg-gray-900 rounded-xl p-4">
                                    <div className="font-medium">{m.name}</div>
                                    {m.match_reason && <p className="text-sm text-gray-400 mt-1">{m.match_reason}</p>}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* ── Panel: Market Signal ────────────────────── */}
            {!loading && panel === 'market' && market && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold">Market Signal — {selectedCluster}</h2>
                        <HelpBubble text={HELP_TEXT.market} />
                    </div>
                    {market.metrics && (
                        <div className="bg-gray-900 rounded-xl p-4 grid grid-cols-2 gap-4">
                            {Object.entries(market.metrics).map(([k, v]) => (
                                <div key={k}>
                                    <div className="text-xs text-gray-400 capitalize">{k.replace(/_/g, ' ')}</div>
                                    <div className="text-xl font-bold">{String(v)}</div>
                                </div>
                            ))}
                        </div>
                    )}
                    {market.recurring_skills?.length > 0 && (
                        <div className="bg-gray-900 rounded-xl p-4">
                            <h3 className="text-sm font-medium text-gray-400 mb-2">Recurring Skills</h3>
                            <div className="flex flex-wrap gap-2">
                                {market.recurring_skills.map((s: string) => (
                                    <span key={s} className="px-3 py-1 bg-gray-800 rounded-full text-xs">{s}</span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

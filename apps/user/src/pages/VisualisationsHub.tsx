import React, { useEffect, useState } from "react";
import { VISUAL_COMPONENTS } from "../components/visuals/registry";
import { API } from '../lib/apiConfig';
import { getEvidence, getTouchnots } from '../lib/api';
import { useSelectionStore } from '../lib/selection_store';

interface VisualEntry {
    id: string;
    title: string;
    category: string;
    react_component: string;
}

// Inline fallback if backend is unreachable
const FALLBACK_REGISTRY: VisualEntry[] = [
    { id: "quadrant_fit_d3", title: "Market Fit Quadrant", category: "Positioning", react_component: "QuadrantFitD3View" },
    { id: "wordcloud_connected_d3", title: "Skill Cloud Analysis", category: "Market Trends", react_component: "ConnectedWordCloudD3View" },
    { id: "touchpoint_network_cytoscape", title: "Network Touchpoints", category: "Explainability", react_component: "TouchpointNetworkCytoscapeView" },
    { id: "mindmap_reactflow", title: "Career Path Mind Map", category: "User Directed", react_component: "MindMapReactFlowView" },
];

// ── TouchPoints Overlay Panel ─────────────────────────────────

function TouchPointsPanel() {
    const { selection } = useSelectionStore();
    const [evidence, setEvidence] = useState<any[]>([]);
    const [touchnots, setTouchnots] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!selection?.touchpoint_ids?.length) {
            setEvidence([]);
            setTouchnots([]);
            return;
        }
        setLoading(true);
        Promise.all([
            getEvidence(selection.touchpoint_ids).catch(() => ({ items: [] })),
            getTouchnots(selection.touchpoint_ids).catch(() => ({ items: [] })),
        ]).then(([ev, tn]) => {
            setEvidence(ev.items || []);
            setTouchnots(tn.items || []);
        }).finally(() => setLoading(false));
    }, [selection?.touchpoint_ids]);

    if (!selection) {
        return (
            <div className="p-4 text-sm text-gray-400 italic">
                Click a data point in any visual to see evidence and gaps here.
            </div>
        );
    }

    return (
        <div className="p-4 space-y-4 overflow-y-auto">
            <div className="text-xs text-gray-500">
                Source: <span className="font-medium text-gray-700">{selection.source_visual_id}</span>
                {" · "}{selection.touchpoint_ids.length} touchpoints
            </div>

            {loading && <div className="text-sm text-gray-500">Loading evidence…</div>}

            {/* Evidence Section */}
            {evidence.length > 0 && (
                <div>
                    <h4 className="text-sm font-semibold text-green-700 mb-2">Evidence ({evidence.length})</h4>
                    {evidence.map((ev, i) => (
                        <div key={i} className="bg-green-50 border border-green-100 rounded-lg p-3 mb-2 text-xs">
                            <div className="font-medium text-gray-800">{ev.text_span}</div>
                            <div className="text-gray-500 mt-1">
                                {ev.source} / {ev.section} · Confidence: {Math.round((ev.confidence || 0) * 100)}%
                            </div>
                            {ev.tags?.length > 0 && (
                                <div className="flex gap-1 mt-1 flex-wrap">
                                    {ev.tags.map((t: string) => (
                                        <span key={t} className="bg-green-100 text-green-700 px-1.5 py-0.5 rounded text-[10px]">{t}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Touch-Nots (Gaps) Section */}
            {touchnots.length > 0 && (
                <div>
                    <h4 className="text-sm font-semibold text-amber-700 mb-2">Gaps ({touchnots.length})</h4>
                    {touchnots.map((tn, i) => (
                        <div key={i} className="bg-amber-50 border border-amber-100 rounded-lg p-3 mb-2 text-xs">
                            <div className="font-medium text-gray-800">{tn.reason}</div>
                            <div className="text-gray-500 mt-1">
                                Type: {tn.gap_type} · Confidence: {Math.round((tn.confidence || 0) * 100)}%
                            </div>
                            {tn.suggested_actions?.length > 0 && (
                                <ul className="list-disc list-inside text-gray-600 mt-1">
                                    {tn.suggested_actions.map((a: string, j: number) => <li key={j}>{a}</li>)}
                                </ul>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {!loading && evidence.length === 0 && touchnots.length === 0 && (
                <div className="text-sm text-gray-400">No evidence or gaps found for this selection.</div>
            )}
        </div>
    );
}

// ── Main Hub ──────────────────────────────────────────────────

export default function VisualisationsHub() {
    const [registry, setRegistry] = useState<VisualEntry[]>(FALLBACK_REGISTRY);
    const [selectedVisual, setSelectedVisual] = useState<string>(FALLBACK_REGISTRY[0].id);
    const [loading, setLoading] = useState(true);
    const [panelOpen, setPanelOpen] = useState(true);
    const { selection } = useSelectionStore();

    useEffect(() => {
        fetch(`${API.insights}/visuals`)
            .then(res => res.json())
            .then(data => {
                if (data.visuals && data.visuals.length > 0) {
                    setRegistry(data.visuals);
                    setSelectedVisual(data.visuals[0].id);
                }
            })
            .catch(() => { /* keep fallback */ })
            .finally(() => setLoading(false));
    }, []);

    const activeVisual = registry.find(v => v.id === selectedVisual);
    const Component = activeVisual ? VISUAL_COMPONENTS[activeVisual.react_component] : null;

    return (
        <div className="flex bg-gray-50 h-screen overflow-hidden">
            {/* Sidebar — Visual Registry */}
            <div className="w-64 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
                <div className="p-4 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">Visuals Registry</h3>
                    <p className="text-xs text-gray-500 mt-1">
                        {loading ? "Loading…" : `${registry.length} visualisations`}
                    </p>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {registry.map(v => (
                        <div
                            key={v.id}
                            onClick={() => setSelectedVisual(v.id)}
                            className={`p-3 rounded-lg cursor-pointer transition-colors text-sm font-medium ${selectedVisual === v.id
                                    ? "bg-indigo-50 text-indigo-700 border border-indigo-100"
                                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                                }`}
                        >
                            {v.title}
                            <div className="text-xs font-normal opacity-70 mt-1">{v.category}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Chart Area */}
            <div className="flex-1 flex flex-col h-full overflow-hidden">
                <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-bold text-gray-900">{activeVisual?.title || "Select a Visual"}</h2>
                        <p className="text-sm text-gray-500">
                            Component: <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">{activeVisual?.react_component}</code>
                        </p>
                    </div>
                    <button
                        onClick={() => setPanelOpen(!panelOpen)}
                        className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                        {panelOpen ? "Hide" : "Show"} Touch-Points
                    </button>
                </div>

                <div className="flex-1 p-6 overflow-auto">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 h-full flex items-center justify-center p-4 relative">
                        {Component ? (
                            <div className="w-full h-full relative">
                                <Component width={800} height={600} />
                            </div>
                        ) : (
                            <div className="text-gray-400">Component not found or not loaded</div>
                        )}
                    </div>
                </div>
            </div>

            {/* Touch-Points Overlay Panel (right side) */}
            {panelOpen && (
                <div className="w-80 bg-white border-l border-gray-200 flex flex-col flex-shrink-0">
                    <div className="p-4 border-b border-gray-200">
                        <h3 className="font-bold text-gray-900 text-sm">Touch-Points</h3>
                        <p className="text-xs text-gray-500 mt-0.5">Evidence & Gaps</p>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        <TouchPointsPanel />
                    </div>
                </div>
            )}
        </div>
    );
}

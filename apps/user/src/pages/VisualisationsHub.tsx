import React, { useEffect, useState } from "react";
import { VISUAL_COMPONENTS } from "../components/visuals/registry";
import { API } from '../lib/apiConfig';

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

export default function VisualisationsHub() {
    const [registry, setRegistry] = useState<VisualEntry[]>(FALLBACK_REGISTRY);
    const [selectedVisual, setSelectedVisual] = useState<string>(FALLBACK_REGISTRY[0].id);
    const [loading, setLoading] = useState(true);

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
            {/* Sidebar */}
            <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
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

            {/* Main Area */}
            <div className="flex-1 flex flex-col h-full overflow-hidden">
                <div className="bg-white border-b border-gray-200 px-6 py-4">
                    <h2 className="text-xl font-bold text-gray-900">{activeVisual?.title || "Select a Visual"}</h2>
                    <p className="text-sm text-gray-500">
                        Component: <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">{activeVisual?.react_component}</code>
                    </p>
                </div>

                <div className="flex-1 p-6 overflow-auto">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 h-full flex items-center justify-center p-4 relative">
                        {Component ? (
                            <div className="w-full h-full relative">
                                <Component
                                    width={800}
                                    height={600}
                                    data={{}} // Placeholder data, components should handle empty data gracefully or mock it internally
                                />
                            </div>
                        ) : (
                            <div className="text-gray-400">Component not found or not loaded</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

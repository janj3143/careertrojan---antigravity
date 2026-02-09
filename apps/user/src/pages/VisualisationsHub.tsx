import React, { useState } from "react";
import { VISUAL_COMPONENTS } from "../components/visuals/registry";

// Hardcoded registry for now as backend endpoint is missing
const REGISTRY = [
    {
        id: "quadrant-fit",
        title: "Market Fit Quadrant",
        category: "Strategic",
        react_component: "QuadrantFitD3View"
    },
    {
        id: "word-cloud",
        title: "Skill Cloud Analysis",
        category: "Text Analysis",
        react_component: "ConnectedWordCloudD3View"
    },
    {
        id: "network-graph",
        title: "Network Touchpoints",
        category: "Graph",
        react_component: "TouchpointNetworkCytoscapeView"
    },
    {
        id: "mind-map",
        title: "Career Path Mind Map",
        category: "Planning",
        react_component: "MindMapReactFlowView"
    }
];

export default function VisualisationsHub() {
    const [selectedVisual, setSelectedVisual] = useState<string>(REGISTRY[0].id);

    const activeVisual = REGISTRY.find(v => v.id === selectedVisual);
    const Component = activeVisual ? VISUAL_COMPONENTS[activeVisual.react_component] : null;

    return (
        <div className="flex bg-gray-50 h-screen overflow-hidden">
            {/* Sidebar */}
            <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
                <div className="p-4 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">Visuals Registry</h3>
                    <p className="text-xs text-gray-500 mt-1">Advanced Analytics Views</p>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {REGISTRY.map(v => (
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

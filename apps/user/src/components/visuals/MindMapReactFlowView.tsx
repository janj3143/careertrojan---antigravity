
import React from "react";
import ReactFlow, { Background, Controls, MiniMap, addEdge, useEdgesState, useNodesState } from "reactflow";
import "reactflow/dist/style.css";

const DEFAULT_NODES = [
    { id: "root", position: { x: 400, y: 50 }, data: { label: "My Career Plan" }, type: "default" },
    { id: "skills", position: { x: 200, y: 180 }, data: { label: "Skills to Develop" } },
    { id: "roles", position: { x: 600, y: 180 }, data: { label: "Target Roles" } },
    { id: "actions", position: { x: 400, y: 310 }, data: { label: "Next Actions" } },
];
const DEFAULT_EDGES = [
    { id: "e-root-skills", source: "root", target: "skills" },
    { id: "e-root-roles", source: "root", target: "roles" },
    { id: "e-root-actions", source: "root", target: "actions" },
];

export function MindMapReactFlowView({ width = 860, height = 520 }: {
    width?: number; height?: number;
}) {
    // Load saved mind-map from localStorage if available
    const saved = React.useMemo(() => {
        try {
            const raw = localStorage.getItem("careertrojan_mindmap");
            if (raw) return JSON.parse(raw);
        } catch { /* ignore */ }
        return null;
    }, []);

    const [nodes, setNodes, onNodesChange] = useNodesState(saved?.nodes ?? DEFAULT_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(saved?.edges ?? DEFAULT_EDGES);
    const [status, setStatus] = React.useState<string>("");

    const onConnect = React.useCallback((params: any) => setEdges(eds => addEdge(params, eds)), [setEdges]);

    function save() {
        setStatus("Saving…");
        try {
            localStorage.setItem("careertrojan_mindmap", JSON.stringify({ nodes, edges }));
            setStatus("Saved ✓");
            setTimeout(() => setStatus(""), 2000);
        } catch (e: any) {
            setStatus(String(e?.message ?? e));
        }
    }

    return (
        <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <b>Mind Map (React Flow)</b>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <span style={{ fontSize: 12, color: "#666" }}>{status}</span>
                    <button onClick={save} className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700">
                        Save
                    </button>
                </div>
            </div>
            <div style={{ height }}>
                <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} fitView>
                    <MiniMap /><Controls /><Background />
                </ReactFlow>
            </div>
        </div>
    );
}

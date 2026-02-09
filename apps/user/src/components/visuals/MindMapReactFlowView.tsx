
import React from "react";
import ReactFlow, { Background, Controls, MiniMap, addEdge, useEdgesState, useNodesState } from "reactflow";
import "reactflow/dist/style.css";

export function MindMapReactFlowView({ initialNodes = [], initialEdges = [], onSave, height = 520 }: {
    initialNodes: any[]; initialEdges: any[]; onSave: (doc: { nodes: any[]; edges: any[] }) => Promise<void>; height?: number;
}) {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const [status, setStatus] = React.useState<string>("");

    const onConnect = React.useCallback((params: any) => setEdges(eds => addEdge(params, eds)), [setEdges]);

    async function save() {
        setStatus("Saving…");
        try { await onSave({ nodes, edges }); setStatus("Saved."); }
        catch (e: any) { setStatus(String(e?.message ?? e)); }
    }

    return (
        <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
                <b>Mind Map (React Flow)</b>
                <button onClick={save} style={{ padding: "6px 10px", cursor: "pointer" }}>Save</button>
            </div>
            <div style={{ fontSize: 12, color: "#666", marginBottom: 6 }}>{status}</div>
            <div style={{ height }}>
                <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} fitView>
                    <MiniMap /><Controls /><Background />
                </ReactFlow>
            </div>
        </div>
    );
}

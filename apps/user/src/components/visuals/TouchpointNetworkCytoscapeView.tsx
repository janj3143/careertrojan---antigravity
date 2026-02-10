
import React from "react";
import CytoscapeComponent from "react-cytoscapejs";
import { getNetworkGraph } from "../../lib/api";
import { useSelectionStore } from "../../lib/selection_store";

export function TouchpointNetworkCytoscapeView({ width = 860, height = 520 }: {
    width?: number; height?: number;
}) {
    const { setSelection } = useSelectionStore();
    const [elements, setElements] = React.useState<any[]>([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        let cancel = false;
        getNetworkGraph()
            .then(data => {
                if (cancel) return;
                // Flatten nodes + edges into Cytoscape elements array
                const cyElements = [
                    ...(data.nodes || []),
                    ...(data.edges || []),
                ];
                setElements(cyElements);
            })
            .catch(() => {})
            .finally(() => !cancel && setLoading(false));
        return () => { cancel = true; };
    }, []);

    if (loading) return <div style={{ color: "#666" }}>Loading network graph…</div>;
    if (elements.length === 0) return <div style={{ color: "#999" }}>No graph data available</div>;

    return (
        <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
            <b>Touch-Point Network (Cytoscape)</b>
            <div style={{ height }}>
                <CytoscapeComponent
                    elements={elements}
                    style={{ width: "100%", height: "100%" }}
                    layout={{ name: "cose", animate: false, padding: 20 }}
                    stylesheet={[
                        { selector: "node[type='profile']", style: { "background-color": "#2b6cb0", label: "data(label)", "font-size": 10, width: 24, height: 24 } },
                        { selector: "node[type='skill']", style: { "background-color": "#48bb78", label: "data(label)", "font-size": 9, width: 18, height: 18 } },
                        { selector: "edge", style: { width: 1, "line-color": "#cbd5e0", "curve-style": "bezier" } },
                    ]}
                    cy={(cy) => {
                        cy.on("tap", "node", (evt) => {
                            const n = evt.target;
                            const touchpoint_ids = (n.data("touchpoint_ids") || []) as string[];
                            setSelection({
                                source_visual_id: "touchpoint_network_cytoscape",
                                selection_type: "node",
                                ids: [String(n.id())],
                                touchpoint_ids,
                                filters: {},
                            });
                        });
                    }}
                />
            </div>
        </div>
    );
}

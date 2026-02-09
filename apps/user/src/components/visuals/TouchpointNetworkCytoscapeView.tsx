
import React from "react";
import CytoscapeComponent from "react-cytoscapejs";

export function TouchpointNetworkCytoscapeView({ elements, height = 520, onSelect }: {
    elements: any[]; height?: number; onSelect: (payload: { id: string; touchpoint_ids: string[] }) => void;
}) {
    return (
        <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
            <b>Touch-Point Network (Cytoscape)</b>
            <div style={{ height }}>
                <CytoscapeComponent
                    elements={elements}
                    style={{ width: "100%", height: "100%" }}
                    layout={{ name: "cose", animate: false, padding: 20 }}
                    cy={(cy) => {
                        cy.on("tap", "node", (evt) => {
                            const n = evt.target;
                            const touchpoint_ids = (n.data("touchpoint_ids") || []) as string[];
                            onSelect({ id: String(n.id()), touchpoint_ids });
                        });
                    }}
                />
            </div>
        </div>
    );
}

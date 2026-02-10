
import React from "react";
import * as d3 from "d3";
import cloud from "d3-cloud";
import { getTermCloud, getCooccurrence } from "../../lib/api";
import type { CohortFilters, TermCloudResponse, CooccurrenceResponse } from "../../lib/types";
import { useSelectionStore } from "../../lib/selection_store";

export function ConnectedWordCloudD3View({ filters = {}, width = 860, height = 520 }: {
    filters?: CohortFilters; width?: number; height?: number;
}) {
    const ref = React.useRef<SVGSVGElement | null>(null);
    const { setSelection } = useSelectionStore();
    const [cloudData, setCloudData] = React.useState<TermCloudResponse | null>(null);
    const [edges, setEdges] = React.useState<CooccurrenceResponse | null>(null);
    const [selected, setSelected] = React.useState<string | null>(null);

    React.useEffect(() => {
        let cancel = false;
        getTermCloud(filters).then(r => !cancel && setCloudData(r)).catch(() => {});
        return () => { cancel = true; };
    }, [JSON.stringify(filters)]);

    React.useEffect(() => {
        if (!selected) { setEdges(null); return; }
        let cancel = false;
        getCooccurrence(filters, selected).then(r => !cancel && setEdges(r)).catch(() => !cancel && setEdges(null));
        return () => { cancel = true; };
    }, [selected, JSON.stringify(filters)]);

    React.useEffect(() => {
        if (!cloudData || !ref.current) return;
        const svg = d3.select(ref.current); svg.selectAll("*").remove();
        const words = cloudData.terms.map(t => ({ text: t.text, value: t.value, touchpoint_ids: t.touchpoint_ids ?? [] }));
        const maxV = d3.max(words, d => d.value) ?? 1, minV = d3.min(words, d => d.value) ?? 0;
        const sizeScale = d3.scaleLinear().domain([minV, maxV]).range([12, 64]);

        const layout = cloud()
            .size([width, height])
            .words(words.map(w => ({ ...w, size: sizeScale(w.value) } as any)))
            .padding(2).rotate(() => (Math.random() > 0.8 ? 90 : 0))
            .font("system-ui").fontSize((d: any) => d.size)
            .on("end", (drawWords: any[]) => {
                const g = svg.append("g").attr("transform", `translate(${width / 2},${height / 2})`);

                if (edges && selected) {
                    const pos = new Map<string, { x: number; y: number }>();
                    drawWords.forEach(w => pos.set(String(w.text), { x: w.x, y: w.y }));
                    const edgeG = g.append("g").attr("stroke", "#999").attr("stroke-width", 1).attr("opacity", 0.55);
                    edges.edges.slice(0, 50).forEach(e => {
                        const a = pos.get(e.source), b = pos.get(e.target);
                        if (a && b) edgeG.append("line").attr("x1", a.x).attr("y1", a.y).attr("x2", b.x).attr("y2", b.y);
                    });
                }

                g.selectAll("text").data(drawWords).enter().append("text")
                    .style("font-size", (d: any) => `${d.size}px`).style("font-family", "system-ui")
                    .style("cursor", "pointer").attr("text-anchor", "middle")
                    .attr("transform", (d: any) => `translate(${d.x},${d.y}) rotate(${d.rotate})`)
                    .attr("fill", (d: any) => (selected && d.text === selected ? "#111" : "#2b6cb0"))
                    .attr("opacity", (d: any) => (selected && d.text !== selected ? 0.35 : 0.9))
                    .text((d: any) => d.text)
                    .on("click", (_, d: any) => {
                        const term = String(d.text); setSelected(term);
                        setSelection({
                            source_visual_id: "wordcloud_connected_d3", selection_type: "term",
                            ids: [term], touchpoint_ids: (d.touchpoint_ids ?? []) as string[], filters
                        });
                    });
            });

        layout.start();
    }, [cloudData, edges, selected, width, height]);

    if (!cloudData) return <div style={{ color: "#666" }}>Loading terms…</div>;
    return <svg ref={ref} width={width} height={height} style={{ border: "1px solid #ddd", borderRadius: 12 }} />;
}

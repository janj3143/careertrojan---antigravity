
import React from "react";
import * as d3 from "d3";
import { getQuadrant } from "../../lib/api";
import type { CohortFilters, QuadrantResponse } from "../../lib/types";
import { useSelectionStore } from "../../lib/selection_store";

export function QuadrantFitD3View({ filters = {}, width = 860, height = 520 }: {
    filters?: CohortFilters; width?: number; height?: number;
}) {
    const ref = React.useRef<SVGSVGElement | null>(null);
    const { setSelection } = useSelectionStore();
    const [data, setData] = React.useState<QuadrantResponse | null>(null);

    React.useEffect(() => {
        let cancel = false;
        getQuadrant(filters).then(r => !cancel && setData(r)).catch(() => {});
        return () => { cancel = true; };
    }, [JSON.stringify(filters)]);

    React.useEffect(() => {
        if (!data || !ref.current) return;
        const svg = d3.select(ref.current); svg.selectAll("*").remove();
        const m = { top: 28, right: 16, bottom: 46, left: 56 };
        const W = width - m.left - m.right, H = height - m.top - m.bottom;
        const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
        const x = d3.scaleLinear().domain([0, 100]).range([0, W]);
        const y = d3.scaleLinear().domain([0, 100]).range([H, 0]);
        g.append("g").attr("transform", `translate(0,${H})`).call(d3.axisBottom(x));
        g.append("g").call(d3.axisLeft(y));
        g.append("line").attr("x1", x(data.x_threshold)).attr("x2", x(data.x_threshold)).attr("y1", 0).attr("y2", H)
            .attr("stroke", "#999").attr("stroke-dasharray", "4,4");
        g.append("line").attr("x1", 0).attr("x2", W).attr("y1", y(data.y_threshold)).attr("y2", y(data.y_threshold))
            .attr("stroke", "#999").attr("stroke-dasharray", "4,4");

        g.selectAll("circle").data(data.points).enter().append("circle")
            .attr("cx", d => x(d.x)).attr("cy", d => y(d.y))
            .attr("r", d => 4 + Math.round((d.confidence ?? 0.5) * 4))
            .attr("fill", "#2b6cb0").attr("opacity", 0.85).style("cursor", "pointer")
            .on("click", (_, d: any) => setSelection({
                source_visual_id: "quadrant_fit_d3", selection_type: "point",
                ids: [String(d.id)], touchpoint_ids: (d.touchpoint_ids ?? []) as string[], filters
            }));
    }, [data, width, height]);

    if (!data) return <div style={{ color: "#666" }}>Loading quadrant…</div>;
    return <svg ref={ref} width={width} height={height} style={{ border: "1px solid #ddd", borderRadius: 12 }} />;
}

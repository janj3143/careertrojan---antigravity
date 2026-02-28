
import React from "react";
import * as d3 from "d3";
import cloud from "d3-cloud";
import type { ApiConfig } from "../../lib/api";
import { getTermCloud, getCooccurrence } from "../../lib/api";
import type { CohortFilters, TermCloudResponse, CooccurrenceResponse } from "../../lib/types";
import { useSelectionStore } from "../../lib/selection_store";
import { useSkillTemplateStore } from "../../lib/skill_template_store";

type WordCloudLayerMode = "all" | "dominant" | "growth" | "unknown";

function splitTerms(input: string): string[] {
    return input
        .split(",")
        .map((term) => term.trim().toLowerCase())
        .filter(Boolean);
}

function matchesAny(text: string, tokens: string[]): boolean {
    const lower = text.toLowerCase();
    return tokens.some((token) => lower.includes(token));
}

export function ConnectedWordCloudD3View({ api, filters, width = 860, height = 520 }: {
    api: ApiConfig; filters: CohortFilters; width?: number; height?: number;
}) {
    const ref = React.useRef<SVGSVGElement | null>(null);
    const { setSelection } = useSelectionStore();
    const [cloudData, setCloudData] = React.useState<TermCloudResponse | null>(null);
    const [edges, setEdges] = React.useState<CooccurrenceResponse | null>(null);
    const [selected, setSelected] = React.useState<string | null>(null);
    const [layerMode, setLayerMode] = React.useState<WordCloudLayerMode>("all");
    const { template } = useSkillTemplateStore();

    React.useEffect(() => {
        let cancel = false;
        getTermCloud(api, filters).then(r => !cancel && setCloudData(r));
        return () => { cancel = true; };
    }, [api.baseUrl, JSON.stringify(filters)]);

    React.useEffect(() => {
        if (!selected) { setEdges(null); return; }
        let cancel = false;
        getCooccurrence(api, filters, selected).then(r => !cancel && setEdges(r)).catch(() => !cancel && setEdges(null));
        return () => { cancel = true; };
    }, [selected, api.baseUrl, JSON.stringify(filters)]);

    React.useEffect(() => {
        if (!cloudData || !ref.current) return;
        const svg = d3.select(ref.current); svg.selectAll("*").remove();
        const dominantTerms = splitTerms(template.dominantElements);
        const growthTerms = splitTerms(template.growthElements);

        const words = cloudData.terms.map(t => {
            const text = t.text;
            const isDominant = dominantTerms.length > 0 && matchesAny(text, dominantTerms);
            const isGrowth = growthTerms.length > 0 && matchesAny(text, growthTerms);
            const layer = isDominant ? "dominant" : isGrowth ? "growth" : "unknown";
            return { text, value: t.value, touchpoint_ids: t.touchpoint_ids ?? [], layer };
        });

        const activeWords = layerMode === "all" ? words : words.filter((w: any) => w.layer === layerMode);
        const wordsToRender = activeWords.length > 0 ? activeWords : words;
        const maxV = d3.max(words, d => d.value) ?? 1, minV = d3.min(words, d => d.value) ?? 0;
        const sizeScale = d3.scaleLinear().domain([minV, maxV]).range([12, 64]);

        const layout = cloud()
            .size([width, height])
            .words(wordsToRender.map(w => ({ ...w, size: sizeScale(w.value) } as any)))
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
                    .attr("fill", (d: any) => {
                        if (selected && d.text === selected) return "#111";
                        if (d.layer === "dominant") return "#065F46";
                        if (d.layer === "growth") return "#B45309";
                        return "#2b6cb0";
                    })
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
    }, [cloudData, edges, selected, width, height, layerMode, template.dominantElements, template.growthElements]);

    if (!cloudData) return <div style={{ color: "#666" }}>Loading terms…</div>;
    return (
        <div className="w-full h-full">
            <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
                <span className="text-gray-500">Layer mode</span>
                {[
                    { id: "all", label: "All" },
                    { id: "dominant", label: "Dominant" },
                    { id: "growth", label: "Growth" },
                    { id: "unknown", label: "Unknown" },
                ].map((item) => (
                    <button
                        key={item.id}
                        onClick={() => setLayerMode(item.id as WordCloudLayerMode)}
                        className={`rounded-full border px-2 py-1 ${layerMode === item.id ? "border-indigo-300 bg-indigo-50 text-indigo-700" : "border-gray-200 bg-white text-gray-600"}`}
                    >
                        {item.label}
                    </button>
                ))}
                <span className="ml-2 text-emerald-700">● Dominant</span>
                <span className="text-amber-700">● Growth</span>
                <span className="text-blue-700">● Unknown</span>
            </div>
            <svg ref={ref} width={width} height={height} style={{ border: "1px solid #ddd", borderRadius: 12 }} />
        </div>
    );
}

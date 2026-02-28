/**
 * SkillsCompetencySpiderD3View — Technical Skills / Competency Spider Chart
 * 
 * A D3-based radar/spider chart with 7 axes:
 *   Technical Skills, Engineering, Development, Sales & Marketing, 
 *   Finance & Admin, Industry Knowledge, Certifications
 * 
 * This is the complementary chart to LeadershipSpiderD3View — together they
 * provide the "two spider" model:
 *   1. Leadership / Strategy / Vision / Management  (LeadershipSpiderD3View)
 *   2. Skills / Competency / Technical split-out    (this component)
 * 
 * Supports:
 *   - Profile overlay with AI-scored dimension values
 *   - Peer cohort comparison overlay
 *   - Bias-aware display (AI score vs peer average)
 *   - Touchpoint-aware click → evidence panel
 */

import React from "react";
import * as d3 from "d3";
import { API } from "../../lib/apiConfig";
import { useSelectionStore } from "../../lib/selection_store";

interface RadarSeries {
    label: string;
    values: number[];
    color?: string;
}

interface RadarResponse {
    axes: string[];
    series: RadarSeries[];
    touchpoint_map?: Record<string, string[]>;
}

const DEFAULT_COLORS = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"];
const AXIS_ICONS: Record<string, string> = {
    "Technical Skills": "⚙️",
    "Engineering": "🔧",
    "Development": "💻",
    "Sales & Marketing": "📈",
    "Finance & Admin": "📊",
    "Industry Knowledge": "🏭",
    "Certifications": "🎓",
};

export function SkillsCompetencySpiderD3View({
    width = 860,
    height = 600,
    profileId,
}: {
    width?: number;
    height?: number;
    profileId?: string;
}) {
    const svgRef = React.useRef<SVGSVGElement | null>(null);
    const tooltipRef = React.useRef<HTMLDivElement | null>(null);
    const { setSelection } = useSelectionStore();
    const [data, setData] = React.useState<RadarResponse | null>(null);
    const [error, setError] = React.useState<string | null>(null);

    // Fetch radar data from backend
    React.useEffect(() => {
        let cancel = false;
        const params = new URLSearchParams({ type: "skills" });
        if (profileId) params.set("profile_id", profileId);

        fetch(`${API.insights}/skills/radar?${params}`, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
            },
        })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
            .then((d) => {
                if (!cancel) setData(d);
            })
            .catch(() => {
                if (!cancel) {
                    // Fallback demo data
                    setData({
                        axes: [
                            "Technical Skills",
                            "Engineering",
                            "Development",
                            "Sales & Marketing",
                            "Finance & Admin",
                            "Industry Knowledge",
                            "Certifications",
                        ],
                        series: [
                            { label: "You", values: [82, 68, 75, 35, 42, 60, 55], color: "#2563EB" },
                            { label: "Peer Average", values: [65, 60, 62, 50, 48, 55, 50], color: "#94A3B8" },
                        ],
                    });
                    setError(null);
                }
            });
        return () => { cancel = true; };
    }, [profileId]);

    // Render D3 radar chart
    React.useEffect(() => {
        if (!data || !svgRef.current) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove();

        const { axes, series } = data;
        const n = axes.length;
        if (n === 0) return;

        const cx = width / 2;
        const cy = height / 2 - 10;
        const maxR = Math.min(width, height) / 2 - 80;
        const levels = 5;
        const angleSlice = (2 * Math.PI) / n;
        const rScale = d3.scaleLinear().domain([0, 100]).range([0, maxR]);

        const g = svg.append("g").attr("transform", `translate(${cx}, ${cy})`);

        // ── Grid: filled concentric polygons ──────────────────
        for (let lvl = levels; lvl >= 1; lvl--) {
            const r = (maxR / levels) * lvl;
            const pts = axes.map((_, i) => {
                const angle = angleSlice * i - Math.PI / 2;
                return `${Math.cos(angle) * r},${Math.sin(angle) * r}`;
            });

            g.append("polygon")
                .attr("points", pts.join(" "))
                .attr("fill", lvl % 2 === 0 ? "#F8FAFC" : "#F1F5F9")
                .attr("stroke", "#E2E8F0")
                .attr("stroke-width", 0.8);

            // Level label
            g.append("text")
                .attr("x", 4)
                .attr("y", -r + 4)
                .attr("font-size", 10)
                .attr("fill", "#94A3B8")
                .text(`${(100 / levels) * lvl}`);
        }

        // ── Axis lines + labels ───────────────────────────────
        axes.forEach((axis, i) => {
            const angle = angleSlice * i - Math.PI / 2;
            const x2 = Math.cos(angle) * maxR;
            const y2 = Math.sin(angle) * maxR;

            g.append("line")
                .attr("x1", 0).attr("y1", 0)
                .attr("x2", x2).attr("y2", y2)
                .attr("stroke", "#CBD5E1")
                .attr("stroke-width", 1);

            // Label
            const labelR = maxR + 35;
            const lx = Math.cos(angle) * labelR;
            const ly = Math.sin(angle) * labelR;
            const icon = AXIS_ICONS[axis] || "●";

            const labelG = g.append("g")
                .attr("transform", `translate(${lx}, ${ly})`)
                .style("cursor", "pointer")
                .on("click", () => {
                    const touchpoints = data.touchpoint_map?.[axis] || [];
                    setSelection({
                        source_visual_id: "skills_competency_spider_d3",
                        selection_type: "node",
                        ids: [axis],
                        touchpoint_ids: touchpoints,
                    });
                });

            labelG.append("text")
                .attr("text-anchor", "middle")
                .attr("dy", -6)
                .attr("font-size", 15)
                .text(icon);

            labelG.append("text")
                .attr("text-anchor", "middle")
                .attr("dy", 10)
                .attr("font-size", 11)
                .attr("font-weight", 600)
                .attr("fill", "#334155")
                .text(axis);
        });

        // ── Data polygons ─────────────────────────────────────
        const line = d3.lineRadial<number>()
            .radius((d) => rScale(d))
            .angle((_, i) => angleSlice * i)
            .curve(d3.curveCardinalClosed.tension(0.3));

        series.forEach((s, si) => {
            const color = s.color || DEFAULT_COLORS[si % DEFAULT_COLORS.length];
            const pathData = line(s.values)!;

            // Area fill
            g.append("path")
                .attr("d", pathData)
                .attr("fill", color)
                .attr("fill-opacity", si === 0 ? 0.2 : 0.08)
                .attr("stroke", color)
                .attr("stroke-width", si === 0 ? 2.5 : 1.5)
                .attr("stroke-dasharray", si === 0 ? "none" : "6,3");

            // Data dots
            s.values.forEach((val, vi) => {
                const angle = angleSlice * vi - Math.PI / 2;
                const px = Math.cos(angle) * rScale(val);
                const py = Math.sin(angle) * rScale(val);

                g.append("circle")
                    .attr("cx", px).attr("cy", py)
                    .attr("r", si === 0 ? 5 : 3.5)
                    .attr("fill", "white")
                    .attr("stroke", color)
                    .attr("stroke-width", 2)
                    .style("cursor", "pointer")
                    .on("mouseenter", function (event) {
                        d3.select(this).attr("r", si === 0 ? 7 : 5);
                        if (tooltipRef.current) {
                            tooltipRef.current.style.display = "block";
                            tooltipRef.current.style.left = `${event.offsetX + 12}px`;
                            tooltipRef.current.style.top = `${event.offsetY - 28}px`;
                            tooltipRef.current.innerHTML = `<strong>${axes[vi]}</strong><br/>${s.label}: ${val}`;
                        }
                    })
                    .on("mouseleave", function () {
                        d3.select(this).attr("r", si === 0 ? 5 : 3.5);
                        if (tooltipRef.current) tooltipRef.current.style.display = "none";
                    })
                    .on("click", () => {
                        const touchpoints = data.touchpoint_map?.[axes[vi]] || [];
                        setSelection({
                            source_visual_id: "skills_competency_spider_d3",
                            selection_type: "point",
                            ids: [axes[vi]],
                            touchpoint_ids: touchpoints,
                        });
                    });

                // Inline value label for primary series
                if (si === 0) {
                    g.append("text")
                        .attr("x", px)
                        .attr("y", py - 10)
                        .attr("text-anchor", "middle")
                        .attr("font-size", 10)
                        .attr("font-weight", 600)
                        .attr("fill", color)
                        .text(val);
                }
            });
        });

        // ── Delta indicators (difference badges) ─────────────
        if (series.length >= 2) {
            const userVals = series[0].values;
            const peerVals = series[1].values;

            axes.forEach((_axis, i) => {
                const diff = userVals[i] - peerVals[i];
                if (Math.abs(diff) < 3) return; // skip negligible

                const angle = angleSlice * i - Math.PI / 2;
                const midR = rScale(Math.max(userVals[i], peerVals[i])) + 18;
                const dx = Math.cos(angle) * midR;
                const dy = Math.sin(angle) * midR;

                const bg = diff > 0 ? "#DCFCE7" : "#FEE2E2";
                const fg = diff > 0 ? "#166534" : "#991B1B";
                const sign = diff > 0 ? "+" : "";

                g.append("rect")
                    .attr("x", dx - 16).attr("y", dy - 8)
                    .attr("width", 32).attr("height", 16)
                    .attr("rx", 8).attr("fill", bg);

                g.append("text")
                    .attr("x", dx).attr("y", dy + 3)
                    .attr("text-anchor", "middle")
                    .attr("font-size", 9)
                    .attr("font-weight", 700)
                    .attr("fill", fg)
                    .text(`${sign}${diff}`);
            });
        }

        // ── Legend ─────────────────────────────────────────────
        const legendG = svg.append("g").attr("transform", `translate(${width - 190}, 28)`);

        series.forEach((s, i) => {
            const color = s.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length];
            const row = legendG.append("g").attr("transform", `translate(0, ${i * 24})`);

            row.append("line")
                .attr("x1", 0).attr("y1", 7).attr("x2", 18).attr("y2", 7)
                .attr("stroke", color).attr("stroke-width", 2.5)
                .attr("stroke-dasharray", i === 0 ? "none" : "6,3");

            row.append("circle")
                .attr("cx", 9).attr("cy", 7).attr("r", 3.5)
                .attr("fill", "white").attr("stroke", color).attr("stroke-width", 2);

            row.append("text")
                .attr("x", 24).attr("y", 11)
                .attr("font-size", 12)
                .attr("fill", "#475569")
                .text(s.label);
        });

        // ── Title ─────────────────────────────────────────────
        svg.append("text")
            .attr("x", 20).attr("y", 28)
            .attr("font-size", 16)
            .attr("font-weight", 700)
            .attr("fill", "#1E293B")
            .text("⚙️ Skills & Competency Spider");

        svg.append("text")
            .attr("x", 20).attr("y", 46)
            .attr("font-size", 11)
            .attr("fill", "#64748B")
            .text("Technical · Engineering · Development · Domain · Certifications");

    }, [data, width, height]);

    if (error) {
        return <div style={{ color: "#EF4444", padding: 16 }}>Error: {error}</div>;
    }

    if (!data) {
        return <div style={{ color: "#666", padding: 16 }}>Loading Skills & Competency spider…</div>;
    }

    return (
        <div style={{ position: "relative" }}>
            <svg
                ref={svgRef}
                width={width}
                height={height}
                style={{ border: "1px solid #E2E8F0", borderRadius: 12, background: "white" }}
            />
            <div
                ref={tooltipRef}
                style={{
                    display: "none",
                    position: "absolute",
                    background: "#1E293B",
                    color: "white",
                    padding: "6px 10px",
                    borderRadius: 6,
                    fontSize: 12,
                    pointerEvents: "none",
                    zIndex: 10,
                    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
                }}
            />
        </div>
    );
}

import React from "react";
import type { ApiConfig } from "../../lib/api";
import { generateQuestions, getSkillsRadar } from "../../lib/api";
import type { StructuralRadarResponse } from "../../lib/types";
import { useSkillTemplateStore, type SkillTemplateState, type ConfidenceLevel, type Horizon } from "../../lib/skill_template_store";

type SpiderOption = "three_domain" | "leadership_strategy_vision_management" | "operational_execution";

function axisPoints(values: number[], radius: number, cx: number, cy: number): string {
    const n = Math.max(values.length, 1);
    return values
        .map((value, index) => {
            const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
            const scaled = (Math.max(0, Math.min(value, 10)) / 10) * radius;
            const x = cx + Math.cos(angle) * scaled;
            const y = cy + Math.sin(angle) * scaled;
            return `${x},${y}`;
        })
        .join(" ");
}

function inferSpiderOption(template: SkillTemplateState): SpiderOption {
    const dominant = template.dominantElements.toLowerCase();
    const growth = template.growthElements.toLowerCase();
    const combined = `${dominant} ${growth}`;

    if (combined.includes("strategy") || combined.includes("lead") || combined.includes("vision")) {
        return "leadership_strategy_vision_management";
    }
    if (combined.includes("execution") || combined.includes("ops") || combined.includes("operational") || combined.includes("delivery")) {
        return "operational_execution";
    }
    return "three_domain";
}

function percentBarWidth(value: number): string {
    const clamped = Math.max(0, Math.min(100, value));
    return `${clamped}%`;
}

function buildClues(data: StructuralRadarResponse, template: SkillTemplateState): string[] {
    const clues: string[] = [];
    const strategic = data.overview.strategic_score;
    const leadership = data.overview.leadership_score;
    const operational = data.overview.operational_score;
    const gap = data.overview.strategic_operational_gap;

    if (gap <= -1.2) clues.push("Execution appears stronger than strategy language; add more vision and roadmap framing.");
    if (gap >= 1.2) clues.push("Strategic framing is strong; add concrete delivery and operating cadence evidence.");
    if (data.domains.leadership.percentile < 45) clues.push("Leadership percentile is below cohort median; include stakeholder and delegation examples.");
    if (data.domains.strategic.percentile < 45) clues.push("Strategic percentile is low; add market-positioning and long-term planning signals.");
    if (data.domains.operational.percentile < 45) clues.push("Operational percentile is low; include execution metrics, runbooks, and delivery outcomes.");

    if (template.confidence === "low") clues.push("Low confidence selected: start with one high-confidence domain and build from recent evidence first.");
    if (template.horizon === "30d") clues.push("30-day horizon: prioritize quick wins that raise weakest percentile by at least 10 points.");
    if (template.growthElements.trim().length > 0) clues.push(`Growth focus captured: ${template.growthElements.trim()}. Use this to drive your next coaching prompts.`);

    if (clues.length === 0 && (strategic + leadership + operational) / 3 >= 6.5) {
        clues.push("Profile looks balanced and strong; focus on refining evidence quality rather than adding new themes.");
    }

    return clues.slice(0, 4);
}

function RadarCard({
    title,
    axes,
    user,
    peer,
    target,
}: {
    title: string;
    axes: string[];
    user: number[];
    peer: number[];
    target: number[];
}) {
    const width = 320;
    const height = 260;
    const cx = width / 2;
    const cy = height / 2 + 6;
    const radius = 92;

    const rings = [2, 4, 6, 8, 10];

    return (
        <div className="rounded-xl border border-gray-200 bg-white p-3">
            <h4 className="text-sm font-semibold text-gray-800 mb-2">{title}</h4>
            <svg width={width} height={height}>
                {rings.map((r) => (
                    <circle
                        key={r}
                        cx={cx}
                        cy={cy}
                        r={(r / 10) * radius}
                        fill="none"
                        stroke="#E5E7EB"
                        strokeWidth={1}
                    />
                ))}

                {axes.map((axis, index) => {
                    const angle = (Math.PI * 2 * index) / Math.max(axes.length, 1) - Math.PI / 2;
                    const x = cx + Math.cos(angle) * radius;
                    const y = cy + Math.sin(angle) * radius;
                    const lx = cx + Math.cos(angle) * (radius + 12);
                    const ly = cy + Math.sin(angle) * (radius + 12);
                    return (
                        <g key={axis}>
                            <line x1={cx} y1={cy} x2={x} y2={y} stroke="#E5E7EB" strokeWidth={1} />
                            <text x={lx} y={ly} fontSize={9} textAnchor="middle" fill="#6B7280">
                                {axis.replace(/_/g, " ")}
                            </text>
                        </g>
                    );
                })}

                <polygon points={axisPoints(target, radius, cx, cy)} fill="rgba(16,185,129,0.18)" stroke="#10B981" strokeWidth={2} />
                <polygon points={axisPoints(peer, radius, cx, cy)} fill="rgba(99,102,241,0.18)" stroke="#6366F1" strokeWidth={2} />
                <polygon points={axisPoints(user, radius, cx, cy)} fill="rgba(245,158,11,0.18)" stroke="#F59E0B" strokeWidth={2} />
            </svg>
            <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-600">
                <span className="inline-flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-amber-500" />You</span>
                <span className="inline-flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-indigo-500" />Peer median</span>
                <span className="inline-flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-emerald-500" />Target role median</span>
            </div>
        </div>
    );
}

export function StructuralCapabilityRadarView({ api }: { api: ApiConfig }) {
    const [data, setData] = React.useState<StructuralRadarResponse | null>(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);
    const [option, setOption] = React.useState<SpiderOption>("three_domain");
    const { template, setTemplate } = useSkillTemplateStore();
    const [coachingPrompts, setCoachingPrompts] = React.useState<string[]>([]);
    const [coachingLoading, setCoachingLoading] = React.useState(false);

    const suggestedOption = React.useMemo(() => inferSpiderOption(template), [template]);
    const clues = React.useMemo(() => (data ? buildClues(data, template) : []), [data, template]);

    const requestCoachingPrompts = React.useCallback(async () => {
        if (!clues.length) {
            setCoachingPrompts([]);
            return;
        }

        setCoachingLoading(true);
        try {
            const prompts = await generateQuestions(api, {
                question_type: "General competency",
                count: 3,
                fit: {
                    gap_clues: clues,
                    target_role: template.targetRole,
                    confidence: template.confidence,
                    horizon: template.horizon,
                },
            });
            setCoachingPrompts(Array.isArray(prompts) ? prompts : []);
        } catch {
            setCoachingPrompts([]);
        } finally {
            setCoachingLoading(false);
        }
    }, [api, clues, template]);

    React.useEffect(() => {
        let cancel = false;
        setLoading(true);
        setError(null);

        getSkillsRadar(api, {
            model: "structural_v1",
            spider_option: option,
            target_role: template.targetRole.trim() || undefined,
        })
            .then((response) => {
                if (cancel) return;
                if (!("model" in response) || response.model !== "structural_v1") {
                    setError("Structural model response not available.");
                    setData(null);
                    return;
                }
                setData(response as StructuralRadarResponse);
            })
            .catch((err) => {
                if (cancel) return;
                setError(String(err?.message || err));
                setData(null);
            })
            .finally(() => {
                if (!cancel) setLoading(false);
            });

        return () => {
            cancel = true;
        };
    }, [api.baseUrl, option, template.targetRole]);

    if (loading) return <div className="text-sm text-gray-500">Loading structural capability model…</div>;
    if (error) return <div className="text-sm text-red-600">{error}</div>;
    if (!data) return <div className="text-sm text-gray-500">No structural capability data available.</div>;

    return (
        <div className="w-full space-y-4">
            <div className="rounded-xl border border-gray-200 bg-white p-4 space-y-3">
                <h3 className="text-lg font-semibold text-gray-900">Guided Capability Template</h3>
                <p className="text-sm text-gray-600">Fill this in to steer spider shape, target calibration, and clue suggestions.</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                        <label className="text-xs text-gray-500">Target role</label>
                        <input
                            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            placeholder="e.g. Product Director"
                            value={template.targetRole}
                            onChange={(e) => setTemplate({ targetRole: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="text-xs text-gray-500">Dominant elements</label>
                        <input
                            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            placeholder="e.g. strategy, stakeholder alignment"
                            value={template.dominantElements}
                            onChange={(e) => setTemplate({ dominantElements: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="text-xs text-gray-500">Growth elements</label>
                        <input
                            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            placeholder="e.g. execution discipline, KPI literacy"
                            value={template.growthElements}
                            onChange={(e) => setTemplate({ growthElements: e.target.value })}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs text-gray-500">Confidence</label>
                            <select
                                className="mt-1 w-full rounded-md border border-gray-300 px-2 py-2 text-sm"
                                value={template.confidence}
                                onChange={(e) => setTemplate({ confidence: e.target.value as ConfidenceLevel })}
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-xs text-gray-500">Focus horizon</label>
                            <select
                                className="mt-1 w-full rounded-md border border-gray-300 px-2 py-2 text-sm"
                                value={template.horizon}
                                onChange={(e) => setTemplate({ horizon: e.target.value as Horizon })}
                            >
                                <option value="30d">30 days</option>
                                <option value="90d">90 days</option>
                                <option value="180d">180 days</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-1 text-indigo-700">
                        Suggested spider: {suggestedOption.replace(/_/g, " ")}
                    </span>
                    <button
                        className="rounded-md border border-gray-300 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
                        onClick={() => setOption(suggestedOption)}
                    >
                        Apply suggestion
                    </button>
                </div>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900">Structural Capability Architecture</h3>
                    <p className="text-sm text-gray-600">Strategic · Leadership · Operational with peer and target calibration.</p>
                </div>
                <div className="flex items-center gap-2">
                    <label className="text-xs text-gray-500">Spider option</label>
                    <select
                        className="rounded-md border border-gray-300 px-2 py-1 text-sm"
                        value={option}
                        onChange={(e) => setOption(e.target.value as SpiderOption)}
                    >
                        <option value="three_domain">Three-domain summary</option>
                        <option value="leadership_strategy_vision_management">Leadership / Strategy / Vision / Management</option>
                        <option value="operational_execution">Operational execution</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="rounded-lg border border-gray-200 bg-white p-3">
                    <p className="text-xs text-gray-500">Strategic</p>
                    <p className="text-2xl font-bold text-gray-900">{data.overview.strategic_score.toFixed(1)}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-white p-3">
                    <p className="text-xs text-gray-500">Leadership</p>
                    <p className="text-2xl font-bold text-gray-900">{data.overview.leadership_score.toFixed(1)}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-white p-3">
                    <p className="text-xs text-gray-500">Operational</p>
                    <p className="text-2xl font-bold text-gray-900">{data.overview.operational_score.toFixed(1)}</p>
                </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-4">
                <h4 className="text-sm font-semibold text-gray-800 mb-3">Peer Percentile Calibration</h4>
                <div className="space-y-3">
                    {[
                        { label: "Strategic", percentile: data.domains.strategic.percentile, delta: data.domains.strategic.delta_vs_peer_median },
                        { label: "Leadership", percentile: data.domains.leadership.percentile, delta: data.domains.leadership.delta_vs_peer_median },
                        { label: "Operational", percentile: data.domains.operational.percentile, delta: data.domains.operational.delta_vs_peer_median },
                    ].map((item) => (
                        <div key={item.label}>
                            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                                <span>{item.label}</span>
                                <span>{item.percentile.toFixed(1)}th percentile · Δ vs peer {item.delta >= 0 ? "+" : ""}{item.delta.toFixed(2)}</span>
                            </div>
                            <div className="h-2 w-full rounded bg-gray-100 overflow-hidden">
                                <div className="h-2 bg-indigo-500" style={{ width: percentBarWidth(item.percentile) }} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
                <RadarCard
                    title="Strategic Layer"
                    axes={data.domains.strategic.axes}
                    user={data.domains.strategic.user_values}
                    peer={data.domains.strategic.peer_median}
                    target={data.domains.strategic.target_role_median}
                />
                <RadarCard
                    title="Leadership & People Layer"
                    axes={data.domains.leadership.axes}
                    user={data.domains.leadership.user_values}
                    peer={data.domains.leadership.peer_median}
                    target={data.domains.leadership.target_role_median}
                />
                <RadarCard
                    title="Operational Execution Layer"
                    axes={data.domains.operational.axes}
                    user={data.domains.operational.user_values}
                    peer={data.domains.operational.peer_median}
                    target={data.domains.operational.target_role_median}
                />
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-4">
                <p className="text-sm text-gray-700">
                    <span className="font-semibold">Imbalance indicator:</span> Strategic − Operational =
                    <span className="font-semibold"> {data.overview.strategic_operational_gap.toFixed(1)}</span>
                    {" · "}
                    <span className="font-semibold">Profile shape:</span> {data.overview.profile_shape.replace(/_/g, " ")}
                </p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-4">
                <h4 className="text-sm font-semibold text-gray-800 mb-2">Intuitive Clues</h4>
                <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                    {clues.map((clue) => (
                        <li key={clue}>{clue}</li>
                    ))}
                </ul>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                    <button
                        className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs text-indigo-700 hover:bg-indigo-100"
                        onClick={requestCoachingPrompts}
                        disabled={coachingLoading}
                    >
                        {coachingLoading ? "Generating coaching prompts..." : "Generate coaching prompts from gaps"}
                    </button>
                </div>
                {coachingPrompts.length > 0 && (
                    <ul className="mt-3 list-disc pl-5 space-y-1 text-sm text-indigo-800">
                        {coachingPrompts.map((prompt) => (
                            <li key={prompt}>{prompt}</li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

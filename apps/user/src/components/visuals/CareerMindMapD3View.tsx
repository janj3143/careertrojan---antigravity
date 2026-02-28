/**
 * CareerMindMapD3View — Career-Driven Organic Mind Map
 * 
 * Inspired by the Figma OrganicMindMap design (l:\Redesign Mind Map Diagram).
 * Pure SVG with Bézier branches, 3 depth levels, hover glow effects.
 * 
 * Career branches auto-populated from AI analysis of user's CV/profile:
 *   - Core Skills (what you have)
 *   - Target Roles (where you're going)
 *   - Skill Gaps (what to develop)
 *   - Industry Sectors (your domains)
 *   - Certifications (credentials)
 *   - Career Actions (next steps)
 *   - Network (connections & mentors)
 *   - Experience Highlights (achievements)
 * 
 * Falls back to editable default structure if no AI data available.
 * Touchpoint-aware — click any node to see evidence in the Touch-Points panel.
 */

import { useState, useEffect, useCallback } from "react";
import { API } from "../../lib/apiConfig";
import { useSelectionStore } from "../../lib/selection_store";

// ── Types ──────────────────────────────────────────────────────

interface MindMapNode {
    id: string;
    label: string;
    children?: MindMapNode[];
    touchpoint_ids?: string[];
}

interface MindMapBranch {
    id: string;
    label: string;
    color: string;
    icon: string;
    startAngle: number;
    spread: number;
    children: MindMapNode[];
}

interface MindMapData {
    center_label: string;
    branches: MindMapBranch[];
}

// ── Default career-domain branches ─────────────────────────────

const DEFAULT_BRANCHES: MindMapBranch[] = [
    {
        id: "skills", label: "Core Skills", color: "#7C3AED", icon: "⚡",
        startAngle: 180, spread: 40,
        children: [
            { id: "s1", label: "Python / TypeScript" },
            { id: "s2", label: "Data Analysis" },
            { id: "s3", label: "Cloud Architecture" },
        ],
    },
    {
        id: "roles", label: "Target Roles", color: "#3B82F6", icon: "🎯",
        startAngle: 225, spread: 35,
        children: [
            { id: "r1", label: "Senior Engineer" },
            { id: "r2", label: "Tech Lead" },
            { id: "r3", label: "Engineering Manager" },
            { id: "r4", label: "CTO Track" },
        ],
    },
    {
        id: "gaps", label: "Skill Gaps", color: "#EF4444", icon: "🔴",
        startAngle: 270, spread: 30,
        children: [
            { id: "g1", label: "System Design" },
            { id: "g2", label: "People Management" },
            { id: "g3", label: "Public Speaking" },
        ],
    },
    {
        id: "sectors", label: "Industry Sectors", color: "#F59E0B", icon: "🏭",
        startAngle: 315, spread: 35,
        children: [
            { id: "i1", label: "FinTech" },
            { id: "i2", label: "HealthTech" },
        ],
    },
    {
        id: "certs", label: "Certifications", color: "#10B981", icon: "🎓",
        startAngle: 0, spread: 40,
        children: [
            { id: "c1", label: "AWS Solutions Architect" },
            { id: "c2", label: "PMP" },
            { id: "c3", label: "Scrum Master" },
            { id: "c4", label: "CISSP" },
        ],
    },
    {
        id: "actions", label: "Career Actions", color: "#06B6D4", icon: "🚀",
        startAngle: 45, spread: 35,
        children: [
            { id: "a1", label: "Update LinkedIn" },
            { id: "a2", label: "Build Portfolio" },
            { id: "a3", label: "Apply to 10 Roles" },
        ],
    },
    {
        id: "network", label: "Network", color: "#8B5CF6", icon: "🤝",
        startAngle: 90, spread: 40,
        children: [
            { id: "n1", label: "Mentors" },
            { id: "n2", label: "Industry Contacts" },
            { id: "n3", label: "Recruiters" },
            { id: "n4", label: "Alumni Network" },
            { id: "n5", label: "Professional Groups" },
        ],
    },
    {
        id: "highlights", label: "Experience", color: "#EC4899", icon: "⭐",
        startAngle: 135, spread: 38,
        children: [
            { id: "h1", label: "Led 12-person team" },
            { id: "h2", label: "Scaled to 1M users" },
            { id: "h3", label: "£2M cost savings" },
            { id: "h4", label: "Patent holder" },
        ],
    },
];

// ── SVG Geometry Helpers ───────────────────────────────────────

function curvePath(
    startX: number, startY: number,
    angle: number, length: number, curvature = 0.5,
) {
    const rad = (angle * Math.PI) / 180;
    const endX = startX + Math.cos(rad) * length;
    const endY = startY + Math.sin(rad) * length;
    const controlX = startX + Math.cos(rad) * (length * curvature);
    const controlY = startY + Math.sin(rad) * (length * curvature);
    return {
        path: `M ${startX} ${startY} Q ${controlX} ${controlY}, ${endX} ${endY}`,
        endX, endY,
    };
}

// ── Component ──────────────────────────────────────────────────

export function CareerMindMapD3View({
    width = 1000,
    height = 700,
    profileId,
}: {
    width?: number;
    height?: number;
    profileId?: string;
}) {
    const { setSelection } = useSelectionStore();
    const [branches, setBranches] = useState<MindMapBranch[]>(DEFAULT_BRANCHES);
    const [centerLabel, setCenterLabel] = useState("My Career");
    const [hoveredBranch, setHoveredBranch] = useState<string | null>(null);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);
    const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);

    // Try to load career-specific mind map from API
    useEffect(() => {
        const params = new URLSearchParams();
        if (profileId) params.set("profile_id", profileId);

        fetch(`${API.insights}/mindmap?${params}`, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
            },
        })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
            .then((data: MindMapData) => {
                if (data.branches?.length > 0) {
                    setBranches(data.branches);
                    if (data.center_label) setCenterLabel(data.center_label);
                }
            })
            .catch(() => {
                // Keep defaults — perfectly fine
            });
    }, [profileId]);

    const cx = width / 2;
    const cy = height / 2;
    const mainLength = 170;
    const subLength = 95;
    const tertLength = 50;

    const handleNodeClick = useCallback(
        (nodeId: string, touchpointIds: string[]) => {
            setSelection({
                source_visual_id: "career_mindmap_d3",
                selection_type: "node",
                ids: [nodeId],
                touchpoint_ids: touchpointIds,
            });
        },
        [setSelection],
    );

    return (
        <div style={{ position: "relative" }}>
            <svg
                width={width}
                height={height}
                viewBox={`0 0 ${width} ${height}`}
                style={{ border: "1px solid #E2E8F0", borderRadius: 12, background: "linear-gradient(135deg, #FAFBFC 0%, #F1F5F9 100%)" }}
            >
                {/* Background grid */}
                <defs>
                    <pattern id="mm-grid" width="40" height="40" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E2E8F0" strokeWidth="0.4" opacity="0.3" />
                    </pattern>
                    <filter id="mm-glow">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <filter id="mm-shadow">
                        <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15" />
                    </filter>
                </defs>

                <rect width={width} height={height} fill="url(#mm-grid)" rx="12" />

                {/* Title */}
                <text x="20" y="28" fontSize="16" fontWeight="700" fill="#1E293B">
                    🧠 Career Mind Map
                </text>
                <text x="20" y="46" fontSize="11" fill="#64748B">
                    Click any node to view evidence · Hover to highlight branch
                </text>

                {/* Branches */}
                {branches.map((branch) => {
                    const isHovered = hoveredBranch === branch.id;
                    const n = branch.children.length;

                    // Main branch
                    const main = curvePath(cx, cy, branch.startAngle, mainLength, 0.6);

                    return (
                        <g
                            key={branch.id}
                            onMouseEnter={() => setHoveredBranch(branch.id)}
                            onMouseLeave={() => setHoveredBranch(null)}
                            style={{ cursor: "pointer" }}
                        >
                            {/* Main branch line */}
                            <path
                                d={main.path}
                                stroke={branch.color}
                                strokeWidth={isHovered ? 7 : 5}
                                fill="none"
                                strokeLinecap="round"
                                opacity={isHovered ? 1 : 0.85}
                                filter={isHovered ? "url(#mm-glow)" : undefined}
                                style={{ transition: "all 0.3s ease" }}
                            />

                            {/* Main branch endpoint + label */}
                            <circle
                                cx={main.endX} cy={main.endY}
                                r={isHovered ? 22 : 18}
                                fill="white" stroke={branch.color} strokeWidth={2.5}
                                filter="url(#mm-shadow)"
                                style={{ transition: "all 0.3s ease" }}
                                onClick={() => handleNodeClick(branch.id, [])}
                            />
                            <text
                                x={main.endX} y={main.endY - 4}
                                textAnchor="middle" fontSize="14"
                            >
                                {branch.icon}
                            </text>
                            <text
                                x={main.endX} y={main.endY + 10}
                                textAnchor="middle"
                                fontSize="8" fontWeight="600" fill="#334155"
                            >
                                {branch.label}
                            </text>

                            {/* Sub-branches (children) */}
                            {branch.children.map((child, ci) => {
                                const subAngle =
                                    branch.startAngle +
                                    (ci - (n - 1) / 2) * (branch.spread / Math.max(n - 1, 1));
                                const subStart = curvePath(cx, cy, branch.startAngle, mainLength * 0.75, 0.6);
                                const sub = curvePath(subStart.endX, subStart.endY, subAngle, subLength, 0.7);
                                const isNodeHovered = hoveredNode === child.id;

                                return (
                                    <g key={child.id}>
                                        <path
                                            d={sub.path}
                                            stroke={branch.color}
                                            strokeWidth={isHovered ? 3.5 : 2.5}
                                            fill="none"
                                            strokeLinecap="round"
                                            opacity={isHovered ? 0.9 : 0.65}
                                            style={{ transition: "all 0.3s ease" }}
                                        />
                                        <circle
                                            cx={sub.endX} cy={sub.endY}
                                            r={isNodeHovered ? 16 : 12}
                                            fill="white"
                                            stroke={branch.color}
                                            strokeWidth={1.5}
                                            opacity={isHovered ? 1 : 0.8}
                                            style={{ transition: "all 0.3s ease", cursor: "pointer" }}
                                            onMouseEnter={(e) => {
                                                setHoveredNode(child.id);
                                                setTooltip({
                                                    x: e.nativeEvent.offsetX + 12,
                                                    y: e.nativeEvent.offsetY - 24,
                                                    text: child.label,
                                                });
                                            }}
                                            onMouseLeave={() => {
                                                setHoveredNode(null);
                                                setTooltip(null);
                                            }}
                                            onClick={() =>
                                                handleNodeClick(child.id, child.touchpoint_ids || [])
                                            }
                                        />
                                        <text
                                            x={sub.endX} y={sub.endY + 3}
                                            textAnchor="middle"
                                            fontSize="7" fontWeight="500" fill="#475569"
                                            pointerEvents="none"
                                        >
                                            {child.label.length > 14
                                                ? child.label.slice(0, 12) + "…"
                                                : child.label}
                                        </text>

                                        {/* Tertiary nodes (grandchildren) */}
                                        {child.children?.map((gc, gi) => {
                                            const tertAngle = subAngle + (gi === 0 ? -15 : 15);
                                            const tert = curvePath(
                                                sub.endX, sub.endY,
                                                tertAngle, tertLength, 0.8,
                                            );
                                            return (
                                                <g key={gc.id}>
                                                    <path
                                                        d={tert.path}
                                                        stroke={branch.color}
                                                        strokeWidth={isHovered ? 2 : 1.5}
                                                        fill="none"
                                                        strokeLinecap="round"
                                                        opacity={isHovered ? 0.8 : 0.5}
                                                        style={{ transition: "all 0.3s ease" }}
                                                    />
                                                    <circle
                                                        cx={tert.endX} cy={tert.endY}
                                                        r={isHovered ? 8 : 6}
                                                        fill={branch.color}
                                                        opacity={isHovered ? 0.85 : 0.6}
                                                        style={{ transition: "all 0.3s ease", cursor: "pointer" }}
                                                        onClick={() =>
                                                            handleNodeClick(gc.id, gc.touchpoint_ids || [])
                                                        }
                                                    />
                                                </g>
                                            );
                                        })}
                                    </g>
                                );
                            })}
                        </g>
                    );
                })}

                {/* Central node — triple concentric */}
                <g>
                    <circle
                        cx={cx} cy={cy} r="38"
                        fill="white" stroke="#475569" strokeWidth="3"
                        filter="url(#mm-glow)"
                    />
                    <circle cx={cx} cy={cy} r="28" fill="#F1F5F9" stroke="#94A3B8" strokeWidth="2" />
                    <circle cx={cx} cy={cy} r="18" fill="#E2E8F0" />
                    <text
                        x={cx} y={cy + 4}
                        textAnchor="middle"
                        fontSize="11" fontWeight="700" fill="#1E293B"
                    >
                        {centerLabel}
                    </text>
                </g>
            </svg>

            {/* Tooltip */}
            {tooltip && (
                <div
                    style={{
                        position: "absolute",
                        left: tooltip.x,
                        top: tooltip.y,
                        background: "#1E293B",
                        color: "white",
                        padding: "5px 10px",
                        borderRadius: 6,
                        fontSize: 12,
                        pointerEvents: "none",
                        zIndex: 10,
                        boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
                        whiteSpace: "nowrap",
                    }}
                >
                    {tooltip.text}
                </div>
            )}
        </div>
    );
}

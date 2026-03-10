import React, { useState, useEffect } from 'react';
import { HelpCircle, X } from 'lucide-react';
import { API } from '../lib/apiConfig';

/**
 * HelpIcon — Contextual help tooltip component (spec §24 UX).
 *
 * Usage:
 *   <HelpIcon slug="compass" />
 *   <HelpIcon slug="coaching" inline />
 *
 * Fetches help text from the help API endpoint.
 * Falls back to a generic message if the API is unavailable.
 */
interface Props {
    /** Page slug matching the backend help registry key */
    slug: string;
    /** Show as inline icon (not floating) */
    inline?: boolean;
    /** Override description (skip API call) */
    description?: string;
    /** Custom class for positioning */
    className?: string;
}

// Local cache to avoid repeat fetches
const _cache: Record<string, { header: string; description: string }> = {};

export default function HelpIcon({ slug, inline, description: overrideDesc, className }: Props) {
    const [open, setOpen] = useState(false);
    const [data, setData] = useState<{ header: string; description: string } | null>(
        overrideDesc ? { header: '', description: overrideDesc } : _cache[slug] ?? null,
    );

    useEffect(() => {
        if (overrideDesc || _cache[slug]) return;
        const controller = new AbortController();
        fetch(`${API.help}/pages/${slug}`, { signal: controller.signal })
            .then(r => r.ok ? r.json() : null)
            .then(json => {
                if (json) {
                    const entry = { header: json.header ?? '', description: json.description ?? '' };
                    _cache[slug] = entry;
                    setData(entry);
                }
            })
            .catch(() => {});
        return () => controller.abort();
    }, [slug, overrideDesc]);

    const toggleOpen = (e: React.MouseEvent) => {
        e.stopPropagation();
        setOpen(prev => !prev);
    };

    return (
        <div className={`relative ${inline ? 'inline-flex' : ''} ${className ?? ''}`}>
            <button
                onClick={toggleOpen}
                aria-label="Page help"
                className="p-1 rounded-full text-gray-400 hover:text-indigo-400 hover:bg-gray-800/50 transition focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
                <HelpCircle size={inline ? 16 : 20} />
            </button>
            {open && data && (
                <>
                    {/* Backdrop */}
                    <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
                    {/* Tooltip */}
                    <div className="absolute z-50 top-full mt-2 right-0 w-80 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-4 text-sm animate-in fade-in slide-in-from-top-1">
                        <div className="flex items-start justify-between mb-2">
                            {data.header && <h4 className="font-semibold text-white pr-4">{data.header}</h4>}
                            <button onClick={() => setOpen(false)} className="text-gray-500 hover:text-gray-300 flex-shrink-0"><X size={14} /></button>
                        </div>
                        <p className="text-gray-300 leading-relaxed">{data.description}</p>
                    </div>
                </>
            )}
        </div>
    );
}

import React, { useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8500";

export interface CollocationEntry {
    phrase: string;
    count?: number;
    pmi?: number;
    type?: "bigram" | "trigram";
}

export default function GlossaryCollocations() {
    const [entries, setEntries] = React.useState<CollocationEntry[]>([]);
    const [loading, setLoading] = React.useState(false);
    const [query, setQuery] = useState("");
    const [maxRows, setMaxRows] = useState(200);
    const [textProbe, setTextProbe] = useState("");

    React.useEffect(() => {
        setLoading(true);
        fetch(`${API_BASE}/api/ontology/v1/phrases?limit=2000`)
            .then(res => res.json())
            .then(data => {
                if (data?.items) {
                    setEntries(data.items as CollocationEntry[]);
                }
            })
            .catch(() => {
                setEntries([]);
            })
            .finally(() => setLoading(false));
    }, []);

    const filtered = useMemo(() => {
        if (!query) return entries;
        const needle = query.toLowerCase();
        return entries.filter(entry => entry.phrase?.toLowerCase().includes(needle));
    }, [entries, query]);

    const hits = useMemo(() => {
        if (!textProbe.trim()) return [];
        const needle = textProbe.toLowerCase();
        return entries
            .filter(entry => needle.includes(entry.phrase.toLowerCase()))
            .map(entry => entry.phrase);
    }, [entries, textProbe]);

    return (
        <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">Collocation Glossary</h2>
                    <p className="text-sm text-gray-500">
                        Collocation phrases extracted from AI data + user interactions.
                    </p>
                </div>
                <div className="text-sm text-gray-500">
                    {loading ? "Loading phrases..." : `${entries.length} phrases loaded`}
                </div>
            </header>

            <div className="mt-4 grid gap-4 md:grid-cols-[2fr_1fr]">
                <div>
                    <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Search</label>
                    <input
                        className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm"
                        placeholder="Search collocation phrases"
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                    />
                </div>
                <div>
                    <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Max rows</label>
                    <input
                        className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm"
                        type="number"
                        min={50}
                        max={2000}
                        value={maxRows}
                        onChange={(event) => setMaxRows(Number(event.target.value))}
                    />
                </div>
            </div>

            <div className="mt-4 overflow-hidden rounded-lg border border-gray-100">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
                        <tr>
                            <th className="px-4 py-2">Phrase</th>
                            <th className="px-4 py-2">Type</th>
                            <th className="px-4 py-2">Count</th>
                            <th className="px-4 py-2">PMI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.slice(0, maxRows).map(entry => (
                            <tr key={entry.phrase} className="border-t border-gray-100">
                                <td className="px-4 py-2 font-medium text-gray-900">{entry.phrase}</td>
                                <td className="px-4 py-2 text-gray-600">{entry.type ?? "-"}</td>
                                <td className="px-4 py-2 text-gray-600">{entry.count ?? 0}</td>
                                <td className="px-4 py-2 text-gray-600">{entry.pmi ?? 0}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="mt-6">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Check your text</label>
                <textarea
                    className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm min-h-[120px]"
                    placeholder="Paste profile text or resume snippet"
                    value={textProbe}
                    onChange={(event) => setTextProbe(event.target.value)}
                />
                {textProbe && (
                    <div className="mt-3 rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
                        <div className="font-semibold">Matched collocations: {hits.length}</div>
                        <div className="mt-2 flex flex-wrap gap-2">
                            {hits.slice(0, 200).map(hit => (
                                <span key={hit} className="rounded-full bg-indigo-50 px-3 py-1 text-xs text-indigo-700">
                                    {hit}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </section>
    );
}

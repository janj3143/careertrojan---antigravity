import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Globe, Search, ExternalLink } from 'lucide-react';

export default function ExaWebIntel() {
    const [query, setQuery] = useState('');
    const [searching, setSearching] = useState(false);

    const handleSearch = async () => {
        setSearching(true);
        // Simulate Exa API call
        setTimeout(() => setSearching(false), 1000);
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🌐 Exa Web Intelligence</h1>
                    <p className="text-slate-400">Web intelligence powered by Exa API</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search the web..."
                            className="flex-1 px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500"
                        />
                        <button
                            onClick={handleSearch}
                            disabled={searching}
                            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg transition flex items-center gap-2"
                        >
                            <Search size={18} />
                            {searching ? 'Searching...' : 'Search'}
                        </button>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-12 text-center">
                    <Globe size={64} className="mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-400">Enter a query to search the web</p>
                </div>
            </div>
        </AdminLayout>
    );
}

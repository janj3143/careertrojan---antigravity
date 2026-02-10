import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { API_BASE } from '../lib/apiConfig';

interface PageTemplateProps {
    title: string;
    subtitle?: string;
    endpoint?: string;
    children?: React.ReactNode;
}

export default function PageTemplate({ title, subtitle, endpoint, children }: PageTemplateProps) {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        if (!endpoint) return;

        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('admin_token');
            const response = await fetch(`${API_BASE}${endpoint}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            setData(result);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (endpoint) {
            fetchData();
        }
    }, [endpoint]);

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white">{title}</h1>
                        {subtitle && <p className="text-slate-400 mt-1">{subtitle}</p>}
                    </div>
                    {endpoint && (
                        <button
                            onClick={fetchData}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded transition"
                        >
                            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                            Refresh
                        </button>
                    )}
                </div>
            </div>

            {error && (
                <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded mb-4">
                    Error: {error}
                </div>
            )}

            {children || (
                <div className="bg-slate-800 rounded-lg p-6">
                    {loading ? (
                        <div className="text-center text-slate-400">Loading...</div>
                    ) : data ? (
                        <pre className="text-sm text-slate-300 overflow-auto max-h-[600px]">
                            {JSON.stringify(data, null, 2)}
                        </pre>
                    ) : (
                        <div className="text-center text-slate-400">No data available</div>
                    )}
                </div>
            )}
        </div>
    );
}

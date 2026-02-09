import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { AlertTriangle, Search } from 'lucide-react';

interface LogEntry {
    timestamp: string;
    level: 'error' | 'warning';
    message: string;
    service: string;
}

export default function LoggingErrors() {
    const [logs] = useState<LogEntry[]>([
        {
            timestamp: new Date().toISOString(),
            level: 'error',
            message: 'Database connection timeout',
            service: 'backend-api'
        }
    ]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">⚠️ Logging & Errors</h1>
                    <p className="text-slate-400">System logs and error tracking</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-slate-800 border-b border-slate-700">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Time</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Level</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Service</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Message</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {logs.map((log, idx) => (
                                <tr key={idx} className="hover:bg-slate-800/50">
                                    <td className="px-6 py-4 text-sm text-slate-300">
                                        {new Date(log.timestamp).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded text-xs ${log.level === 'error' ? 'bg-red-900/30 text-red-400' : 'bg-amber-900/30 text-amber-400'
                                            }`}>
                                            {log.level.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{log.service}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{log.message}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </AdminLayout>
    );
}

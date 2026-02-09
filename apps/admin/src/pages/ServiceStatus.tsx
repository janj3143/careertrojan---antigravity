import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Activity, Database, Server, Cpu, HardDrive, RefreshCw } from 'lucide-react';

interface ServiceHealth {
    name: string;
    status: 'operational' | 'degraded' | 'down';
    uptime: number;
    response_time: number;
    last_check: string;
}

interface SystemMetrics {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
}

export default function ServiceStatus() {
    const [services, setServices] = useState<ServiceHealth[]>([]);
    const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // Update every 30s
        return () => clearInterval(interval);
    }, []);

    const fetchStatus = async () => {
        try {
            const [servicesRes, metricsRes] = await Promise.all([
                fetch('/api/admin/v1/system/health'),
                fetch('/api/admin/v1/system/activity')
            ]);

            if (servicesRes.ok) {
                const data = await servicesRes.json();
                setServices(data.services || []);
            }

            if (metricsRes.ok) {
                const data = await metricsRes.json();
                setMetrics(data);
            }

            setLastUpdate(new Date());
        } catch (err) {
            console.error('Error fetching service status:', err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'operational': return 'bg-green-500';
            case 'degraded': return 'bg-amber-500';
            case 'down': return 'bg-red-500';
            default: return 'bg-slate-500';
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'operational': return 'bg-green-900/30 text-green-400 border-green-700';
            case 'degraded': return 'bg-amber-900/30 text-amber-400 border-amber-700';
            case 'down': return 'bg-red-900/30 text-red-400 border-red-700';
            default: return 'bg-slate-700 text-slate-400';
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">🔧 Service Status</h1>
                        <p className="text-slate-400">Monitor system health and services</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-sm text-slate-400">
                            Last updated: {lastUpdate.toLocaleTimeString()}
                        </div>
                        <button
                            onClick={fetchStatus}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
                        >
                            <RefreshCw size={16} />
                            Refresh
                        </button>
                    </div>
                </div>

                {/* System Metrics */}
                {metrics && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-3">
                                <Cpu className="text-blue-400" size={24} />
                                <div className="text-sm text-slate-300">CPU Usage</div>
                            </div>
                            <div className="text-3xl font-bold text-white mb-2">{metrics.cpu_usage}%</div>
                            <div className="w-full bg-slate-800 rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full transition-all ${metrics.cpu_usage > 80 ? 'bg-red-500' :
                                            metrics.cpu_usage > 60 ? 'bg-amber-500' : 'bg-green-500'
                                        }`}
                                    style={{ width: `${metrics.cpu_usage}%` }}
                                />
                            </div>
                        </div>

                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-3">
                                <Server className="text-green-400" size={24} />
                                <div className="text-sm text-slate-300">Memory Usage</div>
                            </div>
                            <div className="text-3xl font-bold text-white mb-2">{metrics.memory_usage}%</div>
                            <div className="w-full bg-slate-800 rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full transition-all ${metrics.memory_usage > 80 ? 'bg-red-500' :
                                            metrics.memory_usage > 60 ? 'bg-amber-500' : 'bg-green-500'
                                        }`}
                                    style={{ width: `${metrics.memory_usage}%` }}
                                />
                            </div>
                        </div>

                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-3">
                                <HardDrive className="text-amber-400" size={24} />
                                <div className="text-sm text-slate-300">Disk Usage</div>
                            </div>
                            <div className="text-3xl font-bold text-white mb-2">{metrics.disk_usage}%</div>
                            <div className="w-full bg-slate-800 rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full transition-all ${metrics.disk_usage > 80 ? 'bg-red-500' :
                                            metrics.disk_usage > 60 ? 'bg-amber-500' : 'bg-green-500'
                                        }`}
                                    style={{ width: `${metrics.disk_usage}%` }}
                                />
                            </div>
                        </div>

                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-3">
                                <Activity className="text-purple-400" size={24} />
                                <div className="text-sm text-slate-300">Connections</div>
                            </div>
                            <div className="text-3xl font-bold text-white mb-2">{metrics.active_connections}</div>
                            <div className="text-xs text-slate-400">Active connections</div>
                        </div>
                    </div>
                )}

                {/* Services Status */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    <div className="p-6 border-b border-slate-700">
                        <h2 className="text-xl font-bold text-white">Service Health</h2>
                    </div>
                    {loading ? (
                        <div className="text-center py-12 text-slate-400">Loading services...</div>
                    ) : (
                        <table className="w-full">
                            <thead className="bg-slate-800 border-b border-slate-700">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Service</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Uptime</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Response Time</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Last Check</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {services.map((service, idx) => (
                                    <tr key={idx} className="hover:bg-slate-800/50 transition">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-3 h-3 rounded-full ${getStatusColor(service.status)}`} />
                                                <span className="font-medium text-white">{service.name}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex px-2.5 py-0.5 rounded border text-xs font-medium ${getStatusBadge(service.status)}`}>
                                                {service.status.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-300">
                                            {service.uptime.toFixed(2)}%
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-300">
                                            {service.response_time}ms
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-300">
                                            {new Date(service.last_check).toLocaleTimeString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </AdminLayout>
    );
}

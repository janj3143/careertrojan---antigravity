import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Plug, CheckCircle, XCircle, AlertTriangle, Clock, Shield, RefreshCw } from 'lucide-react';

type Environment = 'sandbox' | 'live' | 'test' | 'unknown';

interface APIConfig {
    name: string;
    provider: string;
    endpoint: string;
    environment: Environment;
    status: 'connected' | 'disconnected' | 'error';
    keyPrefix?: string;
    switchedToLiveAt?: string | null;
    lastVerified?: string;
}

const ENV_BADGES: Record<Environment, { label: string; color: string; bgColor: string }> = {
    sandbox: { label: 'SANDBOX', color: 'text-yellow-400', bgColor: 'bg-yellow-400/10 border-yellow-400/30' },
    test: { label: 'TEST', color: 'text-orange-400', bgColor: 'bg-orange-400/10 border-orange-400/30' },
    live: { label: 'LIVE', color: 'text-green-400', bgColor: 'bg-green-400/10 border-green-400/30' },
    unknown: { label: 'UNKNOWN', color: 'text-slate-400', bgColor: 'bg-slate-400/10 border-slate-400/30' },
};

function detectEnvironment(keyPrefix: string | undefined, provider: string): Environment {
    if (!keyPrefix) return 'unknown';
    const lowerKey = keyPrefix.toLowerCase();
    
    // Stripe
    if (provider === 'Stripe') {
        if (lowerKey.startsWith('sk_test') || lowerKey.startsWith('pk_test')) return 'test';
        if (lowerKey.startsWith('sk_live') || lowerKey.startsWith('pk_live')) return 'live';
    }
    // Braintree
    if (provider === 'Braintree') {
        if (lowerKey === 'sandbox') return 'sandbox';
        if (lowerKey === 'production') return 'live';
    }
    // SendGrid / generic
    if (lowerKey.includes('test') || lowerKey.includes('sandbox')) return 'sandbox';
    if (lowerKey.includes('live') || lowerKey.includes('prod')) return 'live';
    
    return 'unknown';
}

export default function APIIntegration() {
    const [apis, setApis] = useState<APIConfig[]>([
        { 
            name: 'Payment Gateway', 
            provider: 'Stripe',
            status: 'connected', 
            endpoint: 'api.stripe.com',
            keyPrefix: 'sk_test_51R7ZBX',
            environment: 'test',
            switchedToLiveAt: null,
            lastVerified: new Date().toISOString()
        },
        { 
            name: 'Primary Payment', 
            provider: 'Braintree',
            status: 'connected', 
            endpoint: 'api.braintreegateway.com',
            keyPrefix: 'sandbox',
            environment: 'sandbox',
            switchedToLiveAt: null,
            lastVerified: new Date().toISOString()
        },
        { 
            name: 'Email Delivery', 
            provider: 'SendGrid',
            status: 'connected', 
            endpoint: 'api.sendgrid.com',
            keyPrefix: 'SG.18HXixP8',
            environment: 'live',
            switchedToLiveAt: '2026-02-15T10:30:00Z',
            lastVerified: new Date().toISOString()
        },
        { 
            name: 'Transactional Email', 
            provider: 'Resend',
            status: 'connected', 
            endpoint: 'api.resend.com',
            keyPrefix: 're_YHpyaFaz',
            environment: 'live',
            switchedToLiveAt: '2026-02-10T14:00:00Z',
            lastVerified: new Date().toISOString()
        },
        { 
            name: 'AI Language Model', 
            provider: 'OpenAI',
            status: 'connected', 
            endpoint: 'api.openai.com',
            keyPrefix: 'sk-proj-LWTHw',
            environment: 'live',
            switchedToLiveAt: '2026-01-20T09:00:00Z',
            lastVerified: new Date().toISOString()
        },
        { 
            name: 'AI Assistant', 
            provider: 'Anthropic (Claude)',
            status: 'connected', 
            endpoint: 'api.anthropic.com',
            keyPrefix: 'sk-ant-api03',
            environment: 'live',
            switchedToLiveAt: '2026-01-25T11:00:00Z',
            lastVerified: new Date().toISOString()
        },
        { 
            name: 'Support Tickets', 
            provider: 'Zendesk',
            status: 'connected', 
            endpoint: 'careertrojan.zendesk.com',
            keyPrefix: '1O3sCfWN',
            environment: 'live',
            switchedToLiveAt: '2026-02-20T16:00:00Z',
            lastVerified: new Date().toISOString()
        },
        { 
            name: 'CRM', 
            provider: 'HubSpot',
            status: 'connected', 
            endpoint: 'api.hubapi.com',
            keyPrefix: 'pat-eu1-d5d1',
            environment: 'live',
            switchedToLiveAt: '2026-02-01T08:00:00Z',
            lastVerified: new Date().toISOString()
        },
    ]);

    const [loading, setLoading] = useState(false);

    const sandboxCount = apis.filter(a => a.environment === 'sandbox' || a.environment === 'test').length;
    const liveCount = apis.filter(a => a.environment === 'live').length;

    const formatDate = (iso: string | null | undefined) => {
        if (!iso) return '—';
        return new Date(iso).toLocaleDateString('en-GB', { 
            day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' 
        });
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">🔌 API Integration</h1>
                        <p className="text-slate-400">Manage external API connections and monitor environment status</p>
                    </div>
                    <button 
                        onClick={() => setLoading(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                        Verify All
                    </button>
                </div>

                {/* Environment Summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                        <div className="text-2xl font-bold text-white">{apis.length}</div>
                        <div className="text-sm text-slate-400">Total APIs</div>
                    </div>
                    <div className="bg-slate-800 border border-green-500/30 rounded-lg p-4">
                        <div className="text-2xl font-bold text-green-400">{liveCount}</div>
                        <div className="text-sm text-slate-400">Live / Production</div>
                    </div>
                    <div className="bg-slate-800 border border-yellow-500/30 rounded-lg p-4">
                        <div className="text-2xl font-bold text-yellow-400">{sandboxCount}</div>
                        <div className="text-sm text-slate-400">Sandbox / Test</div>
                    </div>
                    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                        <div className="text-2xl font-bold text-white">{apis.filter(a => a.status === 'connected').length}</div>
                        <div className="text-sm text-slate-400">Connected</div>
                    </div>
                </div>

                {/* Warning Banner for Sandbox APIs */}
                {sandboxCount > 0 && (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 flex items-start gap-3">
                        <AlertTriangle className="text-yellow-400 flex-shrink-0 mt-0.5" size={20} />
                        <div>
                            <div className="font-semibold text-yellow-400">Sandbox/Test APIs Detected</div>
                            <div className="text-sm text-yellow-200/70">
                                {sandboxCount} API{sandboxCount > 1 ? 's are' : ' is'} running in sandbox/test mode. 
                                Switch to live keys before production launch.
                            </div>
                        </div>
                    </div>
                )}

                {/* API Table */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-slate-800">
                            <tr>
                                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Provider</th>
                                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Purpose</th>
                                <th className="text-center px-4 py-3 text-sm font-semibold text-slate-300">Environment</th>
                                <th className="text-center px-4 py-3 text-sm font-semibold text-slate-300">Status</th>
                                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">
                                    <div className="flex items-center gap-1">
                                        <Clock size={14} />
                                        Switched to Live
                                    </div>
                                </th>
                                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Key Prefix</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {apis.map((api, idx) => {
                                const envBadge = ENV_BADGES[api.environment];
                                return (
                                    <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-4 py-4">
                                            <div className="font-medium text-white">{api.provider}</div>
                                            <div className="text-xs text-slate-500">{api.endpoint}</div>
                                        </td>
                                        <td className="px-4 py-4 text-slate-300">{api.name}</td>
                                        <td className="px-4 py-4 text-center">
                                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${envBadge.bgColor} ${envBadge.color}`}>
                                                {api.environment === 'live' && <Shield size={12} />}
                                                {envBadge.label}
                                            </span>
                                        </td>
                                        <td className="px-4 py-4 text-center">
                                            {api.status === 'connected' ? (
                                                <CheckCircle className="inline text-green-400" size={20} />
                                            ) : api.status === 'error' ? (
                                                <XCircle className="inline text-red-400" size={20} />
                                            ) : (
                                                <XCircle className="inline text-slate-500" size={20} />
                                            )}
                                        </td>
                                        <td className="px-4 py-4">
                                            {api.switchedToLiveAt ? (
                                                <span className="text-sm text-green-300">{formatDate(api.switchedToLiveAt)}</span>
                                            ) : (
                                                <span className="text-sm text-slate-500 italic">Not yet</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-4">
                                            <code className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">
                                                {api.keyPrefix || '—'}...
                                            </code>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {/* Legend */}
                <div className="flex items-center gap-6 text-sm text-slate-400">
                    <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${ENV_BADGES.live.bgColor} ${ENV_BADGES.live.color}`}>LIVE</span>
                        Production ready
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${ENV_BADGES.sandbox.bgColor} ${ENV_BADGES.sandbox.color}`}>SANDBOX</span>
                        Test environment
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${ENV_BADGES.test.bgColor} ${ENV_BADGES.test.color}`}>TEST</span>
                        Test keys
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
}

import { useEffect, useMemo, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { AlertTriangle, CheckCircle, Mail, Plug } from 'lucide-react';

type IntegrationStatusResponse = {
    providers?: Record<string, {
        configured?: boolean;
        mode?: string;
    }>;
    payment_gateways?: Record<string, {
        configured?: boolean;
        mode?: string;
        is_live?: boolean;
    }>;
};

export default function APIIntegration() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusData, setStatusData] = useState<IntegrationStatusResponse | null>(null);
    const [sendingReminderFor, setSendingReminderFor] = useState<string | null>(null);
    const [reminderMessage, setReminderMessage] = useState<string | null>(null);

    useEffect(() => {
        void loadStatus();
    }, []);

    const loadStatus = async () => {
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('admin_token');
            const response = await fetch('/api/admin/v1/integrations/status', {
                headers: token ? { Authorization: `Bearer ${token}` } : undefined,
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Failed to load integration status (${response.status})`);
            }

            const data = await response.json();
            setStatusData(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load integration status');
        } finally {
            setLoading(false);
        }
    };

    const paymentGateways = useMemo(() => {
        const gateways = statusData?.payment_gateways || {};
        return [
            {
                key: 'stripe',
                name: 'Stripe',
                endpoint: 'api.stripe.com',
                ...gateways.stripe,
            },
            {
                key: 'braintree',
                name: 'Braintree',
                endpoint: 'api.braintreegateway.com',
                ...gateways.braintree,
            },
        ];
    }, [statusData]);

    const sendReminder = async (provider: 'stripe' | 'braintree') => {
        setSendingReminderFor(provider);
        setReminderMessage(null);

        try {
            const token = localStorage.getItem('admin_token');
            const response = await fetch('/api/admin/v1/integrations/reminders/non-live', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                credentials: 'include',
                body: JSON.stringify({ provider }),
            });

            const payload = await response.json().catch(() => null);
            if (!response.ok) {
                throw new Error(payload?.detail || `Failed to send reminder (${response.status})`);
            }

            const target = payload?.target ? ` to ${payload.target}` : '';
            setReminderMessage(`Reminder queued for ${provider}${target}`);
        } catch (err) {
            setReminderMessage(err instanceof Error ? err.message : 'Failed to send reminder');
        } finally {
            setSendingReminderFor(null);
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🔌 API Integration</h1>
                    <p className="text-slate-400">Manage external API connections</p>
                </div>

                {error && (
                    <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg p-4">
                        {error}
                    </div>
                )}

                {reminderMessage && (
                    <div className="bg-blue-900/30 border border-blue-700 text-blue-300 rounded-lg p-4">
                        {reminderMessage}
                    </div>
                )}

                <div className="grid grid-cols-1 gap-4">
                    {paymentGateways.map((api) => {
                        const configured = !!api.configured;
                        const mode = api.mode || 'unknown';
                        const isLive = mode === 'live';
                        const showReminder = configured && !isLive;

                        return (
                        <div key={api.key} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-white">{api.name}</h3>
                                    <div className="text-sm text-slate-400">{api.endpoint}</div>
                                    <div className="mt-2 text-sm">
                                        <span className={`inline-flex px-2.5 py-1 rounded border ${
                                            isLive
                                                ? 'bg-green-900/30 text-green-300 border-green-700'
                                                : 'bg-amber-900/30 text-amber-300 border-amber-700'
                                        }`}>
                                            Mode: {mode.toUpperCase()}
                                        </span>
                                    </div>
                                </div>

                                {configured ? (
                                    isLive ? (
                                        <CheckCircle className="text-green-400" size={24} />
                                    ) : (
                                        <AlertTriangle className="text-amber-400" size={24} />
                                    )
                                ) : (
                                    <Plug className="text-slate-500" size={24} />
                                )}
                            </div>

                            {showReminder && (
                                <div className="mt-4 flex items-center justify-between gap-4 border-t border-slate-700 pt-4">
                                    <div className="text-sm text-amber-300">
                                        Non-live credentials detected. Send admin reminder to switch to live credentials.
                                    </div>
                                    <button
                                        onClick={() => sendReminder(api.key as 'stripe' | 'braintree')}
                                        disabled={sendingReminderFor === api.key}
                                        className="inline-flex items-center gap-2 px-3 py-2 rounded bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white text-sm"
                                    >
                                        <Mail size={14} />
                                        {sendingReminderFor === api.key ? 'Sending...' : 'Send Admin Reminder'}
                                    </button>
                                </div>
                            )}
                        </div>
                    )})}
                </div>

                {loading && <div className="text-slate-400">Loading integration status...</div>}
            </div>
        </AdminLayout>
    );
}

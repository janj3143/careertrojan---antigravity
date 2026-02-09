import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Plug, CheckCircle, XCircle } from 'lucide-react';

export default function APIIntegration() {
    const [apis] = useState([
        { name: 'Stripe', status: 'connected', endpoint: 'api.stripe.com' },
        { name: 'SendGrid', status: 'connected', endpoint: 'api.sendgrid.com' }
    ]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🔌 API Integration</h1>
                    <p className="text-slate-400">Manage external API connections</p>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {apis.map((api, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-white">{api.name}</h3>
                                    <div className="text-sm text-slate-400">{api.endpoint}</div>
                                </div>
                                <CheckCircle className="text-green-400" size={24} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AdminLayout>
    );
}

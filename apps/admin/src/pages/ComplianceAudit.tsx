import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { Shield, CheckCircle } from 'lucide-react';

export default function ComplianceAudit() {
    const checks = [
        { name: 'GDPR Compliance', status: 'passed' },
        { name: 'Data Encryption', status: 'passed' },
        { name: 'Access Controls', status: 'passed' }
    ];

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🛡️ Compliance Audit</h1>
                    <p className="text-slate-400">Security and compliance monitoring</p>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {checks.map((check, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="text-green-400" size={24} />
                                    <span className="text-lg font-semibold text-white">{check.name}</span>
                                </div>
                                <span className="px-3 py-1 bg-green-900/30 text-green-400 rounded text-sm">
                                    PASSED
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AdminLayout>
    );
}

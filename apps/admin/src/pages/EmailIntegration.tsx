import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { Mail, Send } from 'lucide-react';

export default function EmailIntegration() {
    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">📧 Email Integration</h1>
                    <p className="text-slate-400">Configure email services and templates</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <Mail className="text-blue-400" size={32} />
                        <div>
                            <h3 className="text-lg font-bold text-white">SendGrid</h3>
                            <div className="text-sm text-green-400">Connected</div>
                        </div>
                    </div>
                    <button className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded transition">
                        <Send size={18} />
                        Test Email
                    </button>
                </div>
            </div>
        </AdminLayout>
    );
}

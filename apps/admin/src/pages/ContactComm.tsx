import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { MessageSquare, Users } from 'lucide-react';

export default function ContactComm() {
    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">💬 Contact Communication</h1>
                    <p className="text-slate-400">Manage contact and communication settings</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-12 text-center">
                    <MessageSquare size={64} className="mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-400">Communication management interface</p>
                </div>
            </div>
        </AdminLayout>
    );
}

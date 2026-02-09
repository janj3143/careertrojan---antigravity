import React from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../components/AdminLayout';
import { BarChart3, ArrowRight } from 'lucide-react';

export default function UnifiedAnalytics() {
    const navigate = useNavigate();

    return (
        <AdminLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold text-white mb-6">📊 Unified Analytics</h1>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-8 text-center">
                    <BarChart3 size={64} className="mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-400 mb-4">This page redirects to the main Analytics dashboard</p>
                    <button
                        onClick={() => navigate('/admin/analytics')}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded transition"
                    >
                        Go to Analytics
                        <ArrowRight size={18} />
                    </button>
                </div>
            </div>
        </AdminLayout>
    );
}

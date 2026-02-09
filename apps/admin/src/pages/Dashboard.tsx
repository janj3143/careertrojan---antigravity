import React from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../components/AdminLayout';
import { LayoutDashboard, ArrowRight } from 'lucide-react';

export default function Dashboard() {
    const navigate = useNavigate();

    return (
        <AdminLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold text-white mb-6">📊 Dashboard</h1>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-8 text-center">
                    <LayoutDashboard size={64} className="mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-400 mb-4">This is a generic dashboard page</p>
                    <p className="text-sm text-slate-500 mb-6">For the main admin dashboard, click below</p>
                    <button
                        onClick={() => navigate('/admin')}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 rounded transition"
                    >
                        Go to Admin Home
                        <ArrowRight size={18} />
                    </button>
                </div>
            </div>
        </AdminLayout>
    );
}

import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { FileText, Plus } from 'lucide-react';

export default function RequirementsMgmt() {
    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">📋 Requirements Management</h1>
                        <p className="text-slate-400">Manage system requirements and specifications</p>
                    </div>
                    <button className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded transition">
                        <Plus size={18} />
                        Add Requirement
                    </button>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-12 text-center">
                    <FileText size={64} className="mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-400">No requirements defined</p>
                </div>
            </div>
        </AdminLayout>
    );
}

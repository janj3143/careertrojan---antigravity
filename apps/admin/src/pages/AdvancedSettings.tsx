import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { Settings, Save } from 'lucide-react';

export default function AdvancedSettings() {
    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">⚙️ Advanced Settings</h1>
                    <p className="text-slate-400">Configure advanced system settings</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <h3 className="text-lg font-bold text-white mb-4">System Configuration</h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Max Upload Size (MB)
                            </label>
                            <input
                                type="number"
                                defaultValue={10}
                                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Session Timeout (minutes)
                            </label>
                            <input
                                type="number"
                                defaultValue={30}
                                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                            />
                        </div>
                        <button className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded transition">
                            <Save size={18} />
                            Save Settings
                        </button>
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
}

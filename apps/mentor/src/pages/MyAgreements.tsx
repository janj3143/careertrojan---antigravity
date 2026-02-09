import React from 'react';
import MentorLayout from '../components/MentorLayout';
import { FileText, Download, Eye } from 'lucide-react';

interface Agreement {
    id: string;
    mentee_name: string;
    package_name: string;
    start_date: string;
    end_date: string;
    status: 'active' | 'completed' | 'pending';
    signed_date?: string;
}

export default function MyAgreements() {
    const agreements: Agreement[] = [
        {
            id: '1',
            mentee_name: 'Mentee #12345',
            package_name: 'Career Transition Package',
            start_date: '2026-01-15',
            end_date: '2026-04-15',
            status: 'active',
            signed_date: '2026-01-14'
        }
    ];

    const getStatusBadge = (status: string) => {
        const styles = {
            active: 'bg-green-900/30 text-green-400 border-green-700',
            completed: 'bg-blue-900/30 text-blue-400 border-blue-700',
            pending: 'bg-amber-900/30 text-amber-400 border-amber-700'
        };
        return styles[status as keyof typeof styles];
    };

    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold text-white mb-6">📄 My Agreements</h1>

                <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-slate-800 border-b border-slate-700">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Mentee</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Package</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Start Date</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">End Date</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {agreements.map(agreement => (
                                <tr key={agreement.id} className="hover:bg-slate-800/50 transition">
                                    <td className="px-6 py-4 text-sm text-white font-medium">{agreement.mentee_name}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{agreement.package_name}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">
                                        {new Date(agreement.start_date).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-300">
                                        {new Date(agreement.end_date).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex px-2.5 py-0.5 rounded text-xs font-medium border ${getStatusBadge(agreement.status)}`}>
                                            {agreement.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex gap-2">
                                            <button className="p-2 hover:bg-slate-700 rounded transition" title="View">
                                                <Eye size={16} className="text-slate-400" />
                                            </button>
                                            <button className="p-2 hover:bg-slate-700 rounded transition" title="Download">
                                                <Download size={16} className="text-slate-400" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </MentorLayout>
    );
}

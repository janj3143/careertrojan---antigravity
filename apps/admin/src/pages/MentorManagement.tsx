import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Briefcase, Search, CheckCircle, XCircle, Clock, Eye } from 'lucide-react';

interface MentorApplication {
    application_id: string;
    user_email: string;
    full_name: string;
    expertise: string[];
    experience_years: number;
    status: 'pending' | 'approved' | 'rejected';
    submitted_at: string;
    linkedin_url?: string;
}

export default function MentorManagement() {
    const [applications, setApplications] = useState<MentorApplication[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('pending');

    useEffect(() => {
        fetchApplications();
    }, []);

    const fetchApplications = async () => {
        try {
            const response = await fetch('/api/mentorship/v1/applications/pending');
            if (response.ok) {
                const data = await response.json();
                setApplications(data.applications || []);
            }
        } catch (err) {
            console.error('Error fetching applications:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (applicationId: string) => {
        try {
            await fetch(`/api/admin/mentor-applications/${applicationId}/approve`, {
                method: 'POST'
            });
            await fetchApplications();
        } catch (err) {
            console.error('Error approving application:', err);
        }
    };

    const handleReject = async (applicationId: string) => {
        try {
            await fetch(`/api/admin/mentor-applications/${applicationId}/reject`, {
                method: 'POST'
            });
            await fetchApplications();
        } catch (err) {
            console.error('Error rejecting application:', err);
        }
    };

    const filteredApplications = applications.filter(app =>
        statusFilter === 'all' || app.status === statusFilter
    );

    const getStatusBadge = (status: string) => {
        const styles = {
            pending: 'bg-amber-900/30 text-amber-400 border-amber-700',
            approved: 'bg-green-900/30 text-green-400 border-green-700',
            rejected: 'bg-red-900/30 text-red-400 border-red-700'
        };
        return styles[status as keyof typeof styles];
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">🎓 Mentor Management</h1>
                        <p className="text-slate-400">Review and approve mentor applications</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-amber-400">
                                {applications.filter(a => a.status === 'pending').length}
                            </div>
                            <div className="text-xs text-slate-400">Pending</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green-400">
                                {applications.filter(a => a.status === 'approved').length}
                            </div>
                            <div className="text-xs text-slate-400">Approved</div>
                        </div>
                    </div>
                </div>

                {/* Filters */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                    <div className="flex gap-2">
                        {['pending', 'approved', 'rejected', 'all'].map(status => (
                            <button
                                key={status}
                                onClick={() => setStatusFilter(status)}
                                className={`px-4 py-2 rounded transition ${statusFilter === status
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                    }`}
                            >
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Applications List */}
                <div className="space-y-4">
                    {loading ? (
                        <div className="text-center py-12 text-slate-400">Loading applications...</div>
                    ) : filteredApplications.length === 0 ? (
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-12 text-center">
                            <Briefcase size={48} className="mx-auto mb-4 text-slate-600" />
                            <p className="text-slate-400">No {statusFilter} applications</p>
                        </div>
                    ) : (
                        filteredApplications.map(app => (
                            <div key={app.application_id} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1">{app.full_name}</h3>
                                        <p className="text-slate-400">{app.user_email}</p>
                                    </div>
                                    <span className={`inline-flex px-3 py-1 rounded border text-sm font-medium ${getStatusBadge(app.status)}`}>
                                        {app.status.toUpperCase()}
                                    </span>
                                </div>

                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div>
                                        <div className="text-sm text-slate-400 mb-1">Experience</div>
                                        <div className="text-white font-semibold">{app.experience_years} years</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-400 mb-1">Submitted</div>
                                        <div className="text-white font-semibold">
                                            {new Date(app.submitted_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                </div>

                                <div className="mb-4">
                                    <div className="text-sm text-slate-400 mb-2">Expertise</div>
                                    <div className="flex flex-wrap gap-2">
                                        {app.expertise.map((skill, idx) => (
                                            <span key={idx} className="px-3 py-1 bg-blue-900/30 text-blue-400 rounded text-sm">
                                                {skill}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {app.status === 'pending' && (
                                    <div className="flex gap-3 pt-4 border-t border-slate-700">
                                        <button
                                            onClick={() => handleApprove(app.application_id)}
                                            className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 rounded transition"
                                        >
                                            <CheckCircle size={18} />
                                            Approve
                                        </button>
                                        <button
                                            onClick={() => handleReject(app.application_id)}
                                            className="flex items-center gap-2 px-6 py-2 bg-red-600 hover:bg-red-700 rounded transition"
                                        >
                                            <XCircle size={18} />
                                            Reject
                                        </button>
                                        <button className="flex items-center gap-2 px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded transition">
                                            <Eye size={18} />
                                            View Details
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </AdminLayout>
    );
}

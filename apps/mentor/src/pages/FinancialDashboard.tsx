import React, { useState, useEffect } from 'react';
import MentorLayout from '../components/MentorLayout';
import { useMentorAuth } from '../context/MentorAuthContext';
import { DollarSign, TrendingUp, Clock, CheckCircle, AlertCircle, Download } from 'lucide-react';

interface Invoice {
    invoice_id: string;
    mentee_anonymous_name: string;
    session_date: string;
    amount: number;
    mentor_portion: number;
    platform_fee: number;
    status: 'pending' | 'paid' | 'held' | 'released';
    paid_date?: string;
}

export default function FinancialDashboard() {
    const { user } = useMentorAuth();
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'paid' | 'pending' | 'held'>('all');

    useEffect(() => {
        if (user?.id) {
            fetchFinancials();
        }
    }, [user]);

    const fetchFinancials = async () => {
        try {
            setLoading(true);
            // Get mentor profile first
            const profileRes = await fetch(`/api/mentor/profile-by-user/${user?.id}`);
            if (!profileRes.ok) throw new Error('Failed to fetch profile');
            const profile = await profileRes.json();

            // Get invoices from mentorship API
            const invoicesRes = await fetch(`/api/mentorship/v1/invoices/mentor/${profile.mentor_profile_id}`);
            if (invoicesRes.ok) {
                const data = await invoicesRes.json();
                setInvoices(data.invoices || []);
            }
        } catch (err) {
            console.error('Error fetching financials:', err);
        } finally {
            setLoading(false);
        }
    };

    const filteredInvoices = invoices.filter(inv =>
        filter === 'all' || inv.status === filter
    );

    const totalEarnings = invoices
        .filter(inv => inv.status === 'paid' || inv.status === 'released')
        .reduce((sum, inv) => sum + inv.mentor_portion, 0);

    const pendingEarnings = invoices
        .filter(inv => inv.status === 'pending')
        .reduce((sum, inv) => sum + inv.mentor_portion, 0);

    const heldEarnings = invoices
        .filter(inv => inv.status === 'held')
        .reduce((sum, inv) => sum + inv.mentor_portion, 0);

    const getStatusBadge = (status: string) => {
        const styles = {
            paid: 'bg-green-900/30 text-green-400 border-green-700',
            released: 'bg-green-900/30 text-green-400 border-green-700',
            pending: 'bg-amber-900/30 text-amber-400 border-amber-700',
            held: 'bg-red-900/30 text-red-400 border-red-700'
        };
        return styles[status as keyof typeof styles] || styles.pending;
    };

    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">💰 Financial Dashboard</h1>
                    <p className="text-slate-400">Track your earnings, invoices, and payouts</p>
                </div>

                {/* Financial Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 border border-green-700/50 rounded-lg p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <CheckCircle className="text-green-400" size={24} />
                            <div className="text-sm text-green-300">Total Earnings</div>
                        </div>
                        <div className="text-3xl font-bold text-white">£{totalEarnings.toFixed(2)}</div>
                        <div className="text-xs text-green-400 mt-1">Paid & Released</div>
                    </div>

                    <div className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border border-amber-700/50 rounded-lg p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <Clock className="text-amber-400" size={24} />
                            <div className="text-sm text-amber-300">Pending</div>
                        </div>
                        <div className="text-3xl font-bold text-white">£{pendingEarnings.toFixed(2)}</div>
                        <div className="text-xs text-amber-400 mt-1">Awaiting Payment</div>
                    </div>

                    <div className="bg-gradient-to-br from-red-900/40 to-red-800/20 border border-red-700/50 rounded-lg p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <AlertCircle className="text-red-400" size={24} />
                            <div className="text-sm text-red-300">On Hold</div>
                        </div>
                        <div className="text-3xl font-bold text-white">£{heldEarnings.toFixed(2)}</div>
                        <div className="text-xs text-red-400 mt-1">Escrow Period</div>
                    </div>

                    <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border border-blue-700/50 rounded-lg p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <TrendingUp className="text-blue-400" size={24} />
                            <div className="text-sm text-blue-300">This Month</div>
                        </div>
                        <div className="text-3xl font-bold text-white">£0.00</div>
                        <div className="text-xs text-blue-400 mt-1">Current Period</div>
                    </div>
                </div>

                {/* Filters & Actions */}
                <div className="flex items-center justify-between">
                    <div className="flex gap-2">
                        <button
                            onClick={() => setFilter('all')}
                            className={`px-4 py-2 rounded transition ${filter === 'all'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                }`}
                        >
                            All ({invoices.length})
                        </button>
                        <button
                            onClick={() => setFilter('paid')}
                            className={`px-4 py-2 rounded transition ${filter === 'paid'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                }`}
                        >
                            Paid
                        </button>
                        <button
                            onClick={() => setFilter('pending')}
                            className={`px-4 py-2 rounded transition ${filter === 'pending'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                }`}
                        >
                            Pending
                        </button>
                        <button
                            onClick={() => setFilter('held')}
                            className={`px-4 py-2 rounded transition ${filter === 'held'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                }`}
                        >
                            On Hold
                        </button>
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition">
                        <Download size={16} />
                        Export CSV
                    </button>
                </div>

                {/* Invoices Table */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-800 border-b border-slate-700">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Invoice ID</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Mentee</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Session Date</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Amount</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Your Portion</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Paid Date</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {loading ? (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-8 text-center text-slate-400">
                                            Loading invoices...
                                        </td>
                                    </tr>
                                ) : filteredInvoices.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-8 text-center text-slate-400">
                                            <DollarSign size={48} className="mx-auto mb-2 text-slate-600" />
                                            <p>No invoices found</p>
                                            <p className="text-sm mt-1">Complete sessions to see your earnings here</p>
                                        </td>
                                    </tr>
                                ) : (
                                    filteredInvoices.map((invoice) => (
                                        <tr key={invoice.invoice_id} className="hover:bg-slate-800/50 transition">
                                            <td className="px-6 py-4 text-sm text-slate-300 font-mono">
                                                {invoice.invoice_id.slice(0, 8)}...
                                            </td>
                                            <td className="px-6 py-4 text-sm text-white font-medium">
                                                {invoice.mentee_anonymous_name}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                {new Date(invoice.session_date).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                £{invoice.amount.toFixed(2)}
                                            </td>
                                            <td className="px-6 py-4 text-sm font-semibold text-green-400">
                                                £{invoice.mentor_portion.toFixed(2)}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium border ${getStatusBadge(invoice.status)}`}>
                                                    {invoice.status.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                {invoice.paid_date ? new Date(invoice.paid_date).toLocaleDateString() : '-'}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Payment Info */}
                <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="text-blue-400 mt-0.5" size={20} />
                        <div className="text-sm text-blue-300">
                            <p className="font-semibold mb-1">Payment Schedule</p>
                            <p>Earnings are released 7 days after session completion. Payouts are processed monthly on the 1st.</p>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="text-center text-sm text-slate-500 pt-4 border-t border-slate-700">
                    💰 CareerTrojan Mentor Portal | Financial Management
                </div>
            </div>
        </MentorLayout>
    );
}

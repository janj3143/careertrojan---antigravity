import React, { useState, useEffect } from 'react';
import MentorLayout from '../components/MentorLayout';
import { useMentorAuth } from '../context/MentorAuthContext';
import { Package, Plus, Edit, Trash2, DollarSign, Clock, CheckCircle } from 'lucide-react';

interface ServicePackage {
    package_id: string;
    package_name: string;
    description: string;
    session_count: number;
    session_duration: number;
    price_per_session: number;
    total_price: number;
    is_active: boolean;
}

export default function ServicePackages() {
    const { user } = useMentorAuth();
    const [packages, setPackages] = useState<ServicePackage[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);

    const [formData, setFormData] = useState({
        package_name: '',
        description: '',
        session_count: 4,
        session_duration: 60,
        price_per_session: 100
    });

    useEffect(() => {
        if (user?.id) {
            fetchPackages();
        }
    }, [user]);

    const fetchPackages = async () => {
        try {
            setLoading(true);
            const profileRes = await fetch(`/api/mentor/profile-by-user/${user?.id}`);
            const profile = await profileRes.json();

            const packagesRes = await fetch(`/api/mentor/${profile.mentor_profile_id}/packages`);
            const data = await packagesRes.json();
            setPackages(data.packages || []);
        } catch (err) {
            console.error('Error fetching packages:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const profileRes = await fetch(`/api/mentor/profile-by-user/${user?.id}`);
            const profile = await profileRes.json();

            const response = await fetch(`/api/mentor/${profile.mentor_profile_id}/packages`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                await fetchPackages();
                setShowCreateForm(false);
                setFormData({
                    package_name: '',
                    description: '',
                    session_count: 4,
                    session_duration: 60,
                    price_per_session: 100
                });
            }
        } catch (err) {
            console.error('Error creating package:', err);
        }
    };

    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">📦 Service Packages</h1>
                        <p className="text-slate-400">Define your mentorship offerings and pricing</p>
                    </div>
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition"
                    >
                        <Plus size={20} />
                        Create Package
                    </button>
                </div>

                {showCreateForm && (
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <h2 className="text-xl font-bold text-white mb-4">Create New Package</h2>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Package Name</label>
                                <input
                                    type="text"
                                    value={formData.package_name}
                                    onChange={(e) => setFormData({ ...formData, package_name: e.target.value })}
                                    required
                                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white"
                                    placeholder="e.g., Career Transition Coaching"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    required
                                    rows={3}
                                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white"
                                    placeholder="Describe what's included in this package..."
                                />
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">Sessions</label>
                                    <input
                                        type="number"
                                        value={formData.session_count}
                                        onChange={(e) => setFormData({ ...formData, session_count: parseInt(e.target.value) })}
                                        min="1"
                                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">Duration (min)</label>
                                    <input
                                        type="number"
                                        value={formData.session_duration}
                                        onChange={(e) => setFormData({ ...formData, session_duration: parseInt(e.target.value) })}
                                        min="15"
                                        step="15"
                                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">Price/Session (£)</label>
                                    <input
                                        type="number"
                                        value={formData.price_per_session}
                                        onChange={(e) => setFormData({ ...formData, price_per_session: parseFloat(e.target.value) })}
                                        min="0"
                                        step="0.01"
                                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white"
                                    />
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <button type="submit" className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded transition">
                                    Create Package
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowCreateForm(false)}
                                    className="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded transition"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {loading ? (
                        <div className="col-span-2 text-center py-12 text-slate-400">Loading packages...</div>
                    ) : packages.length === 0 ? (
                        <div className="col-span-2 text-center py-12">
                            <Package size={48} className="mx-auto mb-4 text-slate-600" />
                            <p className="text-slate-400">No service packages yet</p>
                            <p className="text-sm text-slate-500 mt-2">Create your first package to start offering mentorship services</p>
                        </div>
                    ) : (
                        packages.map((pkg) => (
                            <div key={pkg.package_id} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h3 className="text-xl font-bold text-white">{pkg.package_name}</h3>
                                        <span className={`inline-block px-2 py-1 rounded text-xs mt-2 ${pkg.is_active ? 'bg-green-900/30 text-green-400' : 'bg-slate-700 text-slate-400'
                                            }`}>
                                            {pkg.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </div>
                                    <div className="flex gap-2">
                                        <button className="p-2 hover:bg-slate-800 rounded transition">
                                            <Edit size={16} className="text-slate-400" />
                                        </button>
                                        <button className="p-2 hover:bg-slate-800 rounded transition">
                                            <Trash2 size={16} className="text-red-400" />
                                        </button>
                                    </div>
                                </div>
                                <p className="text-slate-300 text-sm mb-4">{pkg.description}</p>
                                <div className="grid grid-cols-3 gap-4 mb-4">
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-white">{pkg.session_count}</div>
                                        <div className="text-xs text-slate-400">Sessions</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-white">{pkg.session_duration}m</div>
                                        <div className="text-xs text-slate-400">Duration</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-green-400">£{pkg.price_per_session}</div>
                                        <div className="text-xs text-slate-400">Per Session</div>
                                    </div>
                                </div>
                                <div className="border-t border-slate-700 pt-4">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-slate-400">Total Package Price</span>
                                        <span className="text-xl font-bold text-white">£{pkg.total_price.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </MentorLayout>
    );
}

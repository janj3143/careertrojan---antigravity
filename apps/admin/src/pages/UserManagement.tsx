import React, { useState, useEffect } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Users, Search, Filter, Edit, Trash2, Ban, CheckCircle } from 'lucide-react';

interface User {
    user_id: string;
    email: string;
    full_name: string;
    role: 'user' | 'mentor' | 'admin';
    status: 'active' | 'suspended' | 'pending';
    created_at: string;
    last_login?: string;
}

export default function UserManagement() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState<string>('all');

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const response = await fetch('/api/admin/v1/users');
            if (response.ok) {
                const data = await response.json();
                setUsers(data.users || []);
            }
        } catch (err) {
            console.error('Error fetching users:', err);
        } finally {
            setLoading(false);
        }
    };

    const filteredUsers = users.filter(user => {
        const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.full_name?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesRole = roleFilter === 'all' || user.role === roleFilter;
        return matchesSearch && matchesRole;
    });

    const getStatusBadge = (status: string) => {
        const styles = {
            active: 'bg-green-900/30 text-green-400 border-green-700',
            suspended: 'bg-red-900/30 text-red-400 border-red-700',
            pending: 'bg-amber-900/30 text-amber-400 border-amber-700'
        };
        return styles[status as keyof typeof styles] || styles.pending;
    };

    const getRoleBadge = (role: string) => {
        const styles = {
            admin: 'bg-red-900/30 text-red-400',
            mentor: 'bg-blue-900/30 text-blue-400',
            user: 'bg-slate-700 text-slate-300'
        };
        return styles[role as keyof typeof styles] || styles.user;
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">👥 User Management</h1>
                        <p className="text-slate-400">Manage user accounts and permissions</p>
                    </div>
                    <div className="text-2xl font-bold text-white">{filteredUsers.length} users</div>
                </div>

                {/* Filters */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search by email or name..."
                                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <Filter size={18} className="text-slate-400" />
                            <select
                                value={roleFilter}
                                onChange={(e) => setRoleFilter(e.target.value)}
                                className="flex-1 px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                            >
                                <option value="all">All Roles</option>
                                <option value="user">Users</option>
                                <option value="mentor">Mentors</option>
                                <option value="admin">Admins</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Users Table */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    {loading ? (
                        <div className="text-center py-12 text-slate-400">Loading users...</div>
                    ) : (
                        <table className="w-full">
                            <thead className="bg-slate-800 border-b border-slate-700">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">User</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Role</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Created</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Last Login</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {filteredUsers.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                                            No users found
                                        </td>
                                    </tr>
                                ) : (
                                    filteredUsers.map(user => (
                                        <tr key={user.user_id} className="hover:bg-slate-800/50 transition">
                                            <td className="px-6 py-4">
                                                <div className="font-medium text-white">{user.full_name || 'N/A'}</div>
                                                <div className="text-sm text-slate-400">{user.email}</div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex px-2.5 py-0.5 rounded text-xs font-medium ${getRoleBadge(user.role)}`}>
                                                    {user.role.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex px-2.5 py-0.5 rounded text-xs font-medium border ${getStatusBadge(user.status)}`}>
                                                    {user.status.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                {new Date(user.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex gap-2">
                                                    <button className="p-2 hover:bg-slate-700 rounded transition" title="Edit">
                                                        <Edit size={16} className="text-blue-400" />
                                                    </button>
                                                    <button className="p-2 hover:bg-slate-700 rounded transition" title="Suspend">
                                                        <Ban size={16} className="text-amber-400" />
                                                    </button>
                                                    <button className="p-2 hover:bg-slate-700 rounded transition" title="Delete">
                                                        <Trash2 size={16} className="text-red-400" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </AdminLayout>
    );
}

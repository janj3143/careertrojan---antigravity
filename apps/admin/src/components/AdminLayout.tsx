import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAdminAuth } from '../context/AdminAuthContext';
import { LogOut, Home, Settings, Users, Database, BarChart3, Wrench } from 'lucide-react';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
    const { user, logout } = useAdminAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/admin/login');
    };

    return (
        <div className="min-h-screen bg-slate-900 text-white">
            {/* Top Nav */}
            <nav className="bg-slate-800 border-b border-slate-700 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <h1 className="text-xl font-bold text-blue-400">CareerTrojan Admin</h1>
                        <div className="flex gap-4">
                            <Link to="/admin" className="flex items-center gap-2 hover:text-blue-400 transition">
                                <Home size={18} />
                                <span>Home</span>
                            </Link>
                            <Link to="/admin/users" className="flex items-center gap-2 hover:text-blue-400 transition">
                                <Users size={18} />
                                <span>Users</span>
                            </Link>
                            <Link to="/admin/analytics" className="flex items-center gap-2 hover:text-blue-400 transition">
                                <BarChart3 size={18} />
                                <span>Analytics</span>
                            </Link>
                            <Link to="/admin/tools/datasets" className="flex items-center gap-2 hover:text-blue-400 transition">
                                <Database size={18} />
                                <span>Data</span>
                            </Link>
                            <Link to="/admin/tools/api-explorer" className="flex items-center gap-2 hover:text-blue-400 transition">
                                <Wrench size={18} />
                                <span>Tools</span>
                            </Link>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-slate-400">{user?.email}</span>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition"
                        >
                            <LogOut size={16} />
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="p-6">
                {children}
            </main>
        </div>
    );
}

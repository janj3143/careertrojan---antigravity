import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMentorAuth } from '../context/MentorAuthContext';
import { LogOut, Home, Users, DollarSign, Calendar, MessageSquare, Settings } from 'lucide-react';

export default function MentorLayout({ children }: { children: React.ReactNode }) {
    const { user, logout } = useMentorAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/mentor/login');
    };

    return (
        <div className="min-h-screen bg-slate-800 text-white">
            {/* Top Nav */}
            <nav className="bg-slate-900 border-b border-slate-700 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-3">
                            <img
                                src="/logo.png"
                                alt="CareerTrojan Logo"
                                className="h-8 w-auto"
                                onError={(e) => {
                                    // Fallback if logo doesn't exist
                                    e.currentTarget.style.display = 'none';
                                }}
                            />
                            <h1 className="text-xl font-bold text-green-400">CareerTrojan Mentor</h1>
                        </div>
                        <div className="flex gap-4">
                            <Link to="/mentor" className="flex items-center gap-2 hover:text-green-400 transition">
                                <Home size={18} />
                                <span>Dashboard</span>
                            </Link>
                            <Link to="/mentor/agreements" className="flex items-center gap-2 hover:text-green-400 transition">
                                <Users size={18} />
                                <span>Mentees</span>
                            </Link>
                            <Link to="/mentor/financials" className="flex items-center gap-2 hover:text-green-400 transition">
                                <DollarSign size={18} />
                                <span>Financials</span>
                            </Link>
                            <Link to="/mentor/calendar" className="flex items-center gap-2 hover:text-green-400 transition">
                                <Calendar size={18} />
                                <span>Calendar</span>
                            </Link>
                            <Link to="/mentor/communication" className="flex items-center gap-2 hover:text-green-400 transition">
                                <MessageSquare size={18} />
                                <span>Messages</span>
                            </Link>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-slate-400">{user?.full_name || user?.email}</span>
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

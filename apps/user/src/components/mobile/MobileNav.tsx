import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    Menu, X, Home, LayoutDashboard, FileText, Briefcase, Brain,
    Users, Award, CreditCard, User, LogOut, BarChart3, Rocket
} from 'lucide-react';

const NAV_ITEMS = [
    { to: '/', icon: Home, label: 'Home', auth: false },
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', auth: true },
    { to: '/resume', icon: FileText, label: 'Resume', auth: true },
    { to: '/umarketu', icon: Briefcase, label: 'MarketU', auth: true },
    { to: '/coaching', icon: Brain, label: 'Coaching', auth: true },
    { to: '/mentorship', icon: Users, label: 'Mentors', auth: true },
    { to: '/dual-career', icon: Rocket, label: 'Dual Career', auth: true },
    { to: '/rewards', icon: Award, label: 'Rewards', auth: true },
    { to: '/visuals', icon: BarChart3, label: 'Analytics', auth: true },
    { to: '/payment', icon: CreditCard, label: 'Billing', auth: true },
    { to: '/profile', icon: User, label: 'Profile', auth: true },
];

export default function MobileNav() {
    const [open, setOpen] = useState(false);
    const location = useLocation();
    const { isAuthenticated, user, logout } = useAuth();

    // Close on route change
    useEffect(() => { setOpen(false); }, [location.pathname]);

    // Prevent body scroll when menu is open
    useEffect(() => {
        document.body.style.overflow = open ? 'hidden' : '';
        return () => { document.body.style.overflow = ''; };
    }, [open]);

    const filteredItems = NAV_ITEMS.filter(item =>
        item.auth ? isAuthenticated : true
    );

    return (
        <>
            {/* Top Bar — visible on mobile only */}
            <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-indigo-900 text-white shadow-lg">
                <div className="flex items-center justify-between px-4 h-14">
                    <Link to="/" className="font-bold text-lg tracking-tight" onClick={() => setOpen(false)}>
                        CareerTrojan
                    </Link>
                    <button
                        onClick={() => setOpen(!open)}
                        className="p-2 rounded-lg hover:bg-indigo-800 transition-colors touch-target"
                        aria-label={open ? 'Close menu' : 'Open menu'}
                        aria-expanded={open}
                    >
                        {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                    </button>
                </div>
            </header>

            {/* Overlay */}
            {open && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-40 animate-fade-in"
                    onClick={() => setOpen(false)}
                    aria-hidden="true"
                />
            )}

            {/* Slide-out Panel */}
            <nav
                className={`lg:hidden fixed top-14 left-0 bottom-0 w-72 bg-white z-50 shadow-2xl transform transition-transform duration-300 ease-out overflow-y-auto ${
                    open ? 'translate-x-0' : '-translate-x-full'
                }`}
                aria-label="Mobile navigation"
            >
                {/* User info */}
                {isAuthenticated && user && (
                    <div className="px-4 py-4 bg-gray-50 border-b">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                                <User className="w-5 h-5 text-indigo-600" />
                            </div>
                            <div className="min-w-0">
                                <p className="text-sm font-semibold text-gray-900 truncate">
                                    {user.full_name || user.email}
                                </p>
                                <p className="text-xs text-gray-500 truncate">{user.email}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Nav links */}
                <div className="py-2">
                    {filteredItems.map((item) => {
                        const active = location.pathname === item.to;
                        const Icon = item.icon;
                        return (
                            <Link
                                key={item.to}
                                to={item.to}
                                className={`flex items-center gap-3 px-4 py-3 text-sm font-medium transition-colors touch-target ${
                                    active
                                        ? 'bg-indigo-50 text-indigo-700 border-r-2 border-indigo-600'
                                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                                }`}
                            >
                                <Icon className="w-5 h-5 flex-shrink-0" />
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </div>

                {/* Auth actions */}
                <div className="border-t px-4 py-3">
                    {isAuthenticated ? (
                        <button
                            onClick={logout}
                            className="flex items-center gap-3 w-full px-2 py-3 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors touch-target"
                        >
                            <LogOut className="w-5 h-5" />
                            <span>Sign Out</span>
                        </button>
                    ) : (
                        <div className="space-y-2">
                            <Link to="/login" className="block w-full text-center py-3 text-sm font-semibold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors touch-target">
                                Sign In
                            </Link>
                            <Link to="/register" className="block w-full text-center py-3 text-sm font-semibold border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors touch-target">
                                Create Account
                            </Link>
                        </div>
                    )}
                </div>
            </nav>

            {/* Spacer for fixed header on mobile */}
            <div className="lg:hidden h-14" />
        </>
    );
}

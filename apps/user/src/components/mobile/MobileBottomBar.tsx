import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Briefcase, Brain, FileText, User } from 'lucide-react';

const BOTTOM_TABS = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
    { to: '/umarketu', icon: Briefcase, label: 'Jobs' },
    { to: '/coaching', icon: Brain, label: 'Coach' },
    { to: '/resume', icon: FileText, label: 'CV' },
    { to: '/profile', icon: User, label: 'Profile' },
];

export default function MobileBottomBar() {
    const location = useLocation();

    return (
        <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 safe-area-bottom" aria-label="Quick navigation">
            <div className="flex items-center justify-around h-16">
                {BOTTOM_TABS.map((tab) => {
                    const active = location.pathname === tab.to;
                    const Icon = tab.icon;
                    return (
                        <Link
                            key={tab.to}
                            to={tab.to}
                            className={`flex flex-col items-center justify-center flex-1 h-full gap-0.5 touch-target transition-colors ${
                                active ? 'text-indigo-600' : 'text-gray-400 hover:text-gray-600'
                            }`}
                        >
                            <Icon className={`w-5 h-5 ${active ? 'stroke-[2.5px]' : ''}`} />
                            <span className={`text-[10px] font-medium ${active ? 'font-semibold' : ''}`}>
                                {tab.label}
                            </span>
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}

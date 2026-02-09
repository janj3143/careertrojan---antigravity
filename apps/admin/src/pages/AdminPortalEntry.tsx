import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, ArrowRight } from 'lucide-react';

export default function AdminPortalEntry() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-red-900/20 to-slate-900 flex items-center justify-center p-6">
            <div className="w-full max-w-md text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-red-600 rounded-full mb-6">
                    <Shield className="text-white" size={40} />
                </div>
                <h1 className="text-4xl font-bold text-white mb-4">Admin Portal</h1>
                <p className="text-slate-400 mb-8">Secure administrative access to CareerTrojan</p>
                <button
                    onClick={() => navigate('/admin/login')}
                    className="inline-flex items-center gap-2 px-8 py-4 bg-red-600 hover:bg-red-700 rounded-lg text-white font-semibold transition"
                >
                    Sign In
                    <ArrowRight size={20} />
                </button>
            </div>
        </div>
    );
}

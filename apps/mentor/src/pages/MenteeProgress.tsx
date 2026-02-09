import React, { useState } from 'react';
import MentorLayout from '../components/MentorLayout';
import { TrendingUp, Target, CheckCircle, AlertCircle } from 'lucide-react';

interface Mentee {
    id: string;
    name: string;
    goal: string;
    progress: number;
    sessions_completed: number;
    next_session: string;
    status: 'on-track' | 'needs-attention' | 'completed';
}

export default function MenteeProgress() {
    const [mentees, setMentees] = useState<Mentee[]>([
        {
            id: '1',
            name: 'Mentee #12345',
            goal: 'Career transition to Product Management',
            progress: 65,
            sessions_completed: 4,
            next_session: '2026-02-15',
            status: 'on-track'
        }
    ]);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'on-track': return 'text-green-400 bg-green-900/30 border-green-700';
            case 'needs-attention': return 'text-amber-400 bg-amber-900/30 border-amber-700';
            case 'completed': return 'text-blue-400 bg-blue-900/30 border-blue-700';
            default: return 'text-slate-400 bg-slate-800 border-slate-700';
        }
    };

    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold text-white mb-6">📊 Mentee Progress</h1>

                <div className="grid grid-cols-1 gap-6">
                    {mentees.map(mentee => (
                        <div key={mentee.id} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h2 className="text-xl font-bold text-white mb-2">{mentee.name}</h2>
                                    <p className="text-slate-400 flex items-center gap-2">
                                        <Target size={16} />
                                        {mentee.goal}
                                    </p>
                                </div>
                                <span className={`px-3 py-1 rounded border text-sm ${getStatusColor(mentee.status)}`}>
                                    {mentee.status.replace('-', ' ').toUpperCase()}
                                </span>
                            </div>

                            <div className="mb-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm text-slate-400">Overall Progress</span>
                                    <span className="text-sm font-semibold text-white">{mentee.progress}%</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-3">
                                    <div
                                        className="bg-green-600 h-3 rounded-full transition-all"
                                        style={{ width: `${mentee.progress}%` }}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4 mb-4">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-white">{mentee.sessions_completed}</div>
                                    <div className="text-xs text-slate-400">Sessions Done</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-white">{new Date(mentee.next_session).toLocaleDateString()}</div>
                                    <div className="text-xs text-slate-400">Next Session</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-400">
                                        <TrendingUp className="inline" size={24} />
                                    </div>
                                    <div className="text-xs text-slate-400">Trending</div>
                                </div>
                            </div>

                            <div className="flex gap-3">
                                <button className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition">
                                    View Details
                                </button>
                                <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded transition">
                                    Add Note
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </MentorLayout>
    );
}

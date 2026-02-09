import React, { useState } from 'react';
import MentorLayout from '../components/MentorLayout';
import { Calendar as CalendarIcon, Plus, Clock, Video, MapPin } from 'lucide-react';

interface Session {
    id: string;
    mentee_name: string;
    date: string;
    time: string;
    duration: number;
    type: 'video' | 'in-person' | 'phone';
    status: 'scheduled' | 'completed' | 'cancelled';
}

export default function SessionsCalendar() {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [sessions, setSessions] = useState<Session[]>([
        {
            id: '1',
            mentee_name: 'Mentee #12345',
            date: '2026-02-10',
            time: '14:00',
            duration: 60,
            type: 'video',
            status: 'scheduled'
        }
    ]);

    const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
    const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay();

    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];

    const getSessionsForDate = (day: number) => {
        const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        return sessions.filter(s => s.date === dateStr);
    };

    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">📅 Sessions Calendar</h1>
                        <p className="text-slate-400">Schedule and manage your mentorship sessions</p>
                    </div>
                    <button className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition">
                        <Plus size={20} />
                        Schedule Session
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Calendar */}
                    <div className="lg:col-span-2 bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-white">
                                {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
                            </h2>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setCurrentDate(new Date(currentDate.setMonth(currentDate.getMonth() - 1)))}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded transition"
                                >
                                    ←
                                </button>
                                <button
                                    onClick={() => setCurrentDate(new Date())}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded transition"
                                >
                                    Today
                                </button>
                                <button
                                    onClick={() => setCurrentDate(new Date(currentDate.setMonth(currentDate.getMonth() + 1)))}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded transition"
                                >
                                    →
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-7 gap-2">
                            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                                <div key={day} className="text-center text-sm font-semibold text-slate-400 py-2">
                                    {day}
                                </div>
                            ))}

                            {Array.from({ length: firstDayOfMonth }).map((_, i) => (
                                <div key={`empty-${i}`} className="aspect-square" />
                            ))}

                            {Array.from({ length: daysInMonth }).map((_, i) => {
                                const day = i + 1;
                                const daySessions = getSessionsForDate(day);
                                const isToday = day === new Date().getDate() &&
                                    currentDate.getMonth() === new Date().getMonth() &&
                                    currentDate.getFullYear() === new Date().getFullYear();

                                return (
                                    <div
                                        key={day}
                                        className={`aspect-square border rounded-lg p-2 cursor-pointer transition ${isToday
                                                ? 'border-green-500 bg-green-900/20'
                                                : 'border-slate-700 hover:border-slate-600 hover:bg-slate-800'
                                            }`}
                                    >
                                        <div className={`text-sm font-semibold ${isToday ? 'text-green-400' : 'text-white'}`}>
                                            {day}
                                        </div>
                                        {daySessions.length > 0 && (
                                            <div className="mt-1">
                                                {daySessions.map(session => (
                                                    <div
                                                        key={session.id}
                                                        className="text-xs bg-blue-900/30 text-blue-400 rounded px-1 py-0.5 mb-1 truncate"
                                                    >
                                                        {session.time}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Upcoming Sessions */}
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <h2 className="text-xl font-bold text-white mb-4">Upcoming Sessions</h2>
                        <div className="space-y-3">
                            {sessions.length === 0 ? (
                                <div className="text-center py-8 text-slate-400">
                                    <CalendarIcon size={48} className="mx-auto mb-2 text-slate-600" />
                                    <p>No sessions scheduled</p>
                                </div>
                            ) : (
                                sessions.map(session => (
                                    <div key={session.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="font-semibold text-white">{session.mentee_name}</div>
                                            {session.type === 'video' && <Video size={16} className="text-blue-400" />}
                                            {session.type === 'in-person' && <MapPin size={16} className="text-green-400" />}
                                        </div>
                                        <div className="text-sm text-slate-400 space-y-1">
                                            <div className="flex items-center gap-2">
                                                <CalendarIcon size={14} />
                                                {new Date(session.date).toLocaleDateString()}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Clock size={14} />
                                                {session.time} ({session.duration}min)
                                            </div>
                                        </div>
                                        <div className="mt-3 flex gap-2">
                                            <button className="flex-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded text-sm transition">
                                                Join
                                            </button>
                                            <button className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-sm transition">
                                                Reschedule
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </MentorLayout>
    );
}

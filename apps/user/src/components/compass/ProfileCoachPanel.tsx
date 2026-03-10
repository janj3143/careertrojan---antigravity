import React, { useState, useCallback } from 'react';
import { MessageCircle, Send, X, Lightbulb, CheckCircle } from 'lucide-react';
import { API } from '../../lib/apiConfig';

interface Turn {
    role: 'coach' | 'user';
    content: string;
    mirrored?: string[];
}

/**
 * ProfileCoachPanel — Embeddable guided reflection coach (spec §10-§12).
 *
 * UI States:
 *  1. Idle (CTA button visible)
 *  2. Active conversation (start → respond loop)
 *  3. Finished (differentiator summary shown)
 *
 * Props:
 *  - userId / resumeId — context for the session
 *  - userName — optional personalisation
 *  - onComplete — callback with differentiator bullets
 */
interface Props {
    userId: string;
    resumeId: string;
    userName?: string;
    onComplete?: (differentiators: string[]) => void;
}

function authHeaders() {
    const token = localStorage.getItem('token');
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}

export default function ProfileCoachPanel({ userId, resumeId, userName, onComplete }: Props) {
    const [open, setOpen] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [turns, setTurns] = useState<Turn[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [finished, setFinished] = useState(false);
    const [differentiators, setDifferentiators] = useState<string[]>([]);

    const startSession = useCallback(async () => {
        setOpen(true);
        setLoading(true);
        try {
            const res = await fetch(`${API.profileCoach}/start`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ user_id: userId, resume_id: resumeId, user_name: userName }),
            });
            const data = await res.json();
            setSessionId(data.session_id);
            if (data.question) {
                setTurns([{ role: 'coach', content: data.question }]);
            }
        } catch (e) {
            console.error('Profile Coach start failed', e);
        } finally {
            setLoading(false);
        }
    }, [userId, resumeId, userName]);

    const sendAnswer = useCallback(async () => {
        if (!input.trim() || !sessionId) return;
        const answer = input.trim();
        setInput('');
        setTurns(prev => [...prev, { role: 'user', content: answer }]);
        setLoading(true);
        try {
            const res = await fetch(`${API.profileCoach}/respond`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ user_id: userId, session_id: sessionId, answer }),
            });
            const data = await res.json();
            if (data.stop_detected) {
                // Auto-finish
                await finishSession();
                return;
            }
            const turn: Turn = { role: 'coach', content: data.question ?? '', mirrored: data.mirrored_points };
            setTurns(prev => [...prev, turn]);
        } catch (e) {
            console.error('Profile Coach respond failed', e);
        } finally {
            setLoading(false);
        }
    }, [input, sessionId, userId]);

    const finishSession = useCallback(async () => {
        if (!sessionId) return;
        setLoading(true);
        try {
            const res = await fetch(`${API.profileCoach}/finish`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ user_id: userId, session_id: sessionId }),
            });
            const data = await res.json();
            setDifferentiators(data.differentiators ?? []);
            setFinished(true);
            onComplete?.(data.differentiators ?? []);
        } catch (e) {
            console.error('Profile Coach finish failed', e);
        } finally {
            setLoading(false);
        }
    }, [sessionId, userId, onComplete]);

    if (!open) {
        return (
            <button
                onClick={startSession}
                className="flex items-center gap-2 px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg transition"
            >
                <Lightbulb size={18} />
                <span className="font-medium">Start reflecting — let's find the gold in your story</span>
            </button>
        );
    }

    return (
        <div className="bg-gray-900 border border-gray-700 rounded-2xl shadow-xl max-w-lg w-full">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-800">
                <div className="flex items-center gap-2">
                    <MessageCircle size={18} className="text-indigo-400" />
                    <span className="font-semibold text-white">Profile Coach</span>
                </div>
                <button onClick={() => { setOpen(false); }} className="text-gray-500 hover:text-gray-300"><X size={18} /></button>
            </div>

            {/* Chat area */}
            <div className="p-4 max-h-96 overflow-y-auto space-y-3">
                {turns.map((t, i) => (
                    <div key={i} className={`flex ${t.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-xl px-4 py-2 text-sm ${
                            t.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-200'
                        }`}>
                            {t.mirrored && t.mirrored.length > 0 && (
                                <div className="mb-2 space-y-1">
                                    {t.mirrored.map((m, j) => (
                                        <div key={j} className="text-indigo-300 text-xs">• {m}</div>
                                    ))}
                                </div>
                            )}
                            {t.content}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-800 rounded-xl px-4 py-2 text-sm text-gray-400 animate-pulse">Thinking…</div>
                    </div>
                )}
            </div>

            {/* Differentiator summary */}
            {finished && differentiators.length > 0 && (
                <div className="p-4 border-t border-gray-800 space-y-2">
                    <div className="flex items-center gap-2 text-emerald-400 font-medium text-sm">
                        <CheckCircle size={16} /> Your Differentiators
                    </div>
                    {differentiators.map((d, i) => (
                        <div key={i} className="text-sm text-gray-300 pl-6">• {d}</div>
                    ))}
                </div>
            )}

            {/* Input */}
            {!finished && (
                <div className="p-3 border-t border-gray-800 flex gap-2">
                    <input
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && sendAnswer()}
                        placeholder="Share your thoughts…"
                        className="flex-1 px-4 py-2 rounded-lg bg-gray-800 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        disabled={loading}
                    />
                    <button onClick={sendAnswer} disabled={loading || !input.trim()} className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition">
                        <Send size={16} className="text-white" />
                    </button>
                    <button onClick={finishSession} disabled={loading} className="px-3 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white text-sm disabled:opacity-50 transition">
                        Finish
                    </button>
                </div>
            )}
        </div>
    );
}

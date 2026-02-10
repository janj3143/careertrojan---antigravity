import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { API } from '../lib/apiConfig';

interface UserProfile {
    id: string;
    username: string;
    email: string;
    role: string;
    createdAt: string;
    lastLogin: string;
}

interface SessionSummary {
    totalSessions: number;
    totalPageViews: number;
    lastSessionDate: string;
    averageDuration: string;
}

interface ResumeData {
    filename: string;
    uploadDate: string;
    parsedSkills: string[];
    matchCount: number;
}

interface AIMatchSummary {
    topMatches: { title: string; company: string; score: number }[];
    lastUpdated: string;
}

interface CoachingHistory {
    totalSessions: number;
    lastSessionDate: string;
    topicsDiscussed: string[];
}

interface MentorshipSummary {
    activeMentors: number;
    completedSessions: number;
    nextSession: string | null;
}

export default function ConsolidationPage() {
    const { user, token } = useAuth();
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [sessions, setSessions] = useState<SessionSummary | null>(null);
    const [resume, setResume] = useState<ResumeData | null>(null);
    const [matches, setMatches] = useState<AIMatchSummary | null>(null);
    const [coaching, setCoaching] = useState<CoachingHistory | null>(null);
    const [mentorship, setMentorship] = useState<MentorshipSummary | null>(null);
    const [loading, setLoading] = useState(true);

    const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

    useEffect(() => {
        loadConsolidatedData();
    }, []);

    async function loadConsolidatedData() {
        setLoading(true);
        try {
            const [profileRes, sessionsRes, resumeRes, matchesRes, coachingRes, mentorRes] = await Promise.all([
                fetch(`${API.user}/profile`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
                fetch(`${API.user}/sessions/summary`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
                fetch(`${API.user}/resume/latest`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
                fetch(`${API.user}/matches/summary`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
                fetch(`${API.coaching}/history`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
                fetch(`${API.mentorship}/summary`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
            ]);
            setProfile(profileRes);
            setSessions(sessionsRes);
            setResume(resumeRes);
            setMatches(matchesRes);
            setCoaching(coachingRes);
            setMentorship(mentorRes);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b px-6 py-4">
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">My CareerTrojan — Everything in One Place</h1>
                        <p className="text-sm text-gray-500">Consolidated view of your profile, history, matches, and activity</p>
                    </div>
                    <span className="text-sm text-gray-400">
                        {user?.username || 'User'}
                    </span>
                </div>
            </header>

            <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
                {loading && (
                    <div className="text-center py-12 text-gray-400 animate-pulse">
                        Loading your consolidated data...
                    </div>
                )}

                {/* Profile Card */}
                <Card title="👤 Profile" subtitle="Your account details">
                    {profile ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <InfoItem label="Username" value={profile.username} />
                            <InfoItem label="Email" value={profile.email} />
                            <InfoItem label="Role" value={profile.role} />
                            <InfoItem label="Member Since" value={new Date(profile.createdAt).toLocaleDateString()} />
                        </div>
                    ) : (
                        <EmptyState message="Profile data not available" />
                    )}
                </Card>

                {/* Session History */}
                <Card title="📅 Session History" subtitle="Your login and activity history">
                    {sessions ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <InfoItem label="Total Sessions" value={String(sessions.totalSessions)} />
                            <InfoItem label="Page Views" value={String(sessions.totalPageViews)} />
                            <InfoItem label="Avg Duration" value={sessions.averageDuration} />
                            <InfoItem label="Last Active" value={sessions.lastSessionDate} />
                        </div>
                    ) : (
                        <EmptyState message="No session history yet — it will appear after your first full session" />
                    )}
                </Card>

                {/* Resume & Skills */}
                <Card title="📄 Resume & Skills" subtitle="Your latest resume analysis">
                    {resume ? (
                        <div>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                                <InfoItem label="File" value={resume.filename} />
                                <InfoItem label="Uploaded" value={resume.uploadDate} />
                                <InfoItem label="Matches Found" value={String(resume.matchCount)} />
                            </div>
                            {resume.parsedSkills.length > 0 && (
                                <div>
                                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Extracted Skills</p>
                                    <div className="flex flex-wrap gap-2">
                                        {resume.parsedSkills.map((skill) => (
                                            <span key={skill} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                                                {skill}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <EmptyState message="Upload a resume to see your skills analysis" />
                    )}
                </Card>

                {/* AI Job Matches */}
                <Card title="🤖 AI Job Matches" subtitle="Your best career matches from our AI engine">
                    {matches && matches.topMatches.length > 0 ? (
                        <div className="space-y-2">
                            {matches.topMatches.map((m, i) => (
                                <div key={i} className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-3">
                                    <div>
                                        <p className="font-medium text-gray-800">{m.title}</p>
                                        <p className="text-sm text-gray-500">{m.company}</p>
                                    </div>
                                    <div className="text-right">
                                        <span className={`text-lg font-bold ${m.score >= 80 ? 'text-green-600' : m.score >= 60 ? 'text-yellow-600' : 'text-gray-400'}`}>
                                            {m.score}%
                                        </span>
                                        <p className="text-xs text-gray-400">match</p>
                                    </div>
                                </div>
                            ))}
                            <p className="text-xs text-gray-400 text-right">Last updated: {matches.lastUpdated}</p>
                        </div>
                    ) : (
                        <EmptyState message="No AI matches yet — upload your resume and let the engine work" />
                    )}
                </Card>

                {/* Coaching History */}
                <Card title="🎯 Coaching Hub" subtitle="Your career coaching journey">
                    {coaching ? (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            <InfoItem label="Sessions" value={String(coaching.totalSessions)} />
                            <InfoItem label="Last Session" value={coaching.lastSessionDate} />
                            <div>
                                <p className="text-xs text-gray-500 uppercase tracking-wide">Topics Covered</p>
                                <p className="text-sm text-gray-700">{coaching.topicsDiscussed.join(', ') || 'None yet'}</p>
                            </div>
                        </div>
                    ) : (
                        <EmptyState message="Start a coaching session to see your history here" />
                    )}
                </Card>

                {/* Mentorship Summary */}
                <Card title="🎓 Mentorship" subtitle="Your mentorship connections and progress">
                    {mentorship ? (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            <InfoItem label="Active Mentors" value={String(mentorship.activeMentors)} />
                            <InfoItem label="Completed Sessions" value={String(mentorship.completedSessions)} />
                            <InfoItem label="Next Session" value={mentorship.nextSession || 'Not scheduled'} />
                        </div>
                    ) : (
                        <EmptyState message="Visit the Mentorship Marketplace to get matched" />
                    )}
                </Card>

                {/* Data Transparency Notice */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
                    <p className="font-semibold mb-1">🔒 Your Data, Your Control</p>
                    <p>
                        All your activity, uploads, and interactions are stored securely and used to improve your
                        AI-powered career recommendations. Your data is duplicated across two secure locations
                        to prevent loss. You can request a full data export at any time.
                    </p>
                </div>
            </main>
        </div>
    );
}

/* Reusable sub-components */

function Card({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
    return (
        <section className="bg-white rounded-xl shadow-sm border p-6">
            <div className="mb-4">
                <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
                <p className="text-sm text-gray-400">{subtitle}</p>
            </div>
            {children}
        </section>
    );
}

function InfoItem({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
            <p className="text-sm font-medium text-gray-800">{value}</p>
        </div>
    );
}

function EmptyState({ message }: { message: string }) {
    return <p className="text-sm text-gray-400 italic">{message}</p>;
}

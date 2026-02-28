
import React, { useState, useEffect } from 'react';
import { ApiConfig, generateQuestions, reviewAnswer, generateStarStories, detectBlockers, submitInterviewLearningFeedback, getCompanyBriefing, CompanyBriefingResponse } from '../lib/api';
import { AlertCircle, Plus, CheckCircle, Brain, Target, MessageSquare } from 'lucide-react';

// Configuration
const API_CONFIG: ApiConfig = { baseUrl: "http://localhost:8600" };

type Tab = 'overview' | 'questions' | 'practice' | 'star';

export default function CoachingHub() {
    const [activeTab, setActiveTab] = useState<Tab>('overview');
    const [loading, setLoading] = useState(false);

    // Context Loading State
    const [resumeContext, setResumeContext] = useState<any>(null);
    const [jobContext, setJobContext] = useState<any>({
        title: "Target Role (Not Set)",
        description: "Please select a job in UMarketU or upload a Job Description."
    });

    // State for Blocker Integration
    const [blockers, setBlockers] = useState<any[]>([]);
    const [blockerStats, setBlockerStats] = useState<any>(null);

    // State for Questions & Practice
    const [questions, setQuestions] = useState<string[]>([]);
    const [qType, setQType] = useState("General competency");
    const [practiceQ, setPracticeQ] = useState("");
    const [practiceA, setPracticeA] = useState("");
    const [feedback, setFeedback] = useState<any>(null);
    const [feedbackSaved, setFeedbackSaved] = useState<string | null>(null);
    const [companyTarget, setCompanyTarget] = useState('');
    const [companyBriefing, setCompanyBriefing] = useState<CompanyBriefingResponse | null>(null);
    const [companyLoading, setCompanyLoading] = useState(false);
    const [companyError, setCompanyError] = useState<string | null>(null);

    // Initialize & Load Data
    useEffect(() => {
        loadResume();
    }, []);

    const loadResume = async () => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return; // Wait for login

            const res = await fetch(`${API_CONFIG.baseUrl}/resume`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                // Pick the first resume if available
                if (data.data?.resumes?.length > 0) {
                    // Prefer the most recent one or parsed result
                    const r = data.data.resumes[0];
                    setResumeContext(r.parsed_result || r);
                }
            }
        } catch (e) {
            console.error("Failed to load resume context", e);
        }
    }

    // Trigger blocker analysis when context changes
    useEffect(() => {
        if (resumeContext && jobContext.title !== "Target Role (Not Set)") {
            analyzeBlockers();
        }
    }, [resumeContext, jobContext]);

    const analyzeBlockers = async () => {
        try {
            const result = await detectBlockers(API_CONFIG, {
                jd_text: jobContext.description,
                resume_data: resumeContext || {}
            });
            setBlockers(result.blockers || []);
            setBlockerStats({
                total: result.total_blockers,
                critical: result.critical_count,
                impact: result.overall_impact
            });
        } catch (e) {
            console.error("Blocker detection failed", e);
        }
    };

    const handleGenerateQuestions = async () => {
        setLoading(true);
        try {
            const qs = await generateQuestions(API_CONFIG, {
                question_type: qType,
                count: 5,
                resume: resumeContext || {},
                job: jobContext
            });
            setQuestions(qs);
        } catch (e) {
            console.error("Failed to generate questions", e);
            alert("Failed to generate questions");
        }
        setLoading(false);
    };

    const handleReview = async () => {
        if (!practiceQ || !practiceA) return;
        setLoading(true);
        setFeedbackSaved(null);
        try {
            const fb = await reviewAnswer(API_CONFIG, {
                question: practiceQ,
                answer: practiceA,
                resume: resumeContext,
                job: jobContext
            });
            setFeedback(fb);
        } catch (e) {
            alert("Feedback failed");
        }
        setLoading(false);
    };

    const markQuestionUsefulness = async (question: string, helpful: boolean) => {
        try {
            await submitInterviewLearningFeedback(API_CONFIG, {
                question_type: qType,
                question,
                helpful,
                resume: resumeContext,
                job: jobContext,
            });
        } catch (e) {
            console.error('Failed to save question feedback', e);
        }
    };

    const markAnswerFeedback = async (helpful: boolean) => {
        if (!practiceQ || !feedback) return;
        try {
            await submitInterviewLearningFeedback(API_CONFIG, {
                question_type: qType,
                question: practiceQ,
                helpful,
                answer_score: typeof feedback?.score === 'number' ? feedback.score : undefined,
                resume: resumeContext,
                job: jobContext,
            });
            setFeedbackSaved(helpful ? 'Thanks — this coaching was marked helpful.' : 'Saved — we will improve this coaching path.');
        } catch (e) {
            console.error('Failed to save answer feedback', e);
            setFeedbackSaved('Could not save feedback just now.');
        }
    };

    const handleCompanyResearch = async () => {
        const company_name = companyTarget.trim();
        if (!company_name) {
            setCompanyError('Enter a target company first.');
            return;
        }
        setCompanyLoading(true);
        setCompanyError(null);
        try {
            const result = await getCompanyBriefing(API_CONFIG, {
                company_name,
                resume: resumeContext || {},
                job: jobContext || {},
                max_profile_files: 300,
            });
            setCompanyBriefing(result);
        } catch (e: any) {
            setCompanyError(e?.message || 'Company research failed.');
        }
        setCompanyLoading(false);
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                    <Brain className="w-8 h-8 text-indigo-600" />
                    Coaching Hub
                </h1>
                <p className="text-gray-600 mt-2">AI-driven interview preparation and career gap analysis.</p>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200 mb-6">
                {[
                    { id: 'overview', label: '🔎 Blocker & Overview' },
                    { id: 'questions', label: '❓ Interview Questions' },
                    { id: 'practice', label: '🗣️ Practice' },
                    // { id: 'star', label: '⭐ STAR Stories' }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as Tab)}
                        className={`px-6 py-3 font-medium text-sm transition-colors ${activeTab === tab.id
                            ? 'border-b-2 border-indigo-600 text-indigo-600'
                            : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 min-h-[500px] p-6">

                {/* TAB: OVERVIEW & BLOCKERS */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                                <h3 className="font-semibold text-blue-900">Target Role</h3>
                                <p className="text-blue-700">{jobContext.title}</p>
                            </div>
                            <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                                <h3 className="font-semibold text-green-900">Fit Score</h3>
                                <p className="text-2xl font-bold text-green-700">
                                    {blockerStats ? Math.round(100 - (blockerStats.impact * 10)) : '--'}%
                                </p>
                            </div>
                            <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                                <h3 className="font-semibold text-red-900">Critical Blockers</h3>
                                <p className="text-2xl font-bold text-red-700">
                                    {blockerStats?.critical ?? 0}
                                </p>
                            </div>
                        </div>

                        <h2 className="text-xl font-bold mt-8 mb-4 flex items-center gap-2">
                            <AlertCircle className="w-5 h-5 text-amber-500" />
                            Detected Blockers
                        </h2>

                        {blockers.length === 0 ? (
                            <div className="text-center py-10 text-gray-500">
                                No blockers detected! You are a great match.
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {blockers.map((blocker, idx) => (
                                    <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${blocker.severity === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                                                    blocker.severity === 'MAJOR' ? 'bg-orange-100 text-orange-800' :
                                                        'bg-blue-100 text-blue-800'
                                                    }`}>
                                                    {blocker.severity}
                                                </span>
                                                <h4 className="font-semibold mt-2">{blocker.requirement}</h4>
                                                <p className="text-sm text-gray-600 mt-1">{blocker.gap}</p>
                                            </div>
                                            <div className="text-right">
                                                <span className="text-xs text-gray-400">Time to fix</span>
                                                <p className="font-medium text-sm">{blocker.improvement_timeline}</p>
                                            </div>
                                        </div>
                                        {blocker.is_addressable && (
                                            <div className="mt-4 pt-4 border-t border-gray-100 flex gap-3">
                                                <button className="text-sm text-indigo-600 font-medium hover:underline">
                                                    View Improvement Plan
                                                </button>
                                                <button className="text-sm text-gray-500 font-medium hover:underline">
                                                    Generate Objection Script
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}

                        <h2 className="text-xl font-bold mt-10 mb-4 flex items-center gap-2">
                            <Brain className="w-5 h-5 text-indigo-600" />
                            Target Company Interview Intelligence
                        </h2>

                        <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4">
                            <div className="flex flex-col md:flex-row gap-3">
                                <input
                                    type="text"
                                    value={companyTarget}
                                    onChange={(e) => setCompanyTarget(e.target.value)}
                                    className="flex-1 rounded-md border-gray-300 shadow-sm p-3 border"
                                    placeholder="e.g. Microsoft"
                                />
                                <button
                                    onClick={handleCompanyResearch}
                                    disabled={companyLoading}
                                    className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                                >
                                    {companyLoading ? 'Researching...' : 'Research Company'}
                                </button>
                            </div>
                            {companyError && <p className="text-sm text-rose-600 mt-2">{companyError}</p>}
                        </div>

                        {companyBriefing && (
                            <div className="space-y-4">
                                <div className="bg-white border border-gray-200 rounded-lg p-4">
                                    <h3 className="font-semibold text-gray-900 mb-2">What does the company do?</h3>
                                    <p className="text-sm text-gray-700">{companyBriefing.company_overview.what_they_do || 'No summary available yet.'}</p>
                                    <p className="text-xs text-gray-500 mt-2">
                                        Industry: {companyBriefing.company_overview.industry || 'Unknown'}
                                        {companyBriefing.company_overview.website ? ` • Website: ${companyBriefing.company_overview.website}` : ''}
                                    </p>
                                </div>

                                <div className="bg-white border border-gray-200 rounded-lg p-4">
                                    <h3 className="font-semibold text-gray-900 mb-2">Have they employed someone like me before? When?</h3>
                                    <p className="text-sm text-gray-700">
                                        {companyBriefing.similar_hiring_history.employed_similar_profiles
                                            ? `Yes — ${companyBriefing.similar_hiring_history.count} similar profiles found.`
                                            : 'No similar profile evidence found in scanned history yet.'}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-2">
                                        Years: {companyBriefing.similar_hiring_history.years.length > 0
                                            ? companyBriefing.similar_hiring_history.years.join(', ')
                                            : 'No year data found'}
                                    </p>
                                    {companyBriefing.similar_hiring_history.sample_roles.length > 0 && (
                                        <p className="text-xs text-gray-500 mt-1">
                                            Sample roles: {companyBriefing.similar_hiring_history.sample_roles.join(', ')}
                                        </p>
                                    )}
                                </div>

                                <div className="bg-white border border-gray-200 rounded-lg p-4">
                                    <h3 className="font-semibold text-gray-900 mb-2">Key highlights (news, appointments, products, developments)</h3>
                                    <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
                                        {companyBriefing.highlights.recent_news.slice(0, 4).map((n, idx) => (
                                            <li key={idx}>{n.title || n.snippet || 'Untitled update'}</li>
                                        ))}
                                        {companyBriefing.highlights.recent_news.length === 0 && (
                                            <li>No recent headline data returned.</li>
                                        )}
                                    </ul>
                                    {companyBriefing.highlights.new_appointments.length > 0 && (
                                        <p className="text-xs text-gray-500 mt-2">
                                            Appointments: {companyBriefing.highlights.new_appointments.join(' | ')}
                                        </p>
                                    )}
                                    {companyBriefing.highlights.new_products_or_developments.length > 0 && (
                                        <p className="text-xs text-gray-500 mt-1">
                                            Products/Developments: {companyBriefing.highlights.new_products_or_developments.join(' | ')}
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* TAB: QUESTIONS */}
                {activeTab === 'questions' && (
                    <div className="space-y-6">
                        <div className="flex gap-4 items-end">
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Question Type
                                </label>
                                <select
                                    value={qType}
                                    onChange={(e) => setQType(e.target.value)}
                                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2"
                                >
                                    <option>General competency</option>
                                    <option>Role-specific</option>
                                    <option>Role-specific & Performance Questions</option>
                                    <option>Marketing</option>
                                    <option>Technical</option>
                                    <option>Development</option>
                                    <option>Finance</option>
                                    <option>Sales</option>
                                    <option>Engineering</option>
                                    <option>Management</option>
                                    <option>Culture & values</option>
                                    <option>Leadership</option>
                                    <option>Problem-solving</option>
                                </select>
                            </div>
                            <button
                                onClick={handleGenerateQuestions}
                                disabled={loading}
                                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                            >
                                {loading ? 'Generating...' : 'Generate Questions'}
                            </button>
                        </div>

                        <div className="space-y-4">
                            {questions.map((q, i) => (
                                <div key={i} className="p-4 bg-gray-50 rounded-lg border border-gray-200 flex gap-3">
                                    <span className="font-bold text-gray-400">Q{i + 1}</span>
                                    <p className="text-gray-800 font-medium">{q}</p>
                                    <button
                                        className="ml-2 text-xs text-emerald-600 hover:text-emerald-800"
                                        onClick={() => markQuestionUsefulness(q, true)}
                                    >
                                        👍 Useful
                                    </button>
                                    <button
                                        className="text-xs text-rose-600 hover:text-rose-800"
                                        onClick={() => markQuestionUsefulness(q, false)}
                                    >
                                        👎 Not useful
                                    </button>
                                    <button
                                        className="ml-auto text-sm text-indigo-600 hover:text-indigo-800"
                                        onClick={() => {
                                            setPracticeQ(q);
                                            setActiveTab('practice');
                                        }}
                                    >
                                        Practice This
                                    </button>
                                </div>
                            ))}
                            {questions.length === 0 && !loading && (
                                <div className="text-center py-10 text-gray-400">
                                    Select a type and click Generate to start.
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* TAB: PRACTICE */}
                {activeTab === 'practice' && (
                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Question</label>
                            <input
                                type="text"
                                value={practiceQ}
                                onChange={(e) => setPracticeQ(e.target.value)}
                                className="w-full rounded-md border-gray-300 shadow-sm p-3 border"
                                placeholder="Enter interview question..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Your Answer</label>
                            <textarea
                                value={practiceA}
                                onChange={(e) => setPracticeA(e.target.value)}
                                rows={6}
                                className="w-full rounded-md border-gray-300 shadow-sm p-3 border"
                                placeholder="Type your answer here (try using STAR method)..."
                            />
                        </div>

                        <div className="flex justify-end">
                            <button
                                onClick={handleReview}
                                disabled={loading || !practiceQ || !practiceA}
                                className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                            >
                                {loading ? 'Analyzing...' : <> <Target className="w-4 h-4" /> Get Feedback </>}
                            </button>
                        </div>

                        {feedback && (
                            <div className="mt-8 border-t pt-6 animate-fade-in">
                                <h3 className="text-lg font-bold mb-4">AI Feedback</h3>
                                <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100 mb-4">
                                    <p className="text-indigo-900">{feedback.summary}</p>
                                </div>

                                <div className="flex items-center gap-3 mb-4">
                                    <span className="text-sm text-gray-600">Was this coaching useful?</span>
                                    <button
                                        onClick={() => markAnswerFeedback(true)}
                                        className="text-xs px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
                                    >
                                        👍 Yes
                                    </button>
                                    <button
                                        onClick={() => markAnswerFeedback(false)}
                                        className="text-xs px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100"
                                    >
                                        👎 No
                                    </button>
                                    {feedbackSaved && <span className="text-xs text-gray-500">{feedbackSaved}</span>}
                                </div>

                                {feedback.suggestions && (
                                    <div className="space-y-2">
                                        <h4 className="font-semibold text-gray-700">Suggestions</h4>
                                        <ul className="list-disc pl-5 space-y-1 text-gray-600">
                                            {feedback.suggestions.map((s: string, i: number) => (
                                                <li key={i}>{s}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

            </div>
        </div>
    );
}

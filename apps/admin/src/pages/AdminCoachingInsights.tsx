import { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Brain, Loader2, Target } from 'lucide-react';

interface RoleDetectResponse {
    role_family: string;
    role_function: string;
    detected_at: string;
}

interface NinetyDayPlanResponse {
    role_function: string;
    seniority: string;
    plan: {
        days_1_30: string[];
        days_31_60: string[];
        days_61_90: string[];
    };
    generated_at: string;
}

interface LearningProfileResponse {
    user_id: string;
    profile: Record<string, unknown>;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
    const response = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        throw new Error(await response.text());
    }
    return response.json() as Promise<T>;
}

async function getJson<T>(url: string, authToken?: string): Promise<T> {
    const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
    });
    if (!response.ok) {
        throw new Error(await response.text());
    }
    return response.json() as Promise<T>;
}

export default function AdminCoachingInsights() {
    const [jobData, setJobData] = useState<string>('Senior Data Engineer working on cloud platform reliability and ML workloads');
    const [resumeData, setResumeData] = useState<string>('Led data engineering team, built pipelines in Python and SQL, improved deployment reliability');
    const [roleDetect, setRoleDetect] = useState<RoleDetectResponse | null>(null);
    const [plan, setPlan] = useState<NinetyDayPlanResponse | null>(null);
    const [learningProfile, setLearningProfile] = useState<LearningProfileResponse | null>(null);
    const [seniority, setSeniority] = useState<string>('mid');
    const [loadingRole, setLoadingRole] = useState(false);
    const [loadingPlan, setLoadingPlan] = useState(false);
    const [loadingProfile, setLoadingProfile] = useState(false);
    const [error, setError] = useState<string>('');

    const runRoleDetection = async () => {
        try {
            setLoadingRole(true);
            setError('');
            const result = await postJson<RoleDetectResponse>('/api/coaching/v1/role/detect', {
                job_data: { title: jobData, description: jobData },
                resume_data: { raw_text: resumeData, summary: resumeData },
            });
            setRoleDetect(result);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Role detection failed');
        } finally {
            setLoadingRole(false);
        }
    };

    const runPlan = async () => {
        try {
            setLoadingPlan(true);
            setError('');
            const roleFunction = roleDetect?.role_function ?? 'EXEC';
            const result = await postJson<NinetyDayPlanResponse>('/api/coaching/v1/plan/90day', {
                role_function: roleFunction,
                seniority,
            });
            setPlan(result);
        } catch (e) {
            setError(e instanceof Error ? e.message : '90-day plan generation failed');
        } finally {
            setLoadingPlan(false);
        }
    };

    const loadLearningProfile = async () => {
        try {
            setLoadingProfile(true);
            setError('');
            const token = localStorage.getItem('access_token') || undefined;
            const roleFamily = roleDetect?.role_family ? `?role_family=${encodeURIComponent(roleDetect.role_family)}` : '';
            const result = await getJson<LearningProfileResponse>(`/api/coaching/v1/learning/profile${roleFamily}`, token);
            setLearningProfile(result);
        } catch {
            setLearningProfile(null);
            setError('Learning profile endpoint requires authenticated coaching token in this environment.');
        } finally {
            setLoadingProfile(false);
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🧠 Admin Coaching Insights</h1>
                    <p className="text-slate-400">Role detection, 90-day planning, and learning profile checks</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
                    <div className="text-sm font-semibold text-white">Role Detection Harness</div>
                    <textarea
                        value={jobData}
                        onChange={(e) => setJobData(e.target.value)}
                        className="w-full min-h-[90px] p-3 bg-slate-800 border border-slate-600 rounded-lg text-white"
                        placeholder="Job context"
                    />
                    <textarea
                        value={resumeData}
                        onChange={(e) => setResumeData(e.target.value)}
                        className="w-full min-h-[90px] p-3 bg-slate-800 border border-slate-600 rounded-lg text-white"
                        placeholder="Resume context"
                    />
                    <button
                        type="button"
                        onClick={runRoleDetection}
                        disabled={loadingRole}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded-lg text-white"
                    >
                        {loadingRole ? <Loader2 size={16} className="animate-spin" /> : <Brain size={16} />}
                        Detect Role
                    </button>
                    {roleDetect && (
                        <div className="text-sm text-slate-200">
                            Family: <span className="font-semibold">{roleDetect.role_family}</span> • Function: <span className="font-semibold">{roleDetect.role_function}</span>
                        </div>
                    )}
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
                    <div className="text-sm font-semibold text-white">90-Day Plan Generator</div>
                    <div className="flex items-center gap-3">
                        <select
                            aria-label="Seniority"
                            value={seniority}
                            onChange={(e) => setSeniority(e.target.value)}
                            className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                        >
                            <option value="junior">junior</option>
                            <option value="mid">mid</option>
                            <option value="senior">senior</option>
                        </select>
                        <button
                            type="button"
                            onClick={runPlan}
                            disabled={loadingPlan}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-800 rounded-lg text-white"
                        >
                            {loadingPlan ? <Loader2 size={16} className="animate-spin" /> : <Target size={16} />}
                            Generate 90-Day Plan
                        </button>
                    </div>
                    {plan && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
                                <div className="font-semibold text-white mb-2">Days 1-30</div>
                                <ul className="text-slate-300 space-y-1">{plan.plan.days_1_30.map((x) => <li key={x}>• {x}</li>)}</ul>
                            </div>
                            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
                                <div className="font-semibold text-white mb-2">Days 31-60</div>
                                <ul className="text-slate-300 space-y-1">{plan.plan.days_31_60.map((x) => <li key={x}>• {x}</li>)}</ul>
                            </div>
                            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
                                <div className="font-semibold text-white mb-2">Days 61-90</div>
                                <ul className="text-slate-300 space-y-1">{plan.plan.days_61_90.map((x) => <li key={x}>• {x}</li>)}</ul>
                            </div>
                        </div>
                    )}
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
                    <div className="text-sm font-semibold text-white">Learning Profile Viewer</div>
                    <button
                        type="button"
                        onClick={loadLearningProfile}
                        disabled={loadingProfile}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white"
                    >
                        {loadingProfile ? <Loader2 size={16} className="animate-spin" /> : <Brain size={16} />}
                        Load Learning Profile
                    </button>
                    {learningProfile && (
                        <pre className="text-xs text-slate-200 bg-slate-800 border border-slate-700 rounded-lg p-3 overflow-x-auto">
                            {JSON.stringify(learningProfile, null, 2)}
                        </pre>
                    )}
                </div>

                {error && <div className="bg-red-950 border border-red-700 rounded-lg p-3 text-red-200 text-sm">{error}</div>}
            </div>
        </AdminLayout>
    );
}

import { useEffect, useState, useCallback } from 'react';
import AdminLayout from '../components/AdminLayout';
import {
    ArrowLeft,
    Bot,
    Check,
    Edit3,
    Headphones,
    Loader2,
    MessageSquare,
    RefreshCw,
    Send,
    ShieldCheck,
    Tag,
    Zap,
} from 'lucide-react';

/* ── Types ────────────────────────────────────────────────── */

interface Ticket {
    id: number;
    zendesk_ticket_id: string | null;
    user_id: number | null;
    subject: string;
    status: string;
    priority: string | null;
    category: string | null;
    portal: string | null;
    request_id: string | null;
    last_comment_at: string | null;
    created_at: string | null;
    updated_at: string | null;
}

interface Comment {
    id: number;
    body: string;
    html_body?: string;
    public: boolean;
    created_at: string | null;
    author_name: string | null;
    author_email: string | null;
    author_id: number | null;
}
interface AIDraft {
    job_id: string;
    kind: string;
    result: {
        draft_reply?: string;
        confidence?: number;
        needs_human_review?: boolean;
        internal_note?: string;
        processed_at?: string;
        llm_provider?: string;
        llm_model?: string;
    } | null;
    created_at: string | null;
    completed_at: string | null;
}

interface QueueStats {
    pending: number;
    processing: number;
    processed: number;
    failed: number;
}
/* ── API helpers ──────────────────────────────────────────── */

const api = (path: string, opts?: RequestInit) =>
    fetch(path, { credentials: 'include', ...opts }).then(async (r) => {
        if (!r.ok) throw new Error((await r.json().catch(() => ({ detail: r.statusText }))).detail ?? r.statusText);
        return r.json();
    });

async function fetchTickets(params: Record<string, string>): Promise<{ tickets: Ticket[]; total: number }> {
    const qs = new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([, v]) => v)));
    return api(`/api/support/v1/tickets?${qs}`);
}

async function fetchComments(ticketId: number): Promise<{ comments: Comment[] }> {
    return api(`/api/support/v1/tickets/${ticketId}/comments`);
}

async function postReply(ticketId: number, body: string, isPublic: boolean): Promise<unknown> {
    return api(`/api/support/v1/tickets/${ticketId}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body, public: isPublic }),
    });
}

async function fetchAIDraft(ticketId: number): Promise<AIDraft | null> {
    try {
        const data = await api(`/api/support/v1/tickets/${ticketId}/ai-draft`);
        if (data.result) return data as AIDraft;
        return null;
    } catch {
        return null;
    }
}

async function fetchQueueStats(): Promise<QueueStats> {
    try {
        const data = await api('/api/support/v1/ai/queue-stats');
        return { pending: data.pending ?? 0, processing: data.processing ?? 0, processed: data.processed ?? 0, failed: data.failed ?? 0 };
    } catch {
        return { pending: 0, processing: 0, processed: 0, failed: 0 };
    }
}

async function approveAIDraft(ticketId: number, jobId: string, editedBody: string | null, isPublic: boolean): Promise<unknown> {
    return api(`/api/support/v1/tickets/${ticketId}/approve-ai-draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId, edited_body: editedBody, public: isPublic }),
    });
}

/* ── Status badge colours ─────────────────────────────────── */

function statusBadge(status: string) {
    const colours: Record<string, string> = {
        new: 'bg-blue-600',
        open: 'bg-yellow-600',
        pending: 'bg-orange-600',
        solved: 'bg-emerald-600',
        closed: 'bg-slate-600',
    };
    return (
        <span className={`px-2 py-0.5 rounded text-xs font-medium text-white ${colours[status] ?? 'bg-slate-500'}`}>
            {status}
        </span>
    );
}

function priorityBadge(p: string | null) {
    if (!p) return null;
    const colours: Record<string, string> = {
        urgent: 'text-red-400',
        high: 'text-orange-400',
        normal: 'text-blue-400',
        low: 'text-slate-400',
    };
    return <span className={`text-xs font-medium ${colours[p] ?? 'text-slate-400'}`}>{p}</span>;
}

/* ── Format date helper ───────────────────────────────────── */

function fmtDate(iso: string | null) {
    if (!iso) return '—';
    try {
        return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
        return iso;
    }
}

/* ── Main Component ───────────────────────────────────────── */

export default function AdminSupportOps() {
    /* ticket list state */
    const [tickets, setTickets] = useState<Ticket[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [filterStatus, setFilterStatus] = useState('');
    const [filterCategory, setFilterCategory] = useState('');

    /* detail / thread state */
    const [selected, setSelected] = useState<Ticket | null>(null);
    const [comments, setComments] = useState<Comment[]>([]);
    const [commentsLoading, setCommentsLoading] = useState(false);

    /* reply state */
    const [replyText, setReplyText] = useState('');
    const [replyPublic, setReplyPublic] = useState(true);
    const [replying, setReplying] = useState(false);

    /* AI draft state */
    const [aiDraft, setAiDraft] = useState<AIDraft | null>(null);
    const [aiDraftLoading, setAiDraftLoading] = useState(false);
    const [aiEditing, setAiEditing] = useState(false);
    const [aiEditedText, setAiEditedText] = useState('');
    const [aiApproving, setAiApproving] = useState(false);
    const [queueStats, setQueueStats] = useState<QueueStats | null>(null);

    /* ── Load ticket list ─────────────────────────────────── */

    const loadTickets = useCallback(async () => {
        try {
            setLoading(true);
            setError('');
            const data = await fetchTickets({ status: filterStatus, category: filterCategory, limit: '100' });
            setTickets(data.tickets);
            setTotal(data.total);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to load tickets');
        } finally {
            setLoading(false);
        }
    }, [filterStatus, filterCategory]);

    useEffect(() => {
        loadTickets();
    }, [loadTickets]);

    /* ── Load comments for selected ticket ────────────────── */

    const openTicket = async (ticket: Ticket) => {
        setSelected(ticket);
        setComments([]);
        setReplyText('');
        setAiDraft(null);
        setAiEditing(false);
        setCommentsLoading(true);
        setAiDraftLoading(true);
        try {
            const [cData, draft] = await Promise.all([
                fetchComments(ticket.id),
                fetchAIDraft(ticket.id),
            ]);
            setComments(cData.comments);
            setAiDraft(draft);
            if (draft?.result?.draft_reply) {
                setAiEditedText(draft.result.draft_reply);
            }
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to load ticket details');
        } finally {
            setCommentsLoading(false);
            setAiDraftLoading(false);
        }
    };

    /* ── Send reply ───────────────────────────────────────── */

    const handleReply = async () => {
        if (!selected || !replyText.trim()) return;
        setReplying(true);
        try {
            await postReply(selected.id, replyText.trim(), replyPublic);
            setReplyText('');
            // Refresh the thread
            const data = await fetchComments(selected.id);
            setComments(data.comments);
            // Refresh list in background to update status
            loadTickets();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to send reply');
        } finally {
            setReplying(false);
        }
    };
    /* ── Approve AI draft ─────────────────────────────────── */

    const handleApproveAI = async () => {
        if (!selected || !aiDraft) return;
        setAiApproving(true);
        try {
            const body = aiEditing ? aiEditedText : null;
            await approveAIDraft(selected.id, aiDraft.job_id, body, replyPublic);
            setAiDraft(null);
            setAiEditing(false);
            // refresh thread
            const data = await fetchComments(selected.id);
            setComments(data.comments);
            loadTickets();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to approve AI draft');
        } finally {
            setAiApproving(false);
        }
    };

    /* ── Load queue stats on mount ────────────────────────── */

    useEffect(() => {
        fetchQueueStats().then(setQueueStats);
    }, []);
    /* ── Ticket Detail / Thread View ──────────────────────── */

    if (selected) {
        return (
            <AdminLayout>
                <div className="max-w-4xl mx-auto space-y-4">
                    {/* Back + header */}
                    <button
                        onClick={() => { setSelected(null); loadTickets(); }}
                        className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition"
                    >
                        <ArrowLeft size={16} /> Back to ticket queue
                    </button>

                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-5 space-y-2">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-semibold text-white">{selected.subject}</h2>
                            <div className="flex items-center gap-2">
                                {statusBadge(selected.status)}
                                {priorityBadge(selected.priority)}
                            </div>
                        </div>
                        <div className="flex flex-wrap gap-4 text-xs text-slate-400">
                            <span>Local #{selected.id}</span>
                            {selected.zendesk_ticket_id && <span>Zendesk #{selected.zendesk_ticket_id}</span>}
                            {selected.category && <span className="inline-flex items-center gap-1"><Tag size={12} />{selected.category}</span>}
                            {selected.portal && <span>Portal: {selected.portal}</span>}
                            <span>Created: {fmtDate(selected.created_at)}</span>
                        </div>
                    </div>

                    {/* Comment thread */}
                    <div className="bg-slate-900 border border-slate-700 rounded-lg divide-y divide-slate-800">
                        <div className="p-4 flex items-center justify-between">
                            <h3 className="text-sm font-semibold text-white inline-flex items-center gap-2">
                                <MessageSquare size={16} className="text-blue-400" /> Conversation
                            </h3>
                            <button onClick={() => openTicket(selected)} className="text-xs text-slate-400 hover:text-white transition inline-flex items-center gap-1">
                                <RefreshCw size={12} /> Refresh
                            </button>
                        </div>

                        {commentsLoading ? (
                            <div className="p-6 flex items-center gap-2 text-slate-400">
                                <Loader2 size={16} className="animate-spin" /> Loading thread...
                            </div>
                        ) : comments.length === 0 ? (
                            <div className="p-6 text-sm text-slate-500">No comments yet.</div>
                        ) : (
                            comments.map((c) => (
                                <div key={c.id} className={`p-4 space-y-1 ${!c.public ? 'bg-yellow-950/20 border-l-2 border-yellow-600' : ''}`}>
                                    <div className="flex items-center justify-between">
                                        <div className="text-sm font-medium text-white">
                                            {c.author_name || c.author_email || `Author #${c.author_id}`}
                                        </div>
                                        <div className="flex items-center gap-2 text-xs text-slate-500">
                                            {!c.public && (
                                                <span className="text-yellow-500 font-medium flex items-center gap-1">
                                                    <ShieldCheck size={12} /> Internal
                                                </span>
                                            )}
                                            {fmtDate(c.created_at)}
                                        </div>
                                    </div>
                                    <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{c.body}</div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* AI Draft Card */}
                    {aiDraftLoading ? (
                        <div className="bg-purple-950/30 border border-purple-700/50 rounded-lg p-4 flex items-center gap-2 text-purple-300 text-sm">
                            <Loader2 size={16} className="animate-spin" /> Checking for AI draft...
                        </div>
                    ) : aiDraft?.result ? (
                        <div className="bg-purple-950/30 border border-purple-700/50 rounded-lg p-4 space-y-3">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-semibold text-purple-300 inline-flex items-center gap-2">
                                    <Bot size={16} className="text-purple-400" /> AI Draft Reply
                                    {aiDraft.result.confidence != null && (
                                        <span className="text-xs font-normal text-purple-400/70 ml-2">
                                            Confidence: {Math.round(aiDraft.result.confidence * 100)}%
                                        </span>
                                    )}
                                </h3>
                                <div className="flex items-center gap-2 text-xs text-purple-400/60">
                                    {aiDraft.result.llm_model && <span>{aiDraft.result.llm_model}</span>}
                                    {aiDraft.result.needs_human_review && (
                                        <span className="text-yellow-400 font-medium">Needs Review</span>
                                    )}
                                </div>
                            </div>

                            {aiDraft.result.internal_note && (
                                <div className="text-xs text-purple-400/60 italic border-l-2 border-purple-700 pl-2">
                                    AI note: {aiDraft.result.internal_note}
                                </div>
                            )}

                            {aiEditing ? (
                                <textarea
                                    rows={6}
                                    value={aiEditedText}
                                    onChange={(e) => setAiEditedText(e.target.value)}
                                    className="w-full bg-slate-800 border border-purple-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-y"
                                />
                            ) : (
                                <div className="bg-slate-800/50 rounded-lg px-3 py-2 text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                                    {aiDraft.result.draft_reply}
                                </div>
                            )}

                            <div className="flex items-center justify-between">
                                <label className="inline-flex items-center gap-2 text-sm text-slate-400 cursor-pointer select-none">
                                    <input
                                        type="checkbox"
                                        checked={replyPublic}
                                        onChange={(e) => setReplyPublic(e.target.checked)}
                                        className="rounded border-slate-600"
                                    />
                                    Public reply
                                </label>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => { setAiEditing(!aiEditing); if (!aiEditing && aiDraft.result?.draft_reply) setAiEditedText(aiDraft.result.draft_reply); }}
                                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-medium transition"
                                    >
                                        <Edit3 size={12} /> {aiEditing ? 'Preview' : 'Edit'}
                                    </button>
                                    <button
                                        onClick={handleApproveAI}
                                        disabled={aiApproving}
                                        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-medium transition"
                                    >
                                        {aiApproving ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                                        {aiApproving ? 'Sending...' : 'Approve & Send'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : null}

                    {/* Reply box */}
                    {selected.zendesk_ticket_id && (
                        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
                            <h3 className="text-sm font-semibold text-white">Reply</h3>
                            <textarea
                                rows={4}
                                value={replyText}
                                onChange={(e) => setReplyText(e.target.value)}
                                placeholder="Type your reply to the customer..."
                                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
                            />
                            <div className="flex items-center justify-between">
                                <label className="inline-flex items-center gap-2 text-sm text-slate-400 cursor-pointer select-none">
                                    <input
                                        type="checkbox"
                                        checked={replyPublic}
                                        onChange={(e) => setReplyPublic(e.target.checked)}
                                        className="rounded border-slate-600"
                                    />
                                    Public reply (visible to customer)
                                </label>
                                <button
                                    onClick={handleReply}
                                    disabled={replying || !replyText.trim()}
                                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition"
                                >
                                    {replying ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                                    {replying ? 'Sending...' : 'Send Reply'}
                                </button>
                            </div>
                        </div>
                    )}

                    {error && <div className="bg-red-950 border border-red-700 rounded-lg p-3 text-red-200 text-sm">{error}</div>}
                </div>
            </AdminLayout>
        );
    }

    /* ── Ticket Queue (list view) ─────────────────────────── */

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-1 inline-flex items-center gap-3">
                            <Headphones className="text-blue-400" /> Support Tickets
                        </h1>
                        <p className="text-slate-400 text-sm">{total} ticket{total !== 1 ? 's' : ''} total</p>
                    </div>
                    <button
                        onClick={loadTickets}
                        disabled={loading}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white text-sm transition"
                    >
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
                    </button>
                </div>

                {/* AI Queue Stats */}
                {queueStats && (queueStats.pending > 0 || queueStats.processing > 0 || queueStats.processed > 0) && (
                    <div className="bg-purple-950/20 border border-purple-700/40 rounded-lg px-4 py-3 flex items-center gap-4 text-sm">
                        <Zap size={16} className="text-purple-400 shrink-0" />
                        <span className="text-purple-300 font-medium">AI Agent Queue:</span>
                        <span className="text-slate-300">{queueStats.pending} pending</span>
                        <span className="text-slate-300">{queueStats.processing} processing</span>
                        <span className="text-emerald-400">{queueStats.processed} processed</span>
                        {queueStats.failed > 0 && <span className="text-red-400">{queueStats.failed} failed</span>}
                    </div>
                )}

                {/* Filters */}
                <div className="flex gap-3 flex-wrap">
                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                    >
                        <option value="">All statuses</option>
                        <option value="new">New</option>
                        <option value="open">Open</option>
                        <option value="pending">Pending</option>
                        <option value="solved">Solved</option>
                        <option value="closed">Closed</option>
                    </select>
                    <select
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                        className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                    >
                        <option value="">All categories</option>
                        <option value="Login">Login</option>
                        <option value="Billing">Billing</option>
                        <option value="Bugs">Bugs</option>
                        <option value="Feature Request">Feature Request</option>
                        <option value="Test">Test</option>
                    </select>
                </div>

                {/* Error */}
                {error && <div className="bg-red-950 border border-red-700 rounded-lg p-3 text-red-200 text-sm">{error}</div>}

                {/* Table */}
                {loading ? (
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-8 flex items-center gap-3 text-slate-300">
                        <Loader2 size={18} className="animate-spin" /> Loading tickets...
                    </div>
                ) : tickets.length === 0 ? (
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-8 text-center text-slate-500">
                        No tickets found.
                    </div>
                ) : (
                    <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-slate-800 text-slate-400 text-xs uppercase">
                                <tr>
                                    <th className="px-4 py-3">ID</th>
                                    <th className="px-4 py-3">Subject</th>
                                    <th className="px-4 py-3">Status</th>
                                    <th className="px-4 py-3">Priority</th>
                                    <th className="px-4 py-3">Category</th>
                                    <th className="px-4 py-3">Updated</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {tickets.map((t) => (
                                    <tr
                                        key={t.id}
                                        onClick={() => openTicket(t)}
                                        className="hover:bg-slate-800/50 cursor-pointer transition"
                                    >
                                        <td className="px-4 py-3 text-slate-400 font-mono">
                                            #{t.id}
                                            {t.zendesk_ticket_id && (
                                                <span className="ml-1 text-xs text-slate-600">ZD#{t.zendesk_ticket_id}</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-white font-medium">{t.subject}</td>
                                        <td className="px-4 py-3">{statusBadge(t.status)}</td>
                                        <td className="px-4 py-3">{priorityBadge(t.priority)}</td>
                                        <td className="px-4 py-3 text-slate-400">{t.category ?? '—'}</td>
                                        <td className="px-4 py-3 text-slate-400 text-xs">{fmtDate(t.updated_at)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </AdminLayout>
    );
}

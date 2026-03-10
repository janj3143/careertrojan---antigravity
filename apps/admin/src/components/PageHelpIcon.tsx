import React from 'react';
import { HelpCircle, X } from 'lucide-react';
import { useLocation } from 'react-router-dom';

function stripEmoji(value: string): string {
    return value.replace(/^[^\p{L}\p{N}]+/u, '').trim();
}

function inferPurpose(title: string, subtitle: string, pathname: string): string {
    const cleanTitle = stripEmoji(title || 'this page');
    if (subtitle) return subtitle;

    const lower = cleanTitle.toLowerCase();
    if (lower.includes('dashboard')) return `review key metrics and operational summaries for ${cleanTitle}`;
    if (lower.includes('analytics')) return `analyze trends and performance data for ${cleanTitle}`;
    if (lower.includes('management')) return `manage records, settings, and actions related to ${cleanTitle}`;
    if (lower.includes('audit')) return `inspect compliance and traceability signals for ${cleanTitle}`;
    if (lower.includes('api')) return `inspect and validate API connectivity and behaviors for ${cleanTitle}`;
    if (lower.includes('model')) return `manage model lifecycle and training controls for ${cleanTitle}`;
    if (lower.includes('support')) return `oversee support workflows and helpdesk operations for ${cleanTitle}`;

    const routeHint = pathname.replace('/admin', '').replace(/\//g, ' ').trim();
    return `work with ${cleanTitle}${routeHint ? ` in the ${routeHint} section` : ''}`;
}

export default function PageHelpIcon() {
    const location = useLocation();
    const [open, setOpen] = React.useState(false);
    const [title, setTitle] = React.useState('This page');
    const [subtitle, setSubtitle] = React.useState('');

    React.useEffect(() => {
        const update = () => {
            const heading = document.querySelector('main h1, h1');
            const headingText = (heading?.textContent || 'This page').trim();
            const sub = (heading?.parentElement?.querySelector('p')?.textContent || '').trim();
            setTitle(headingText || 'This page');
            setSubtitle(sub);
        };

        const id = window.setTimeout(update, 0);
        return () => window.clearTimeout(id);
    }, [location.pathname]);

    const purpose = inferPurpose(title, subtitle, location.pathname);

    return (
        <div className="fixed right-4 bottom-4 z-50">
            {open && (
                <div className="mb-3 w-80 rounded-xl border border-slate-700 bg-slate-900/95 p-4 text-sm text-slate-200 shadow-xl">
                    <div className="mb-2 flex items-start justify-between gap-2">
                        <h3 className="font-semibold text-white">Page Help</h3>
                        <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white" aria-label="Close help">
                            <X size={16} />
                        </button>
                    </div>
                    <p className="mb-2 text-slate-300"><span className="font-medium text-white">Page:</span> {stripEmoji(title)}</p>
                    <p className="mb-2 text-slate-300"><span className="font-medium text-white">Route:</span> {location.pathname}</p>
                    <p className="text-slate-200">This page is meant to {purpose}.</p>
                </div>
            )}
            <button
                onClick={() => setOpen(!open)}
                className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition hover:bg-blue-500"
                aria-label="Open page help"
                title="Page help"
            >
                <HelpCircle size={20} />
            </button>
        </div>
    );
}

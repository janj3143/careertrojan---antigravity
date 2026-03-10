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
    if (lower.includes('dashboard')) return `track mentee progress and mentor operations from ${cleanTitle}`;
    if (lower.includes('agreement')) return `manage mentor agreements and commitments in ${cleanTitle}`;
    if (lower.includes('calendar')) return `manage session scheduling and availability in ${cleanTitle}`;
    if (lower.includes('communication')) return `coordinate mentor-mentee communication from ${cleanTitle}`;
    if (lower.includes('assistant')) return `use AI assistance for mentorship tasks in ${cleanTitle}`;

    const routeHint = pathname.replace('/mentor', '').replace(/\//g, ' ').trim();
    return `handle mentorship workflows for ${cleanTitle}${routeHint ? ` in ${routeHint}` : ''}`;
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
                className="flex h-12 w-12 items-center justify-center rounded-full bg-green-600 text-white shadow-lg transition hover:bg-green-500"
                aria-label="Open page help"
                title="Page help"
            >
                <HelpCircle size={20} />
            </button>
        </div>
    );
}

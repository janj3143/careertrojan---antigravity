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
    if (lower.includes('dashboard')) return `review your progress and key career signals on ${cleanTitle}`;
    if (lower.includes('profile')) return `manage and enrich your profile details on ${cleanTitle}`;
    if (lower.includes('resume')) return `upload, parse, and improve your resume from ${cleanTitle}`;
    if (lower.includes('coaching')) return `run guided reflection and coaching actions in ${cleanTitle}`;
    if (lower.includes('market')) return `review market-fit insights and route signals in ${cleanTitle}`;
    if (lower.includes('rewards')) return `track and redeem reward progress from ${cleanTitle}`;

    const routeHint = pathname.replace(/\//g, ' ').trim();
    return `complete the workflow for ${cleanTitle}${routeHint ? ` in ${routeHint}` : ''}`;
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
        <div className="fixed right-4 bottom-20 z-50">
            {open && (
                <div className="mb-3 w-80 rounded-xl border border-gray-200 bg-white/95 p-4 text-sm text-gray-700 shadow-xl">
                    <div className="mb-2 flex items-start justify-between gap-2">
                        <h3 className="font-semibold text-gray-900">Page Help</h3>
                        <button onClick={() => setOpen(false)} className="text-gray-500 hover:text-gray-900" aria-label="Close help">
                            <X size={16} />
                        </button>
                    </div>
                    <p className="mb-2"><span className="font-medium text-gray-900">Page:</span> {stripEmoji(title)}</p>
                    <p className="mb-2"><span className="font-medium text-gray-900">Route:</span> {location.pathname}</p>
                    <p>This page is meant to {purpose}.</p>
                </div>
            )}
            <button
                onClick={() => setOpen(!open)}
                className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg transition hover:bg-indigo-500"
                aria-label="Open page help"
                title="Page help"
            >
                <HelpCircle size={20} />
            </button>
        </div>
    );
}

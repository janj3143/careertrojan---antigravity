import React from 'react';

interface PullToRefreshProps {
    onRefresh: () => Promise<void>;
    children: React.ReactNode;
}

/**
 * PullToRefresh — wraps content to enable pull-down refresh on mobile.
 * Phase 3 mobile UX enhancement.
 */
export default function PullToRefresh({ onRefresh, children }: PullToRefreshProps) {
    const [pulling, setPulling] = React.useState(false);
    const [refreshing, setRefreshing] = React.useState(false);
    const [pullDistance, setPullDistance] = React.useState(0);
    const startY = React.useRef(0);
    const containerRef = React.useRef<HTMLDivElement>(null);

    const threshold = 80;

    const handleTouchStart = (e: React.TouchEvent) => {
        if (containerRef.current && containerRef.current.scrollTop === 0) {
            startY.current = e.touches[0].clientY;
            setPulling(true);
        }
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        if (!pulling || refreshing) return;
        const delta = e.touches[0].clientY - startY.current;
        if (delta > 0) {
            setPullDistance(Math.min(delta * 0.5, 120));
        }
    };

    const handleTouchEnd = async () => {
        if (pullDistance > threshold && !refreshing) {
            setRefreshing(true);
            try {
                await onRefresh();
            } finally {
                setRefreshing(false);
            }
        }
        setPulling(false);
        setPullDistance(0);
    };

    return (
        <div
            ref={containerRef}
            className="overflow-y-auto"
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
        >
            {/* Pull indicator */}
            <div
                className="flex items-center justify-center overflow-hidden transition-all"
                style={{ height: pullDistance }}
            >
                {refreshing ? (
                    <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                ) : pullDistance > threshold ? (
                    <span className="text-xs text-indigo-600 font-medium">Release to refresh</span>
                ) : pullDistance > 10 ? (
                    <span className="text-xs text-gray-400">Pull to refresh</span>
                ) : null}
            </div>
            {children}
        </div>
    );
}

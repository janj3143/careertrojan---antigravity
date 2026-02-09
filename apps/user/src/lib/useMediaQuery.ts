import { useState, useEffect } from 'react';

/**
 * Returns true when the viewport matches the given CSS media query.
 * Re-evaluates on window resize / orientation change.
 *
 * @example
 *   const isMobile = useMediaQuery('(max-width: 1023px)');
 */
export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState(() =>
        typeof window !== 'undefined' ? window.matchMedia(query).matches : false,
    );

    useEffect(() => {
        const mql = window.matchMedia(query);
        const handler = (e: MediaQueryListEvent) => setMatches(e.matches);

        // Modern browsers
        if (mql.addEventListener) {
            mql.addEventListener('change', handler);
            return () => mql.removeEventListener('change', handler);
        }
        // Safari < 14 fallback
        mql.addListener(handler);
        return () => mql.removeListener(handler);
    }, [query]);

    return matches;
}

/** Convenience shortcut — true on phones & small tablets */
export function useIsMobile() {
    return useMediaQuery('(max-width: 1023px)');
}

/** True when user has enabled reduced-motion in OS settings */
export function usePrefersReducedMotion() {
    return useMediaQuery('(prefers-reduced-motion: reduce)');
}

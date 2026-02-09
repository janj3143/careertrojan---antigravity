import { useState, useEffect, useCallback } from 'react';

type NetworkStatus = 'online' | 'offline';

/**
 * Tracks browser online/offline state.
 * Shows a reconnection notice in mobile-first apps.
 */
export function useNetworkStatus() {
    const [status, setStatus] = useState<NetworkStatus>(
        navigator.onLine ? 'online' : 'offline',
    );

    useEffect(() => {
        const goOnline = () => setStatus('online');
        const goOffline = () => setStatus('offline');
        window.addEventListener('online', goOnline);
        window.addEventListener('offline', goOffline);
        return () => {
            window.removeEventListener('online', goOnline);
            window.removeEventListener('offline', goOffline);
        };
    }, []);

    return status;
}

/**
 * Detects viewport keyboard opening (Android mostly).
 * Returns true when the visible viewport shrinks significantly,
 * indicating a virtual keyboard is open.
 */
export function useVirtualKeyboard() {
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        if (!('visualViewport' in window)) return;

        const vv = window.visualViewport!;
        const check = () => {
            // Keyboard is likely open if visible height < 75% of window height
            setIsOpen(vv.height < window.innerHeight * 0.75);
        };

        vv.addEventListener('resize', check);
        return () => vv.removeEventListener('resize', check);
    }, []);

    return isOpen;
}

/**
 * Locks body scroll (for modals / slide-out panels on mobile).
 */
export function useScrollLock(locked: boolean) {
    useEffect(() => {
        if (locked) {
            const prev = document.body.style.overflow;
            document.body.style.overflow = 'hidden';
            return () => {
                document.body.style.overflow = prev;
            };
        }
    }, [locked]);
}

/**
 * Debounced callback — useful for search inputs, scroll handlers.
 */
export function useDebounce<T extends (...args: any[]) => void>(
    fn: T,
    delay: number,
): T {
    const timer = useCallback(() => {
        let id: ReturnType<typeof setTimeout>;
        return ((...args: any[]) => {
            clearTimeout(id);
            id = setTimeout(() => fn(...args), delay);
        }) as T;
    }, [fn, delay]);

    return timer();
}

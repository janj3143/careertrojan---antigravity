import { useRef, useCallback } from 'react';

interface SwipeHandlers {
    onSwipeLeft?: () => void;
    onSwipeRight?: () => void;
    onSwipeUp?: () => void;
    onSwipeDown?: () => void;
}

interface SwipeState {
    startX: number;
    startY: number;
    startTime: number;
}

/**
 * Hook that returns `onTouchStart` / `onTouchEnd` handlers for swipe detection.
 * Attach them to any element: `<div {...swipeHandlers}>`.
 *
 * @param handlers  – callbacks for each direction
 * @param threshold – minimum px distance (default 80)
 * @param maxTime   – maximum ms duration (default 300)
 */
export function useSwipe(
    handlers: SwipeHandlers,
    threshold = 80,
    maxTime = 300,
) {
    const state = useRef<SwipeState | null>(null);

    const onTouchStart = useCallback((e: React.TouchEvent) => {
        const t = e.touches[0];
        state.current = { startX: t.clientX, startY: t.clientY, startTime: Date.now() };
    }, []);

    const onTouchEnd = useCallback(
        (e: React.TouchEvent) => {
            if (!state.current) return;
            const t = e.changedTouches[0];
            const dx = t.clientX - state.current.startX;
            const dy = t.clientY - state.current.startY;
            const dt = Date.now() - state.current.startTime;
            state.current = null;

            if (dt > maxTime) return;

            const absDx = Math.abs(dx);
            const absDy = Math.abs(dy);

            // Horizontal swipe wins when dx > dy
            if (absDx > absDy && absDx >= threshold) {
                if (dx > 0) handlers.onSwipeRight?.();
                else handlers.onSwipeLeft?.();
            }
            // Vertical swipe
            else if (absDy > absDx && absDy >= threshold) {
                if (dy > 0) handlers.onSwipeDown?.();
                else handlers.onSwipeUp?.();
            }
        },
        [handlers, threshold, maxTime],
    );

    return { onTouchStart, onTouchEnd };
}

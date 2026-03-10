/**
 * Reusable Modal / Dialog Component — CareerTrojan
 * ==================================================
 * Accessible modal with:
 *   - Backdrop click to close
 *   - ESC key to close
 *   - Focus trap (first focusable element on mount)
 *   - Body scroll lock
 *   - Framer-motion entry/exit animations
 *   - Responsive (full-screen on mobile, centred on desktop)
 *
 * Usage:
 *   <Modal open={isOpen} onClose={() => setOpen(false)} title="Confirm">
 *     <p>Are you sure?</p>
 *   </Modal>
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';

interface ModalProps {
    /** Whether the modal is open */
    open: boolean;
    /** Called when the modal should close (backdrop click, ESC, close button) */
    onClose: () => void;
    /** Optional title rendered in the header */
    title?: string;
    /** Content inside the modal body */
    children: React.ReactNode;
    /** Max width class (default: max-w-md) */
    maxWidth?: string;
    /** Hide the close (X) button */
    hideCloseButton?: boolean;
    /** Prevent closing via backdrop click / ESC (for mandatory confirmation) */
    persistent?: boolean;
    /** Optional footer (e.g. action buttons) */
    footer?: React.ReactNode;
}

const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
};

const panelVariants = {
    hidden: { opacity: 0, y: 24, scale: 0.97 },
    visible: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring', damping: 25, stiffness: 350 } },
    exit: { opacity: 0, y: 16, scale: 0.97, transition: { duration: 0.15 } },
};

export default function Modal({
    open,
    onClose,
    title,
    children,
    maxWidth = 'max-w-md',
    hideCloseButton = false,
    persistent = false,
    footer,
}: ModalProps) {
    const panelRef = useRef<HTMLDivElement>(null);

    // ── Body scroll lock ─────────────────────────────────────
    useEffect(() => {
        if (open) {
            const prev = document.body.style.overflow;
            document.body.style.overflow = 'hidden';
            return () => {
                document.body.style.overflow = prev;
            };
        }
    }, [open]);

    // ── Focus trap (simple: focus first focusable on mount) ──
    useEffect(() => {
        if (open && panelRef.current) {
            const focusable = panelRef.current.querySelector<HTMLElement>(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            focusable?.focus();
        }
    }, [open]);

    // ── ESC key handler ──────────────────────────────────────
    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            if (e.key === 'Escape' && !persistent) {
                onClose();
            }
        },
        [onClose, persistent],
    );

    useEffect(() => {
        if (open) {
            document.addEventListener('keydown', handleKeyDown);
            return () => document.removeEventListener('keydown', handleKeyDown);
        }
    }, [open, handleKeyDown]);

    // ── Backdrop click ───────────────────────────────────────
    const handleBackdropClick = () => {
        if (!persistent) onClose();
    };

    return (
        <AnimatePresence>
            {open && (
                <motion.div
                    className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
                    initial="hidden"
                    animate="visible"
                    exit="hidden"
                    aria-modal="true"
                    role="dialog"
                >
                    {/* Backdrop */}
                    <motion.div
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                        variants={backdropVariants}
                        onClick={handleBackdropClick}
                    />

                    {/* Panel */}
                    <motion.div
                        ref={panelRef}
                        className={`relative z-10 w-full ${maxWidth} bg-white rounded-2xl shadow-2xl overflow-hidden
                                    max-h-[90vh] flex flex-col`}
                        variants={panelVariants}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        {(title || !hideCloseButton) && (
                            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                                {title && (
                                    <h2 className="text-lg font-bold text-gray-900">{title}</h2>
                                )}
                                {!hideCloseButton && (
                                    <button
                                        onClick={onClose}
                                        className="ml-auto p-1 rounded-lg text-gray-400 hover:text-gray-600
                                                   hover:bg-gray-100 transition"
                                        aria-label="Close"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                        )}

                        {/* Body (scrollable) */}
                        <div className="flex-1 overflow-y-auto px-6 py-5">
                            {children}
                        </div>

                        {/* Footer */}
                        {footer && (
                            <div className="px-6 py-4 border-t border-gray-100 bg-gray-50">
                                {footer}
                            </div>
                        )}
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

import React, { useState, useEffect } from 'react';
import { Download, X } from 'lucide-react';

/**
 * PWA Install Banner — Shows when the browser offers to install.
 * Phase 2-3: Promotes "Add to Home Screen" on mobile.
 */
export default function PWAInstallBanner() {
    const [show, setShow] = useState(false);
    const [dismissed, setDismissed] = useState(false);

    useEffect(() => {
        // Check if already dismissed this session
        if (sessionStorage.getItem('pwa-banner-dismissed')) return;

        const handler = () => setShow(true);
        window.addEventListener('pwa-install-available', handler);
        return () => window.removeEventListener('pwa-install-available', handler);
    }, []);

    const handleInstall = () => {
        if ((window as any).__pwaInstallPrompt) {
            (window as any).__pwaInstallPrompt();
        }
        setShow(false);
    };

    const handleDismiss = () => {
        setDismissed(true);
        setShow(false);
        sessionStorage.setItem('pwa-banner-dismissed', 'true');
    };

    if (!show || dismissed) return null;

    return (
        <div className="lg:hidden fixed bottom-20 left-4 right-4 z-40 animate-slide-up">
            <div className="bg-indigo-900 text-white rounded-2xl p-4 shadow-2xl flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-xl flex-shrink-0">
                    <Download className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold">Install CareerTrojan</p>
                    <p className="text-xs text-indigo-200">Add to home screen for quick access</p>
                </div>
                <button
                    onClick={handleInstall}
                    className="flex-shrink-0 px-4 py-2 bg-white text-indigo-900 rounded-lg text-xs font-bold hover:bg-indigo-50 transition-colors touch-target"
                >
                    Install
                </button>
                <button
                    onClick={handleDismiss}
                    className="flex-shrink-0 p-1 hover:bg-white/10 rounded-lg transition-colors touch-target"
                    aria-label="Dismiss"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}

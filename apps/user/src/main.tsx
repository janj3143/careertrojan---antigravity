
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// ── PWA Service Worker Registration ──────────────────────
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('[SW] Registered:', reg.scope))
            .catch(err => console.warn('[SW] Registration failed:', err));
    });
}

// ── PWA Install Prompt ───────────────────────────────────
let deferredPrompt: any = null;
window.addEventListener('beforeinstallprompt', (e: Event) => {
    e.preventDefault();
    deferredPrompt = e;
    // Dispatch custom event so components can show an install button
    window.dispatchEvent(new CustomEvent('pwa-install-available', { detail: deferredPrompt }));
});

// Export for components to trigger install
(window as any).__pwaInstallPrompt = () => {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choice: any) => {
            if (choice.outcome === 'accepted') console.log('[PWA] Installed');
            deferredPrompt = null;
        });
    }
};

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
)

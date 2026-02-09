import { useNetworkStatus } from '../../lib/useMobileUtils';

/**
 * Floating banner shown when the device goes offline.
 * Auto-hides when connectivity is restored.
 */
export default function NetworkBanner() {
    const status = useNetworkStatus();

    if (status === 'online') return null;

    return (
        <div className="fixed top-0 inset-x-0 z-[60] bg-amber-600 text-white text-center py-2 text-sm font-medium safe-area-top animate-fade-in">
            You're offline — some features may be unavailable
        </div>
    );
}

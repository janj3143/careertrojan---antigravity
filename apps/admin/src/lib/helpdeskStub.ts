export async function initHelpdeskStub(portal: 'admin' | 'user' | 'mentor') {
    try {
        const response = await fetch(`/api/support/v1/widget-config?portal=${portal}`, {
            method: 'GET',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) return;

        const payload = await response.json();
        (window as any).__CAREERTROJAN_HELPDESK__ = payload;
        window.dispatchEvent(new CustomEvent('careertrojan:helpdesk:ready', { detail: payload }));

        const scriptUrl = payload?.bootstrap?.config?.script_url as string | undefined;
        const widgetEnabled = Boolean(payload?.bootstrap?.config?.widget_enabled);
        if (widgetEnabled && scriptUrl && !(document.getElementById('careertrojan-helpdesk-script'))) {
            const script = document.createElement('script');
            script.id = 'careertrojan-helpdesk-script';
            script.src = scriptUrl;
            script.async = true;
            document.head.appendChild(script);
        }
    } catch {
        // no-op in stub mode
    }
}

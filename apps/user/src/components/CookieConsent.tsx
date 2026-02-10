import React, { useState, useEffect, useCallback } from 'react';

/* ------------------------------------------------------------------ */
/*  CookieConsent.tsx — GDPR Cookie Banner                            */
/*  Mounted globally in App.tsx, alongside NetworkBanner               */
/*  Track E, Step E6                                                   */
/* ------------------------------------------------------------------ */

interface CookiePreferences {
  necessary: true;       // always true — cannot be disabled
  functional: boolean;
  analytics: boolean;
  consentedAt: string;   // ISO timestamp
}

const STORAGE_KEY = 'ct_cookie_consent';
const CONSENT_API = '/api/gdpr/v1/consent';

const defaultPrefs: CookiePreferences = {
  necessary: true,
  functional: true,
  analytics: false,
  consentedAt: '',
};

/* ---- Inline styles ---- */
const bannerStyle: React.CSSProperties = {
  position: 'fixed',
  bottom: 0,
  left: 0,
  right: 0,
  zIndex: 9999,
  background: '#1a202c',
  color: '#e2e8f0',
  padding: '1rem 1.25rem',
  boxShadow: '0 -4px 24px rgba(0,0,0,0.25)',
  display: 'flex',
  flexWrap: 'wrap',
  alignItems: 'center',
  gap: '1rem',
  fontFamily: 'inherit',
  fontSize: '0.9rem',
  lineHeight: 1.6,
};

const btnBase: React.CSSProperties = {
  padding: '0.5rem 1.25rem',
  border: 'none',
  borderRadius: '6px',
  fontWeight: 600,
  cursor: 'pointer',
  fontSize: '0.85rem',
  whiteSpace: 'nowrap',
};

const btnAccept: React.CSSProperties = { ...btnBase, background: '#38a169', color: '#fff' };
const btnReject: React.CSSProperties = { ...btnBase, background: '#718096', color: '#fff' };
const btnCustomize: React.CSSProperties = { ...btnBase, background: 'transparent', color: '#90cdf4', textDecoration: 'underline' };

const toggleRow: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '0.4rem 0',
  borderBottom: '1px solid #2d3748',
};

/* ---- Helpers ---- */

function loadPrefs(): CookiePreferences | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function savePrefs(prefs: CookiePreferences) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
}

async function reportConsentToServer(prefs: CookiePreferences) {
  /* Only call backend when user is authenticated (JWT exists). */
  const token =
    localStorage.getItem('ct_access_token') ||
    sessionStorage.getItem('ct_access_token');
  if (!token) return;

  try {
    await fetch(CONSENT_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        consent_type: 'cookies',
        granted: prefs.analytics || prefs.functional,
        details: {
          necessary: true,
          functional: prefs.functional,
          analytics: prefs.analytics,
        },
      }),
    });
  } catch {
    /* Silently fail — consent is still stored locally. */
  }
}

/* ================================================================== */
/*  COMPONENT                                                          */
/* ================================================================== */

const CookieConsent: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [showCustomize, setShowCustomize] = useState(false);
  const [prefs, setPrefs] = useState<CookiePreferences>(defaultPrefs);

  useEffect(() => {
    const stored = loadPrefs();
    if (!stored) {
      setVisible(true); // first visit — show the banner
    }
  }, []);

  const persist = useCallback((p: CookiePreferences) => {
    const stamped = { ...p, consentedAt: new Date().toISOString() };
    savePrefs(stamped);
    reportConsentToServer(stamped);
    setVisible(false);
  }, []);

  /* ---- Actions ---- */
  const acceptAll = () => persist({ necessary: true, functional: true, analytics: true, consentedAt: '' });
  const rejectOptional = () => persist({ necessary: true, functional: false, analytics: false, consentedAt: '' });
  const saveCustom = () => persist(prefs);

  if (!visible) return null;

  return (
    <div style={bannerStyle} role="dialog" aria-label="Cookie consent">
      {/* Message */}
      <div style={{ flex: '1 1 400px' }}>
        We use cookies to keep you logged in and to improve your experience.
        See our <a href="/privacy#cookies" style={{ color: '#90cdf4' }}>Privacy Policy</a> for details.
      </div>

      {/* Buttons */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button style={btnAccept} onClick={acceptAll}>Accept All</button>
        <button style={btnReject} onClick={rejectOptional}>Reject Optional</button>
        <button style={btnCustomize} onClick={() => setShowCustomize(!showCustomize)}>
          {showCustomize ? 'Hide Options' : 'Customise'}
        </button>
      </div>

      {/* Customisation panel */}
      {showCustomize && (
        <div style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem', background: '#2d3748', borderRadius: '8px' }}>
          <div style={toggleRow}>
            <span>🔒 Strictly Necessary</span>
            <span style={{ color: '#a0aec0' }}>Always on</span>
          </div>
          <div style={toggleRow}>
            <label style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={prefs.functional}
                onChange={(e) => setPrefs({ ...prefs, functional: e.target.checked })}
                style={{ marginRight: '0.5rem' }}
              />
              Functional (preferences)
            </label>
          </div>
          <div style={toggleRow}>
            <label style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={prefs.analytics}
                onChange={(e) => setPrefs({ ...prefs, analytics: e.target.checked })}
                style={{ marginRight: '0.5rem' }}
              />
              Analytics (anonymised usage)
            </label>
          </div>
          <button style={{ ...btnAccept, marginTop: '0.75rem' }} onClick={saveCustom}>
            Save Preferences
          </button>
        </div>
      )}
    </div>
  );
};

export default CookieConsent;

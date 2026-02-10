import React from 'react';

/* ------------------------------------------------------------------ */
/*  PrivacyPolicy.tsx — UK GDPR-Compliant Privacy Policy              */
/*  Route: /privacy  (public, no auth required)                       */
/*  Track E, Step E6                                                   */
/* ------------------------------------------------------------------ */

const sectionStyle: React.CSSProperties = { marginBottom: '2rem' };
const h2Style: React.CSSProperties = { fontSize: '1.4rem', fontWeight: 700, margin: '1.5rem 0 0.75rem' };
const h3Style: React.CSSProperties = { fontSize: '1.15rem', fontWeight: 600, margin: '1.25rem 0 0.5rem' };
const pStyle: React.CSSProperties = { lineHeight: 1.7, marginBottom: '0.75rem', color: '#333' };
const listStyle: React.CSSProperties = { lineHeight: 1.7, paddingLeft: '1.5rem', marginBottom: '0.75rem' };

const EFFECTIVE_DATE = '1 June 2025';
const COMPANY_NAME = 'CareerTrojan';
const CONTACT_EMAIL = 'privacy@careertrojan.com';

const PrivacyPolicy: React.FC = () => (
  <div style={{ maxWidth: 820, margin: '0 auto', padding: '2rem 1.25rem 4rem' }}>
    <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>Privacy Policy</h1>
    <p style={{ color: '#666', marginBottom: '2rem' }}>Effective date: {EFFECTIVE_DATE}</p>

    {/* 1 — WHO WE ARE */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>1. Who We Are</h2>
      <p style={pStyle}>
        {COMPANY_NAME} ("we", "us", "our") operates the CareerTrojan platform — an AI-powered
        career coaching and job-matching service. We are the data controller for your personal
        data under the UK General Data Protection Regulation (UK GDPR) and the Data Protection
        Act 2018.
      </p>
      <p style={pStyle}>
        <strong>Contact:</strong> {CONTACT_EMAIL}
      </p>
    </section>

    {/* 2 — WHAT DATA WE COLLECT */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>2. What Data We Collect</h2>

      <h3 style={h3Style}>2.1 Data you provide directly</h3>
      <ul style={listStyle}>
        <li>Account details — name, email, password (hashed)</li>
        <li>Profile information — skills, experience level, industry preferences, LinkedIn/GitHub URLs</li>
        <li>CV / resume uploads (PDF, DOCX)</li>
        <li>Coaching session questions and feedback</li>
        <li>Payment selection (plan choice, promo codes — card details are held solely by Braintree, our payment processor)</li>
      </ul>

      <h3 style={h3Style}>2.2 Data we collect automatically</h3>
      <ul style={listStyle}>
        <li>Usage data — pages visited, features used, time on page</li>
        <li>Device information — browser type, operating system, screen size</li>
        <li>IP address (hashed after 30 days)</li>
        <li>Session identifiers and authentication tokens</li>
        <li>AI match results — which job recommendations were shown and how you responded</li>
      </ul>

      <h3 style={h3Style}>2.3 Data from third parties</h3>
      <ul style={listStyle}>
        <li>Payment confirmation from Braintree (transaction IDs, subscription status)</li>
      </ul>
    </section>

    {/* 3 — WHY WE COLLECT IT */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>3. Why We Collect Your Data (Legal Bases)</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '1rem' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
            <th style={{ padding: '0.5rem' }}>Purpose</th>
            <th style={{ padding: '0.5rem' }}>Legal Basis (UK GDPR)</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['Provide your account & core features', 'Performance of contract'],
            ['Process payments', 'Performance of contract'],
            ['AI job matching & coaching', 'Performance of contract'],
            ['Improve our AI models (anonymised data)', 'Legitimate interest'],
            ['Usage analytics', 'Legitimate interest'],
            ['Fraud prevention & security', 'Legitimate interest'],
            ['Marketing emails (opt-in only)', 'Consent'],
            ['Cookie analytics (optional)', 'Consent'],
            ['Legal & tax record retention', 'Legal obligation'],
          ].map(([purpose, basis], i) => (
            <tr key={i} style={{ borderBottom: '1px solid #e2e8f0' }}>
              <td style={{ padding: '0.5rem' }}>{purpose}</td>
              <td style={{ padding: '0.5rem' }}>{basis}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>

    {/* 4 — AI AND YOUR DATA */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>4. How We Use AI With Your Data</h2>
      <p style={pStyle}>
        CareerTrojan uses artificial intelligence to match you with relevant job opportunities,
        provide coaching suggestions, and analyse your CV. Specifically:
      </p>
      <ul style={listStyle}>
        <li>Your CV text, skills, and preferences are processed by our matching engine to score job relevance.</li>
        <li>Coaching conversations are analysed to generate personalised career advice.</li>
        <li>Anonymised, aggregated interaction data (e.g., "X % of users in sector Y clicked on role Z") is used to improve model accuracy. Individual users cannot be re-identified from training data.</li>
        <li>No automated decisions with legal effect are made — all final career decisions remain yours.</li>
      </ul>
    </section>

    {/* 5 — DATA RETENTION */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>5. How Long We Keep Your Data</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '1rem' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
            <th style={{ padding: '0.5rem' }}>Category</th>
            <th style={{ padding: '0.5rem' }}>Retention</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['Profile & account data', 'Until you delete your account'],
            ['CVs & resumes', 'Until you delete your account'],
            ['Job search & match data', '12 months'],
            ['Coaching sessions', '12 months'],
            ['Session / usage logs', '90 days'],
            ['Feedback signals', '24 months (critical for model quality)'],
            ['Payment records', '7 years (UK tax/accounting requirement)'],
            ['Consent records', '7 years (compliance proof)'],
          ].map(([cat, ret], i) => (
            <tr key={i} style={{ borderBottom: '1px solid #e2e8f0' }}>
              <td style={{ padding: '0.5rem' }}>{cat}</td>
              <td style={{ padding: '0.5rem' }}>{ret}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>

    {/* 6 — YOUR RIGHTS */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>6. Your Rights Under UK GDPR</h2>
      <p style={pStyle}>You have the right to:</p>
      <ul style={listStyle}>
        <li><strong>Access</strong> (Article 15) — Request a copy of all data we hold about you.</li>
        <li><strong>Rectification</strong> (Article 16) — Correct inaccurate or incomplete data.</li>
        <li><strong>Erasure</strong> (Article 17) — Request deletion of your data ("right to be forgotten"). Note: we must retain payment and consent records for legal obligations.</li>
        <li><strong>Data Portability</strong> (Article 20) — Receive your data in a machine-readable format (JSON).</li>
        <li><strong>Restrict Processing</strong> (Article 18) — Limit how we use your data while a dispute is resolved.</li>
        <li><strong>Object</strong> (Article 21) — Object to processing based on legitimate interest.</li>
        <li><strong>Withdraw Consent</strong> (Article 7) — Revoke consent at any time (e.g., marketing emails, optional cookies).</li>
      </ul>
      <p style={pStyle}>
        To exercise any right, email <strong>{CONTACT_EMAIL}</strong> or use the self-service
        options in your <strong>Account Settings → Data &amp; Privacy</strong> page. We respond
        within 30 days.
      </p>
    </section>

    {/* 7 — COOKIES */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>7. Cookies</h2>
      <p style={pStyle}>We use the following types of cookies:</p>
      <ul style={listStyle}>
        <li><strong>Strictly necessary</strong> — Session cookies, CSRF tokens. Cannot be disabled.</li>
        <li><strong>Functional</strong> — Remember your preferences (dark mode, language). Optional.</li>
        <li><strong>Analytics</strong> — Anonymised usage data to improve the platform. Optional.</li>
      </ul>
      <p style={pStyle}>
        You can manage cookie preferences at any time via the cookie banner or your account settings.
        We do not use advertising or tracking cookies.
      </p>
    </section>

    {/* 8 — DATA SHARING */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>8. Who We Share Data With</h2>
      <ul style={listStyle}>
        <li><strong>Braintree (PayPal)</strong> — Payment processing. They are an independent controller for card data. See <a href="https://www.braintreepayments.com/legal" target="_blank" rel="noreferrer">Braintree Privacy Policy</a>.</li>
        <li><strong>Hosting provider</strong> — Our servers run on infrastructure within the UK/EEA. No data is transferred outside the UK without adequate safeguards.</li>
        <li><strong>We never sell your data.</strong></li>
      </ul>
    </section>

    {/* 9 — SECURITY */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>9. Data Security</h2>
      <p style={pStyle}>
        We protect your data with: HTTPS encryption in transit, bcrypt-hashed passwords,
        JWT-based authentication with short-lived tokens, role-based access controls,
        automated daily backups, and regular security reviews.
      </p>
    </section>

    {/* 10 — CHILDREN */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>10. Children</h2>
      <p style={pStyle}>
        CareerTrojan is intended for users aged 16 and over. We do not knowingly collect data
        from anyone under 16. If you believe we have, contact us immediately and we will delete it.
      </p>
    </section>

    {/* 11 — CHANGES */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>11. Changes to This Policy</h2>
      <p style={pStyle}>
        We may update this policy from time to time. Material changes will be communicated via
        email or an in-app notification. The "Effective date" at the top will always reflect the
        latest version.
      </p>
    </section>

    {/* 12 — COMPLAINTS */}
    <section style={sectionStyle}>
      <h2 style={h2Style}>12. Complaints</h2>
      <p style={pStyle}>
        If you are unhappy with how we handle your data, please contact us first at{' '}
        <strong>{CONTACT_EMAIL}</strong>. You also have the right to lodge a complaint with the{' '}
        <a href="https://ico.org.uk/make-a-complaint/" target="_blank" rel="noreferrer">
          Information Commissioner's Office (ICO)
        </a>.
      </p>
    </section>
  </div>
);

export default PrivacyPolicy;

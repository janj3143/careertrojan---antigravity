/**
 * Braintree Drop-in UI Component — CareerTrojan
 * ================================================
 * Renders the Braintree Drop-in payment form (cards, PayPal, Apple Pay, etc.)
 * inside a container div. Fetches a client token from the backend, initialises
 * the SDK, and returns a payment method nonce on submission.
 *
 * Usage:
 *   <BraintreeDropIn
 *     onPaymentNonce={(nonce) => submitToBackend(nonce)}
 *     onError={(msg) => setError(msg)}
 *     disabled={processing}
 *   />
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';

// --- Types for Braintree Drop-in SDK (loaded from CDN) ---
declare global {
    interface Window {
        braintree?: {
            dropin: {
                create: (options: any) => Promise<any>;
            };
        };
    }
}

interface BraintreeDropInProps {
    /** Called with the payment method nonce when user completes form */
    onPaymentNonce: (nonce: string, type: string) => void;
    /** Called if an error occurs during SDK init or tokenisation */
    onError?: (message: string) => void;
    /** Whether the submit button should be disabled (e.g. while processing) */
    disabled?: boolean;
    /** Label for the pay button */
    buttonLabel?: string;
    /** Amount to display (informational only — backend controls actual charge) */
    amount?: string;
}

const API_BASE = '/api/payment/v1';

/** Load the Braintree Drop-in SDK from CDN if not already loaded */
function loadDropInScript(): Promise<void> {
    return new Promise((resolve, reject) => {
        if (window.braintree?.dropin) {
            resolve();
            return;
        }
        const existing = document.getElementById('braintree-dropin-script');
        if (existing) {
            existing.addEventListener('load', () => resolve());
            return;
        }
        const script = document.createElement('script');
        script.id = 'braintree-dropin-script';
        script.src = 'https://js.braintreegateway.com/web/dropin/1.46.0/js/dropin.min.js';
        script.async = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load Braintree Drop-in SDK'));
        document.head.appendChild(script);
    });
}

export default function BraintreeDropIn({
    onPaymentNonce,
    onError,
    disabled = false,
    buttonLabel = 'Pay Now',
    amount,
}: BraintreeDropInProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const instanceRef = useRef<any>(null);
    const [ready, setReady] = useState(false);
    const [loading, setLoading] = useState(true);
    const [tokenising, setTokenising] = useState(false);

    // -- Fetch client token & init --
    useEffect(() => {
        let cancelled = false;

        async function init() {
            try {
                // 1. Load SDK
                await loadDropInScript();

                // 2. Fetch client token from backend
                const token = localStorage.getItem('token');
                const res = await fetch(`${API_BASE}/client-token`, {
                    headers: token ? { Authorization: `Bearer ${token}` } : {},
                });
                if (!res.ok) throw new Error('Could not fetch client token');
                const { client_token } = await res.json();

                if (cancelled || !containerRef.current) return;

                // 3. Teardown previous instance
                if (instanceRef.current) {
                    await instanceRef.current.teardown();
                    instanceRef.current = null;
                }

                // 4. Create Drop-in with all payment methods
                const instance = await window.braintree!.dropin.create({
                    authorization: client_token,
                    container: containerRef.current,
                    card: {
                        cardholderName: { required: true },
                        overrides: {
                            fields: {
                                postalCode: { prefill: '' },
                            },
                        },
                    },
                    // PayPal — enabled automatically when linked in Braintree dashboard
                    paypal: {
                        flow: 'vault',              // save for recurring
                        buttonStyle: {
                            color: 'blue',
                            shape: 'rect',
                            size: 'responsive',
                        },
                    },
                    // Apple Pay — requires verified domain in Braintree dashboard
                    applePay: {
                        displayName: 'CareerTrojan',
                        paymentRequest: {
                            total: { label: 'CareerTrojan', amount: amount || '0.00' },
                            requiredBillingContactFields: ['postalAddress'],
                        },
                    },
                    // Google Pay — requires merchant ID in Braintree dashboard
                    googlePay: {
                        merchantId: 'CareerTrojan',
                        transactionInfo: {
                            totalPriceStatus: 'FINAL',
                            totalPrice: amount || '0.00',
                            currencyCode: 'GBP',
                        },
                    },
                    // Venmo (US users)
                    venmo: { allowNewBrowserTab: false },
                });

                if (cancelled) {
                    await instance.teardown();
                    return;
                }

                instanceRef.current = instance;
                setReady(true);
            } catch (err: any) {
                if (!cancelled) onError?.(err.message || 'Payment form failed to load');
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        init();

        return () => {
            cancelled = true;
            instanceRef.current?.teardown().catch(() => {});
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // -- Submit handler --
    const handleSubmit = useCallback(async () => {
        if (!instanceRef.current || disabled || tokenising) return;

        setTokenising(true);
        try {
            const { nonce, type } = await instanceRef.current.requestPaymentMethod();
            onPaymentNonce(nonce, type);
        } catch (err: any) {
            onError?.(err.message || 'Please complete the payment form');
        } finally {
            setTokenising(false);
        }
    }, [disabled, tokenising, onPaymentNonce, onError]);

    return (
        <div className="braintree-dropin-wrapper">
            {loading && (
                <div className="flex items-center justify-center py-8">
                    <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                    <span className="ml-3 text-sm text-gray-500">Loading payment form…</span>
                </div>
            )}

            {/* Braintree mounts its UI here */}
            <div ref={containerRef} className={loading ? 'hidden' : ''} />

            {ready && (
                <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={disabled || tokenising}
                    className="w-full mt-4 bg-green-600 text-white py-3 rounded-lg font-bold text-lg
                               hover:bg-green-700 transition shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {tokenising
                        ? 'Processing…'
                        : amount
                            ? `${buttonLabel} — $${amount}`
                            : buttonLabel}
                </button>
            )}

            <div className="mt-4 flex items-center justify-center gap-3 text-gray-400 text-xs">
                <span>Visa</span>
                <span>Mastercard</span>
                <span>Amex</span>
                <span>PayPal</span>
                <span>Apple Pay</span>
                <span>Google Pay</span>
            </div>
            <p className="text-xs text-gray-500 text-center mt-2 flex items-center justify-center gap-1">
                <span>🔒</span> Secured by Braintree (a PayPal service). Your details are encrypted.
            </p>
        </div>
    );
}

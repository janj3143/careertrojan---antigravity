/**
 * Saved Payment Methods — CareerTrojan
 * =====================================
 * Displays the user's vaulted cards / PayPal from Braintree.
 * Allows selecting a saved method or deleting it.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { CreditCard, Trash2, CheckCircle } from 'lucide-react';

interface PaymentMethod {
    token: string;
    type: 'card' | 'paypal' | string;
    card_type?: string;
    last4?: string;
    expiration?: string;
    email?: string;
    default: boolean;
}

interface SavedPaymentMethodsProps {
    /** Called when user selects a saved method token */
    onSelect: (token: string) => void;
    /** Currently selected token (controlled) */
    selectedToken?: string | null;
}

const API_BASE = '/api/payment/v1';

function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function SavedPaymentMethods({ onSelect, selectedToken }: SavedPaymentMethodsProps) {
    const [methods, setMethods] = useState<PaymentMethod[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchMethods = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/methods`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                const data = await res.json();
                setMethods(data.methods || []);
            }
        } catch {
            // silently fail — user just won't see saved methods
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchMethods();
    }, [fetchMethods]);

    const handleDelete = async (token: string) => {
        if (!confirm('Remove this payment method?')) return;
        try {
            await fetch(`${API_BASE}/methods/${token}`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
            });
            setMethods(prev => prev.filter(m => m.token !== token));
        } catch {
            // ignore
        }
    };

    if (loading) {
        return <div className="text-sm text-gray-400 py-2">Loading saved methods…</div>;
    }

    if (methods.length === 0) return null;

    return (
        <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-600 mb-3">Saved Payment Methods</h4>
            <div className="space-y-2">
                {methods.map(m => (
                    <div
                        key={m.token}
                        onClick={() => onSelect(m.token)}
                        className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition
                            ${selectedToken === m.token
                                ? 'border-indigo-600 bg-indigo-50 ring-1 ring-indigo-200'
                                : 'border-gray-200 hover:border-gray-300 bg-white'}`}
                    >
                        <div className="flex items-center gap-3">
                            {selectedToken === m.token ? (
                                <CheckCircle className="w-5 h-5 text-indigo-600" />
                            ) : (
                                <CreditCard className="w-5 h-5 text-gray-400" />
                            )}
                            <div>
                                {m.type === 'card' ? (
                                    <span className="text-sm font-medium text-gray-800">
                                        {m.card_type} •••• {m.last4}
                                        <span className="ml-2 text-gray-400 text-xs">{m.expiration}</span>
                                    </span>
                                ) : m.type === 'paypal' ? (
                                    <span className="text-sm font-medium text-gray-800">
                                        PayPal — {m.email}
                                    </span>
                                ) : (
                                    <span className="text-sm text-gray-600">{m.type}</span>
                                )}
                                {m.default && (
                                    <span className="ml-2 text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                                        Default
                                    </span>
                                )}
                            </div>
                        </div>
                        <button
                            onClick={(e) => { e.stopPropagation(); handleDelete(m.token); }}
                            className="p-1 text-gray-400 hover:text-red-500 transition"
                            title="Remove"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Or use a new payment method below</p>
        </div>
    );
}

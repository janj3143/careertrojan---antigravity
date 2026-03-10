/**
 * Payment Confirmation Modal — CareerTrojan
 * ==========================================
 * Shows plan details + asks user to confirm before charging.
 *
 * Usage:
 *   <PaymentConfirmModal
 *     open={showConfirm}
 *     plan={selectedPlan}
 *     discount={discountAmount}
 *     onConfirm={() => processPayment()}
 *     onCancel={() => setShowConfirm(false)}
 *     processing={isProcessing}
 *   />
 */

import React from 'react';
import { ShieldCheck, CreditCard, Calendar } from 'lucide-react';
import Modal from '../Modal';

interface Plan {
    id: string;
    name: string;
    price: number;
    currency: string;
    interval: string | null;
    features: string[];
}

interface PaymentConfirmModalProps {
    open: boolean;
    plan: Plan | null;
    discount?: number;
    promoCode?: string;
    onConfirm: () => void;
    onCancel: () => void;
    processing?: boolean;
}

export default function PaymentConfirmModal({
    open,
    plan,
    discount = 0,
    promoCode,
    onConfirm,
    onCancel,
    processing = false,
}: PaymentConfirmModalProps) {
    if (!plan) return null;

    const finalPrice = Math.max(0, plan.price - discount);

    return (
        <Modal
            open={open}
            onClose={onCancel}
            title="Confirm Subscription"
            persistent={processing}
            footer={
                <div className="flex gap-3 justify-end">
                    <button
                        onClick={onCancel}
                        disabled={processing}
                        className="px-4 py-2 rounded-lg border border-gray-200 text-gray-600
                                   hover:bg-gray-100 transition disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={processing}
                        className="px-6 py-2 rounded-lg bg-indigo-600 text-white font-semibold
                                   hover:bg-indigo-700 transition shadow-lg disabled:opacity-50
                                   flex items-center gap-2"
                    >
                        {processing ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Processing…
                            </>
                        ) : (
                            <>
                                <CreditCard className="w-4 h-4" />
                                Pay ${finalPrice.toFixed(2)}
                            </>
                        )}
                    </button>
                </div>
            }
        >
            <div className="space-y-5">
                {/* Plan summary */}
                <div className="bg-indigo-50 rounded-xl p-4">
                    <h3 className="font-bold text-indigo-900 text-lg">{plan.name}</h3>
                    <div className="mt-1 flex items-baseline gap-1">
                        <span className="text-2xl font-extrabold text-indigo-700">
                            ${finalPrice.toFixed(2)}
                        </span>
                        {plan.interval && (
                            <span className="text-sm text-indigo-500">/{plan.interval}</span>
                        )}
                    </div>
                    {discount > 0 && (
                        <div className="mt-2 text-sm text-green-700 flex items-center gap-1">
                            <span className="line-through text-gray-400">${plan.price.toFixed(2)}</span>
                            — {promoCode && <span className="font-medium">{promoCode}</span>} saves you ${discount.toFixed(2)}
                        </div>
                    )}
                </div>

                {/* Features */}
                <ul className="space-y-2">
                    {plan.features.map((feat, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                            <span className="text-green-500 mt-0.5">✓</span>
                            {feat}
                        </li>
                    ))}
                </ul>

                {/* Billing info */}
                <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
                    <Calendar className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div>
                        {plan.interval === 'month'
                            ? 'You will be charged monthly. Cancel any time before the next billing cycle.'
                            : plan.interval === 'year'
                                ? 'Annual billing — that\'s 2 months free compared to monthly.'
                                : 'One-time charge. No recurring billing.'}
                    </div>
                </div>

                {/* Security note */}
                <div className="flex items-center gap-2 text-xs text-gray-400">
                    <ShieldCheck className="w-4 h-4" />
                    <span>Payment processed securely by Braintree (a PayPal service). PCI SAQ-A compliant.</span>
                </div>
            </div>
        </Modal>
    );
}

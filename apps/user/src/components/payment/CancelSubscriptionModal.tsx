/**
 * Cancel Subscription Modal — CareerTrojan
 * ==========================================
 * Asks for confirmation before cancelling the user's subscription.
 */

import React from 'react';
import { AlertTriangle } from 'lucide-react';
import Modal from '../Modal';

interface CancelSubscriptionModalProps {
    open: boolean;
    planName?: string;
    effectiveDate?: string;
    onConfirm: () => void;
    onCancel: () => void;
    processing?: boolean;
}

export default function CancelSubscriptionModal({
    open,
    planName,
    effectiveDate,
    onConfirm,
    onCancel,
    processing = false,
}: CancelSubscriptionModalProps) {
    return (
        <Modal
            open={open}
            onClose={onCancel}
            title="Cancel Subscription"
            persistent={processing}
            footer={
                <div className="flex gap-3 justify-end">
                    <button
                        onClick={onCancel}
                        disabled={processing}
                        className="px-4 py-2 rounded-lg border border-gray-200 text-gray-600
                                   hover:bg-gray-100 transition disabled:opacity-50"
                    >
                        Keep Plan
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={processing}
                        className="px-5 py-2 rounded-lg bg-red-600 text-white font-semibold
                                   hover:bg-red-700 transition disabled:opacity-50 flex items-center gap-2"
                    >
                        {processing ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Cancelling…
                            </>
                        ) : (
                            'Yes, Cancel Subscription'
                        )}
                    </button>
                </div>
            }
        >
            <div className="space-y-4">
                <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                        <AlertTriangle className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                        <p className="text-gray-800 font-medium">
                            Are you sure you want to cancel {planName ? <strong>{planName}</strong> : 'your subscription'}?
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                            {effectiveDate
                                ? `Your access will continue until ${new Date(effectiveDate).toLocaleDateString()}. After that, you'll be moved to the Free plan.`
                                : 'You will lose access to premium features at the end of your current billing period.'}
                        </p>
                    </div>
                </div>

                <div className="bg-amber-50 rounded-lg p-3 text-sm text-amber-800">
                    <strong>What you'll lose:</strong>
                    <ul className="mt-1 ml-5 list-disc space-y-1">
                        <li>Unlimited AI analysis</li>
                        <li>Resume tuning & application tracker</li>
                        <li>Interview coaching sessions</li>
                        <li>Priority support</li>
                    </ul>
                </div>
            </div>
        </Modal>
    );
}

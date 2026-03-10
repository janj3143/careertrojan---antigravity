/**
 * Payment Result Modal — CareerTrojan
 * =====================================
 * Shown after payment succeeds or fails.
 * Success: receipt summary, auto-redirect after 5s.
 * Failure: error message + retry button.
 */

import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Modal from '../Modal';

interface PaymentResultModalProps {
    open: boolean;
    success: boolean;
    planName?: string;
    amount?: number;
    message?: string;
    nextBillingDate?: string;
    onClose: () => void;
    onRetry?: () => void;
}

export default function PaymentResultModal({
    open,
    success,
    planName,
    amount,
    message,
    nextBillingDate,
    onClose,
    onRetry,
}: PaymentResultModalProps) {
    const navigate = useNavigate();
    const [countdown, setCountdown] = useState(5);

    // Auto-redirect on success
    useEffect(() => {
        if (!open || !success) {
            setCountdown(5);
            return;
        }
        const timer = setInterval(() => {
            setCountdown((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    navigate('/dashboard');
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
        return () => clearInterval(timer);
    }, [open, success, navigate]);

    return (
        <Modal
            open={open}
            onClose={onClose}
            hideCloseButton={success}
            persistent={success}
            footer={
                <div className="flex justify-end gap-3">
                    {success ? (
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="px-5 py-2 rounded-lg bg-green-600 text-white font-semibold
                                       hover:bg-green-700 transition flex items-center gap-2"
                        >
                            Go to Dashboard <ArrowRight className="w-4 h-4" />
                        </button>
                    ) : (
                        <>
                            <button
                                onClick={onClose}
                                className="px-4 py-2 rounded-lg border border-gray-200 text-gray-600
                                           hover:bg-gray-100 transition"
                            >
                                Close
                            </button>
                            {onRetry && (
                                <button
                                    onClick={onRetry}
                                    className="px-5 py-2 rounded-lg bg-indigo-600 text-white font-semibold
                                               hover:bg-indigo-700 transition"
                                >
                                    Try Again
                                </button>
                            )}
                        </>
                    )}
                </div>
            }
        >
            <div className="text-center space-y-4 py-2">
                {success ? (
                    <>
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100">
                            <CheckCircle className="w-10 h-10 text-green-600" />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900">Payment Successful!</h3>
                        <p className="text-gray-600">
                            {message || `You are now subscribed to ${planName || 'your plan'}.`}
                        </p>

                        {/* Receipt summary */}
                        <div className="bg-gray-50 rounded-xl p-4 text-left text-sm space-y-2 mt-4">
                            {planName && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Plan</span>
                                    <span className="font-medium text-gray-900">{planName}</span>
                                </div>
                            )}
                            {amount !== undefined && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Amount Charged</span>
                                    <span className="font-medium text-gray-900">${amount.toFixed(2)}</span>
                                </div>
                            )}
                            {nextBillingDate && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Next Billing</span>
                                    <span className="font-medium text-gray-900">
                                        {new Date(nextBillingDate).toLocaleDateString()}
                                    </span>
                                </div>
                            )}
                        </div>

                        <p className="text-xs text-gray-400 mt-3">
                            Redirecting to dashboard in {countdown}s…
                        </p>
                    </>
                ) : (
                    <>
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100">
                            <XCircle className="w-10 h-10 text-red-500" />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900">Payment Failed</h3>
                        <p className="text-gray-600">
                            {message || 'Your payment could not be processed. Please check your details and try again.'}
                        </p>
                    </>
                )}
            </div>
        </Modal>
    );
}

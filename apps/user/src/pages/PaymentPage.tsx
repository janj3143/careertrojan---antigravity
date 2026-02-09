import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BraintreeDropIn from '../components/payment/BraintreeDropIn';
import SavedPaymentMethods from '../components/payment/SavedPaymentMethods';

const API_CONFIG = {
    baseUrl: "/api/payment/v1",
};

interface Plan {
    id: string;
    name: string;
    price: number;
    currency: string;
    interval: string | null;
    features: string[];
}

export default function PaymentPage() {
    const navigate = useNavigate();
    const [plans, setPlans] = useState<Plan[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [savedMethodToken, setSavedMethodToken] = useState<string | null>(null);
    const [promoCode, setPromoCode] = useState('');
    const [gatewayEnv, setGatewayEnv] = useState<string | null>(null);

    useEffect(() => {
        fetchPlans();
        fetchGatewayInfo();
    }, []);

    const fetchPlans = async () => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return;

            const res = await fetch(`${API_CONFIG.baseUrl}/plans`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setPlans(data.plans || []);
            }
        } catch (e) {
            console.error(e);
            setError("Failed to load plans.");
        } finally {
            setLoading(false);
        }
    };

    const fetchGatewayInfo = async () => {
        try {
            const res = await fetch(`${API_CONFIG.baseUrl}/gateway-info`);
            if (res.ok) {
                const data = await res.json();
                setGatewayEnv(data.environment);
            }
        } catch { /* ignore */ }
    };

    /** Process payment with a Braintree nonce (new card / PayPal) */
    const handleBraintreeNonce = async (nonce: string, _type: string) => {
        if (!selectedPlan) return;
        await submitPayment({ payment_method_nonce: nonce });
    };

    /** Process payment with a saved/vaulted payment method */
    const handleSavedMethodPay = async () => {
        if (!selectedPlan || !savedMethodToken) return;
        await submitPayment({ payment_method_token: savedMethodToken });
    };

    const submitPayment = async (
        paymentData: { payment_method_nonce?: string; payment_method_token?: string }
    ) => {
        if (!selectedPlan) return;
        setProcessing(true);
        setError(null);
        setSuccess(null);

        try {
            const token = localStorage.getItem("token");
            if (!token) throw new Error("Not logged in");

            // Free plan — no payment needed
            if (selectedPlan === 'free') {
                paymentData = {};
            }

            const res = await fetch(`${API_CONFIG.baseUrl}/process`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    plan_id: selectedPlan,
                    ...paymentData,
                    promo_code: promoCode || undefined,
                })
            });

            if (!res.ok) {
                const txt = await res.text();
                throw new Error(txt || "Payment failed");
            }

            const result = await res.json();
            setSuccess(result.message || 'Payment successful!');

            // Navigate to verification after short delay
            setTimeout(() => navigate('/verify'), 2000);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setProcessing(false);
        }
    };

    const selectedPlanData = plans.find(p => p.id === selectedPlan);

    if (loading) return <div className="p-8">Loading plans...</div>;

    return (
        <div className="p-4 sm:p-8 max-w-6xl mx-auto">
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">💳 Select Your Plan</h1>
            <p className="text-gray-600 mb-6 sm:mb-8">Choose the plan that fits your career goals.</p>

            {/* Sandbox indicator */}
            {gatewayEnv === 'sandbox' && (
                <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
                    <strong>🧪 Sandbox Mode</strong> — Use test card <code className="bg-amber-100 px-1 rounded">4111 1111 1111 1111</code> with any future expiry & CVV.
                </div>
            )}

            {error && (
                <div className="mb-6 p-4 bg-red-100 text-red-700 rounded-lg">
                    {error}
                </div>
            )}
            {success && (
                <div className="mb-6 p-4 bg-green-100 text-green-700 rounded-lg">
                    ✅ {success}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
                {plans.map((plan) => (
                    <div
                        key={plan.id}
                        className={`border rounded-xl p-5 sm:p-6 flex flex-col transition hover:shadow-lg ${selectedPlan === plan.id ? 'border-indigo-600 ring-2 ring-indigo-100' : 'border-gray-200 bg-white'}`}
                        onClick={() => { setSelectedPlan(plan.id); setSavedMethodToken(null); }}
                    >
                        <div className="mb-4">
                            <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                            <div className="mt-2 text-3xl font-extrabold text-gray-900">
                                {plan.price === 0 ? "Free" : `$${plan.price}`}
                                {plan.interval && <span className="text-sm font-medium text-gray-500">/{plan.interval}</span>}
                            </div>
                        </div>

                        <ul className="mb-8 space-y-3 flex-1">
                            {plan.features.map((feat, idx) => (
                                <li key={idx} className="flex items-start">
                                    <span className="flex-shrink-0 text-green-500">✓</span>
                                    <span className="ml-3 text-sm text-gray-600">{feat}</span>
                                </li>
                            ))}
                        </ul>

                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPlan(plan.id);
                                setSavedMethodToken(null);
                                if (plan.id === 'free') {
                                    submitPayment({});
                                }
                            }}
                            className={`w-full py-2 px-4 rounded-lg font-medium transition-colors touch-target ${plan.id === 'elitepro'
                                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700'
                                    : plan.id === 'free'
                                        ? 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                                        : 'bg-indigo-600 text-white hover:bg-indigo-700'
                                }`}
                            disabled={processing}
                        >
                            {processing && selectedPlan === plan.id ? 'Processing...' : (plan.id === 'free' ? 'Start Free Trial' : 'Select Plan')}
                        </button>
                    </div>
                ))}
            </div>

            {/* ── Braintree Payment Form for Paid Plans ── */}
            {selectedPlan && selectedPlan !== 'free' && (
                <div className="mt-8 sm:mt-12 bg-gray-50 p-5 sm:p-8 rounded-xl border border-gray-200 animate-fade-in">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                        Complete Payment — {selectedPlanData?.name}
                    </h3>
                    <p className="text-gray-500 text-sm mb-6">
                        ${selectedPlanData?.price}{selectedPlanData?.interval ? `/${selectedPlanData.interval}` : ''}
                    </p>

                    {/* Promo code */}
                    <div className="mb-6 max-w-sm">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Promo Code</label>
                        <input
                            type="text"
                            placeholder="LAUNCH20"
                            value={promoCode}
                            onChange={e => setPromoCode(e.target.value.toUpperCase())}
                            className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 border text-sm"
                        />
                    </div>

                    {/* Saved payment methods */}
                    <SavedPaymentMethods
                        onSelect={(token) => setSavedMethodToken(token)}
                        selectedToken={savedMethodToken}
                    />

                    {/* Pay with saved method button */}
                    {savedMethodToken && (
                        <button
                            onClick={handleSavedMethodPay}
                            disabled={processing}
                            className="w-full mb-6 bg-indigo-600 text-white py-3 rounded-lg font-bold text-lg
                                       hover:bg-indigo-700 transition shadow-lg disabled:opacity-50"
                        >
                            {processing ? 'Processing…' : `Pay with saved method — $${selectedPlanData?.price}`}
                        </button>
                    )}

                    {/* Braintree Drop-in (new card / PayPal) */}
                    {!savedMethodToken && (
                        <div className="max-w-md">
                            <BraintreeDropIn
                                onPaymentNonce={handleBraintreeNonce}
                                onError={(msg) => setError(msg)}
                                disabled={processing}
                                buttonLabel="Pay & Subscribe"
                                amount={selectedPlanData?.price.toString()}
                            />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

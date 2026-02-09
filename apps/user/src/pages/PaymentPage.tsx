import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API_CONFIG = {
    baseUrl: "http://localhost:8500",
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

    // Card State (Mock)
    const [cardDetails, setCardDetails] = useState({
        number: '',
        cvv: '',
        expiry: '',
        name: ''
    });

    useEffect(() => {
        fetchPlans();
    }, []);

    const fetchPlans = async () => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return;

            const res = await fetch(`${API_CONFIG.baseUrl}/api/payment/v1/plans`, {
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

    const handleSubscribe = async (planId: string) => {
        setProcessing(true);
        setError(null);

        try {
            const token = localStorage.getItem("token");
            if (!token) throw new Error("Not logged in");

            // Mock Stripe token for paid plans
            const stripeToken = planId !== 'free' ? "tok_visa_mock" : undefined;

            const res = await fetch(`${API_CONFIG.baseUrl}/api/payment/v1/process`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    plan_id: planId,
                    stripe_token: stripeToken
                })
            });

            if (!res.ok) {
                const txt = await res.text();
                throw new Error(txt || "Payment failed");
            }

            // Success
            navigate('/verify'); // Move to Step 07
        } catch (err: any) {
            setError(err.message);
        } finally {
            setProcessing(false);
        }
    };

    if (loading) return <div className="p-8">Loading plans...</div>;

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold mb-2">💳 Select Your Plan</h1>
            <p className="text-gray-600 mb-8">Choose the plan that fits your career goals.</p>

            {error && (
                <div className="mb-6 p-4 bg-red-100 text-red-700 rounded-lg">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {plans.map((plan) => (
                    <div
                        key={plan.id}
                        className={`border rounded-xl p-6 flex flex-col transition hover:shadow-lg ${selectedPlan === plan.id ? 'border-indigo-600 ring-2 ring-indigo-100' : 'border-gray-200 bg-white'}`}
                        onClick={() => setSelectedPlan(plan.id)}
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
                                if (plan.id === 'free') {
                                    handleSubscribe(plan.id);
                                }
                            }}
                            className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${plan.id === 'elitepro'
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

            {/* Payment Form for Paid Plans */}
            {selectedPlan && selectedPlan !== 'free' && (
                <div className="mt-12 bg-gray-50 p-8 rounded-xl border border-gray-200 animate-fade-in">
                    <h3 className="text-xl font-bold text-gray-900 mb-6">Enter Payment Details</h3>
                    <div className="max-w-md space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Card Number</label>
                            <input
                                type="text"
                                placeholder="0000 0000 0000 0000"
                                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 border"
                                value={cardDetails.number}
                                onChange={e => setCardDetails({ ...cardDetails, number: e.target.value })}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Expiry</label>
                                <input
                                    type="text"
                                    placeholder="MM/YY"
                                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 border"
                                    value={cardDetails.expiry}
                                    onChange={e => setCardDetails({ ...cardDetails, expiry: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">CVC</label>
                                <input
                                    type="text"
                                    placeholder="123"
                                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 border"
                                    value={cardDetails.cvv}
                                    onChange={e => setCardDetails({ ...cardDetails, cvv: e.target.value })}
                                />
                            </div>
                        </div>

                        <button
                            onClick={() => handleSubscribe(selectedPlan)}
                            disabled={processing}
                            className="w-full mt-4 bg-green-600 text-white py-3 rounded-lg font-bold text-lg hover:bg-green-700 transition shadow-lg"
                        >
                            {processing ? 'Processing...' : `Pay & Subscribe`}
                        </button>
                        <p className="text-xs text-gray-500 text-center mt-2">
                            <span className="mr-1">🔒</span> Secure 256-bit SSL Encrypted
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

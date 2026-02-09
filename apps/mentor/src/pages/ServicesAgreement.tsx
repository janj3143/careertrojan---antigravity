import React from 'react';
import MentorLayout from '../components/MentorLayout';
import { FileCheck, Download } from 'lucide-react';

export default function ServicesAgreement() {
    return (
        <MentorLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold text-white mb-6">📋 Services Agreement</h1>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-8">
                    <h2 className="text-2xl font-bold text-white mb-6">Mentor Services Agreement</h2>

                    <div className="prose prose-invert max-w-none space-y-4 text-slate-300">
                        <section>
                            <h3 className="text-lg font-semibold text-white mb-2">1. Services Provided</h3>
                            <p>As a CareerTrojan mentor, you agree to provide professional mentorship services including career guidance, skill development coaching, and professional networking support.</p>
                        </section>

                        <section>
                            <h3 className="text-lg font-semibold text-white mb-2">2. Payment Terms</h3>
                            <p>Mentors receive 80% of session fees. Platform retains 20% for service fees. Payments are processed via Stripe Connect and released 7 days after session completion.</p>
                        </section>

                        <section>
                            <h3 className="text-lg font-semibold text-white mb-2">3. Confidentiality</h3>
                            <p>All mentee information and session content must remain confidential. Mentors may not share mentee details without explicit consent.</p>
                        </section>

                        <section>
                            <h3 className="text-lg font-semibold text-white mb-2">4. Professional Conduct</h3>
                            <p>Mentors must maintain professional standards, provide quality guidance, and adhere to scheduled session times.</p>
                        </section>

                        <section>
                            <h3 className="text-lg font-semibold text-white mb-2">5. Termination</h3>
                            <p>Either party may terminate this agreement with 30 days notice. Active mentorship agreements must be completed or refunded.</p>
                        </section>
                    </div>

                    <div className="mt-8 pt-6 border-t border-slate-700">
                        <div className="flex items-center gap-4">
                            <button className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded transition">
                                <FileCheck size={20} />
                                I Accept
                            </button>
                            <button className="flex items-center gap-2 px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded transition">
                                <Download size={20} />
                                Download PDF
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </MentorLayout>
    );
}

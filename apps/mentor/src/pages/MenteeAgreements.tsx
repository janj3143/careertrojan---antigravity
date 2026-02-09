import React from 'react';
import MentorLayout from '../components/MentorLayout';
import { FileSignature, CheckCircle, Clock } from 'lucide-react';

export default function MenteeAgreements() {
    return (
        <MentorLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold text-white mb-6">📝 Mentee Agreements</h1>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <div className="text-center py-12">
                        <FileSignature size={64} className="mx-auto mb-4 text-slate-600" />
                        <p className="text-slate-400 mb-2">No pending agreements</p>
                        <p className="text-sm text-slate-500">New mentee agreements will appear here for your review</p>
                    </div>
                </div>
            </div>
        </MentorLayout>
    );
}

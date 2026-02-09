import React from 'react';
import MentorLayout from '../components/MentorLayout';
import { Shield, Star, MessageSquare } from 'lucide-react';

export default function GuardianFeedback() {
    return (
        <MentorLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold text-white mb-6">🛡️ Guardian Feedback</h1>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <div className="text-center py-12">
                        <Shield size={64} className="mx-auto mb-4 text-slate-600" />
                        <p className="text-slate-400 mb-2">No guardian feedback available</p>
                        <p className="text-sm text-slate-500">Feedback from the CareerTrojan Guardian system will appear here</p>
                    </div>
                </div>
            </div>
        </MentorLayout>
    );
}

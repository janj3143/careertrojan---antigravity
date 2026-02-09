import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function ScoringAnalytics() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Scoring Analytics"
                subtitle="Admin portal page"
                endpoint="/analytics/scoring"
            />
        </AdminLayout>
    );
}

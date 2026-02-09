import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function BiasAndFairness() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Bias and Fairness"
                subtitle="Admin portal page"
                endpoint="/analytics/fairness"
            />
        </AdminLayout>
    );
}

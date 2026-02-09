import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function EvaluationHarness() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Evaluation Harness"
                subtitle="Admin portal page"
                endpoint="/eval/runs"
            />
        </AdminLayout>
    );
}

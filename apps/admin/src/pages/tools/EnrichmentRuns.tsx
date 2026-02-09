import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function EnrichmentRuns() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Enrichment Runs"
                subtitle="Admin portal page"
                endpoint="/runs/enrichment"
            />
        </AdminLayout>
    );
}

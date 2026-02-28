import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsDiagnostics() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Diagnostics (Ops)"
                subtitle="Admin portal page"
                endpoint="/api/ops/v1/diagnostics"
            />
        </AdminLayout>
    );
}

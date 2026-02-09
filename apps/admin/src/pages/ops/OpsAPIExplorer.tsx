import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsAPIExplorer() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="API Explorer (Ops)"
                subtitle="Admin portal page"
                endpoint="/ops/api-explorer"
            />
        </AdminLayout>
    );
}

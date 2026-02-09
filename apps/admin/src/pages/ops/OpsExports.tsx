import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsExports() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Exports (Ops)"
                subtitle="Admin portal page"
                endpoint="/ops/exports"
            />
        </AdminLayout>
    );
}

import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function BlobStorage() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Blob Storage"
                subtitle="Admin portal page"
                endpoint="/api/ops/v1/blob"
            />
        </AdminLayout>
    );
}

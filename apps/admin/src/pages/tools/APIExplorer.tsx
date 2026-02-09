import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function APIExplorer() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="API Explorer"
                subtitle="Admin portal page"
                endpoint="/admin/api-explorer"
            />
        </AdminLayout>
    );
}

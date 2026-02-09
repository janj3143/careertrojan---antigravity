import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function TokenManagementAlt() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Token Management (Alt)"
                subtitle="Admin portal page"
                endpoint="/admin/tokens-alt"
            />
        </AdminLayout>
    );
}

import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function AdminAudit() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Admin Audit"
                subtitle="Admin portal page"
                endpoint="/audit/admin"
            />
        </AdminLayout>
    );
}

import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsAdminAudit() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Admin Audit (Ops)"
                subtitle="Admin portal page"
                endpoint="/audit/admin"
            />
        </AdminLayout>
    );
}

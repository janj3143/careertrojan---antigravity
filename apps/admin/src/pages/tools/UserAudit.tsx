import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function UserAudit() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="User Audit"
                subtitle="Admin portal page"
                endpoint="/audit/users"
            />
        </AdminLayout>
    );
}

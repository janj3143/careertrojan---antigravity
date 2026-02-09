import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function ConnectivityAudit() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="System Connectivity Audit"
                subtitle="Admin portal page"
                endpoint="/admin/connectivity"
            />
        </AdminLayout>
    );
}

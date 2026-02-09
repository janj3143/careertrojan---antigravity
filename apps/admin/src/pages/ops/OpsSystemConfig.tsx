import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsSystemConfig() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="System Config (Ops)"
                subtitle="Admin portal page"
                endpoint="/ops/config"
            />
        </AdminLayout>
    );
}

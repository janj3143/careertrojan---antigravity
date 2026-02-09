import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function Diagnostics() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Diagnostics"
                subtitle="Admin portal page"
                endpoint="/admin/diagnostics"
            />
        </AdminLayout>
    );
}

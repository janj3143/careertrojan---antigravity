import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function SystemConfig() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="System Config"
                subtitle="Admin portal page"
                endpoint="/admin/config"
            />
        </AdminLayout>
    );
}

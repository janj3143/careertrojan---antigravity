import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function DataRootsHealth() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Data Roots & Health"
                subtitle="Admin portal page"
                endpoint="/admin/data-health"
            />
        </AdminLayout>
    );
}

import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function Exports() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Exports"
                subtitle="Admin portal page"
                endpoint="/admin/exports"
            />
        </AdminLayout>
    );
}

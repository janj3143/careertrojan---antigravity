import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function ModelRegistry() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Model Registry"
                subtitle="Admin portal page"
                endpoint="/models/registry"
            />
        </AdminLayout>
    );
}

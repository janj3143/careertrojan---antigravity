import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsAbout() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="About (Ops)"
                subtitle="Admin portal page"
                endpoint="/ops/about"
            />
        </AdminLayout>
    );
}

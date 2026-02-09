import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function JobIndex() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Job Index"
                subtitle="Admin portal page"
                endpoint="/api/jobs/v1/index"
            />
        </AdminLayout>
    );
}

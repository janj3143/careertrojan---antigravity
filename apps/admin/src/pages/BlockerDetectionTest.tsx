import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function BlockerDetectionTest() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Blocker Detection Test"
                subtitle="Admin portal page"
                endpoint="/admin/blocker-test"
            />
        </AdminLayout>
    );
}

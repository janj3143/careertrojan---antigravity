import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function EmailCapture() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Email Capture"
                subtitle="Admin portal page"
                endpoint="/email/captured"
            />
        </AdminLayout>
    );
}

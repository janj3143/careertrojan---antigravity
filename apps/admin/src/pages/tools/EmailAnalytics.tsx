import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function EmailAnalytics() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Email Analytics"
                subtitle="Admin portal page"
                endpoint="/email/analytics"
            />
        </AdminLayout>
    );
}

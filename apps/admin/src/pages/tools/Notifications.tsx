import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function Notifications() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Notifications"
                subtitle="Admin portal page"
                endpoint="/admin/notifications"
            />
        </AdminLayout>
    );
}

import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsNotifications() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Notifications (Ops)"
                subtitle="Admin portal page"
                endpoint="/ops/notifications"
            />
        </AdminLayout>
    );
}

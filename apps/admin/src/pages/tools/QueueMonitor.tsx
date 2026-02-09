import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function QueueMonitor() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Queue Monitor"
                subtitle="Admin portal page"
                endpoint="/ops/queue"
            />
        </AdminLayout>
    );
}

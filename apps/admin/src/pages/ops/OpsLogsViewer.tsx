import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsLogsViewer() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Logs Viewer (Ops)"
                subtitle="Admin portal page"
                endpoint="/ops/logs"
            />
        </AdminLayout>
    );
}

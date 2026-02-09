import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function LogsViewer() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Logs Viewer"
                subtitle="Admin portal page"
                endpoint="/admin/logs-viewer"
            />
        </AdminLayout>
    );
}

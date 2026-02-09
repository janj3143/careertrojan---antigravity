import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsBackupRestore() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Backup & Restore (Ops)"
                subtitle="Admin portal page"
                endpoint="/ops/backup"
            />
        </AdminLayout>
    );
}

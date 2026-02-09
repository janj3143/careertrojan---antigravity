import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function BackupRestore() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Backup & Restore"
                subtitle="Admin portal page"
                endpoint="/admin/backup"
            />
        </AdminLayout>
    );
}

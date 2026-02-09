import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function DatasetsBrowser() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Datasets Browser"
                subtitle="Admin portal page"
                endpoint="/fs/list"
            />
        </AdminLayout>
    );
}

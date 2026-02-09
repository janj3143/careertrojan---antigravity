import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function RoleTaxonomy() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Role Taxonomy"
                subtitle="Admin portal page"
                endpoint="/api/taxonomy/v1/summary"
            />
        </AdminLayout>
    );
}

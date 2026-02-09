import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function About() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="About"
                subtitle="Admin portal page"
                endpoint="/admin/about"
            />
        </AdminLayout>
    );
}

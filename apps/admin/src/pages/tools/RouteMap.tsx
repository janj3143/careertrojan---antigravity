import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function RouteMap() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Route Map"
                subtitle="Admin portal page"
                endpoint="/admin/route-map"
            />
        </AdminLayout>
    );
}

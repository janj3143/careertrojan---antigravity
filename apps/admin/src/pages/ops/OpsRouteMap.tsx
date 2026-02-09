import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsRouteMap() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Route Map (Ops)"
                subtitle="Admin portal page"
                endpoint="/ops/route-map"
            />
        </AdminLayout>
    );
}

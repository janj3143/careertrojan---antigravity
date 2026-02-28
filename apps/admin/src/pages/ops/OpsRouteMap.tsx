import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function OpsRouteMap() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Route Map (Ops)"
                subtitle="Admin portal page"
                endpoint="/api/ops/v1/route-map"
            />
        </AdminLayout>
    );
}

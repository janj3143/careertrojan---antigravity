import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function ParserRuns() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Parser Runs"
                subtitle="Admin portal page"
                endpoint="/runs/parser"
            />
        </AdminLayout>
    );
}

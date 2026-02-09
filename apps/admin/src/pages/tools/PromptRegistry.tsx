import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function PromptRegistry() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Prompt Registry"
                subtitle="Admin portal page"
                endpoint="/prompts/registry"
            />
        </AdminLayout>
    );
}

import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function PhraseManager() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Phrase Manager"
                subtitle="Admin portal page"
                endpoint="/ontology/phrases"
            />
        </AdminLayout>
    );
}

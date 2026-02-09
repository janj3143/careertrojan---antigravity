import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function KeywordOntology() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Keyword Ontology"
                subtitle="Admin portal page"
                endpoint="/ontology/keywords"
            />
        </AdminLayout>
    );
}

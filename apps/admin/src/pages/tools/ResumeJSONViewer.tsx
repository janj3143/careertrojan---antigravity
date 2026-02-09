import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function ResumeJSONViewer() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="Resume JSON Viewer"
                subtitle="Admin portal page"
                endpoint="/admin/resume-viewer"
            />
        </AdminLayout>
    );
}

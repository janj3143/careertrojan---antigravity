import React from "react";
import GlossaryCollocations from "../components/GlossaryCollocations";

export default function GlossaryInsights() {
    return (
        <div className="min-h-screen bg-gray-50 px-6 py-8">
            <div className="mx-auto max-w-6xl">
                <div className="mb-6">
                    <h1 className="text-2xl font-bold text-gray-900">Glossary Insights</h1>
                    <p className="text-sm text-gray-600">
                        Collocation-aware glossary to surface multi-word concepts and hidden patterns.
                    </p>
                </div>
                <GlossaryCollocations />
            </div>
        </div>
    );
}

import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { FileText, Upload, Download, CheckCircle, XCircle } from 'lucide-react';

interface ParseResult {
    file_name: string;
    status: 'success' | 'failed';
    records_extracted: number;
    errors?: string[];
}

export default function DataParser() {
    const [file, setFile] = useState<File | null>(null);
    const [parsing, setParsing] = useState(false);
    const [results, setResults] = useState<ParseResult[]>([]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const uploadedFile = e.target.files?.[0];
        if (!uploadedFile) return;

        setFile(uploadedFile);
        setParsing(true);

        const formData = new FormData();
        formData.append('file', uploadedFile);

        try {
            const response = await fetch('/api/admin/v1/parsing/parse', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                setResults([result, ...results]);
            }
        } catch (err) {
            console.error('Error parsing file:', err);
        } finally {
            setParsing(false);
            setFile(null);
        }
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">📄 Data Parser</h1>
                    <p className="text-slate-400">Parse and import data files</p>
                </div>

                {/* Upload Section */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg p-8">
                    <div className="text-center">
                        <Upload size={48} className="mx-auto mb-4 text-slate-600" />
                        <h2 className="text-xl font-bold text-white mb-2">Upload Data File</h2>
                        <p className="text-slate-400 mb-6">Supported formats: CSV, JSON, Excel</p>

                        <label className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg cursor-pointer transition">
                            <FileText size={18} />
                            {parsing ? 'Parsing...' : 'Select File'}
                            <input
                                type="file"
                                onChange={handleFileUpload}
                                accept=".csv,.json,.xlsx,.xls"
                                className="hidden"
                                disabled={parsing}
                            />
                        </label>

                        {file && (
                            <div className="mt-4 text-sm text-slate-400">
                                Selected: {file.name}
                            </div>
                        )}
                    </div>
                </div>

                {/* Results */}
                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <h2 className="text-xl font-bold text-white mb-4">Parse Results</h2>
                    <div className="space-y-3">
                        {results.length === 0 ? (
                            <div className="text-center py-8 text-slate-400">
                                No files parsed yet
                            </div>
                        ) : (
                            results.map((result, idx) => (
                                <div key={idx} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-start gap-3">
                                            {result.status === 'success' ? (
                                                <CheckCircle className="text-green-400 mt-1" size={20} />
                                            ) : (
                                                <XCircle className="text-red-400 mt-1" size={20} />
                                            )}
                                            <div>
                                                <div className="font-semibold text-white">{result.file_name}</div>
                                                <div className="text-sm text-slate-400">
                                                    {result.records_extracted} records extracted
                                                </div>
                                                {result.errors && result.errors.length > 0 && (
                                                    <div className="mt-2 text-xs text-red-400">
                                                        {result.errors.join(', ')}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <button className="p-2 hover:bg-slate-700 rounded transition">
                                            <Download size={16} className="text-slate-400" />
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
}

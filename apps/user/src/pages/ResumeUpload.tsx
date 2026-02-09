import React, { useState } from 'react';

const API_CONFIG = {
    baseUrl: "http://localhost:8500", // Update port if needed
};

export default function ResumeUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<any | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
            setError(null);
            setResult(null);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setUploading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("file", file);

            const token = localStorage.getItem("token");
            if (!token) throw new Error("Not logged in");

            const res = await fetch(`${API_CONFIG.baseUrl}/api/resume/v1/upload`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`
                },
                body: formData
            });

            if (!res.ok) {
                const txt = await res.text();
                throw new Error(txt || "Upload failed");
            }

            const data = await res.json();
            setResult(data.data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold mb-6 text-gray-800">📄 Resume Upload & Analysis</h1>

            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold mb-2">Upload your CV</h2>
                    <p className="text-gray-600 text-sm mb-4">
                        Supported formats: PDF, DOCX, TXT. We analyze your resume to provide instant feedback.
                    </p>

                    <form onSubmit={handleUpload} className="space-y-4">
                        <div className="flex items-center justify-center w-full">
                            <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <svg className="w-8 h-8 mb-4 text-gray-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                                        <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2" />
                                    </svg>
                                    <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                                    <p className="text-xs text-gray-500">PDF, DOCX, TXT (MAX. 5MB)</p>
                                </div>
                                <input id="dropzone-file" type="file" className="hidden" onChange={handleFileChange} accept=".pdf,.docx,.txt" />
                            </label>
                        </div>

                        {file && (
                            <div className="text-sm text-green-600 font-medium">
                                Selected: {file.name}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={!file || uploading}
                            className={`w-full text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 focus:outline-none ${(!file || uploading) ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {uploading ? 'Analyzing...' : 'Upload & Analyze'}
                        </button>
                    </form>

                    {error && (
                        <div className="mt-4 p-4 text-sm text-red-800 bg-red-50 rounded-lg" role="alert">
                            <span className="font-medium">Error:</span> {error}
                        </div>
                    )}
                </div>
            </div>

            {result && result.parsed_result && (
                <div className="mt-8 bg-white p-6 rounded-lg shadow-md border border-gray-200">
                    <h2 className="text-2xl font-bold mb-4 text-gray-800">Analysis Results</h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div className="p-4 bg-blue-50 rounded-lg">
                            <h3 className="font-semibold text-blue-700">Word Count</h3>
                            <p className="text-2xl font-bold text-gray-800">{result.parsed_result.word_count}</p>
                        </div>
                        <div className="p-4 bg-green-50 rounded-lg">
                            <h3 className="font-semibold text-green-700">Detected Type</h3>
                            <p className="text-2xl font-bold text-gray-800">{result.parsed_result.detected_type}</p>
                        </div>
                    </div>

                    <div className="mb-6">
                        <h3 className="font-semibold text-gray-700 mb-2">Extracted Text Snippet</h3>
                        <div className="p-4 bg-gray-50 rounded border border-gray-200 text-sm font-mono text-gray-600 whitespace-pre-wrap h-40 overflow-y-auto">
                            {result.parsed_result.raw_text}
                        </div>
                    </div>

                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <h3 className="font-semibold text-yellow-800 mb-2">🔒 Premium Analysis</h3>
                        <p className="text-sm text-yellow-700">
                            Detailed ATS scoring, keyword optimization, and competitive analysis are available in the <strong>Pro Plan</strong>.
                            <a href="/payment" className="underline ml-1">Upgrade now</a>.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

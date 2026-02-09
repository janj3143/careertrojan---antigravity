import React, { useState, useRef } from 'react';
import { Camera, Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

const API_BASE = '/api';

/**
 * MobileCVUpload — Phase 3 mobile-optimised CV upload.
 * Supports camera capture + file picker + drag.
 * Designed for 375px+ screens.
 */
export default function MobileCVUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const cameraInputRef = useRef<HTMLInputElement>(null);

    const handleFile = (f: File) => {
        setFile(f);
        setError(null);
        setResult(null);

        // Preview for images (camera capture)
        if (f.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => setPreview(e.target?.result as string);
            reader.readAsDataURL(f);
        } else {
            setPreview(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const token = localStorage.getItem('token');
            if (!token) throw new Error('Please sign in first');

            const res = await fetch(`${API_BASE}/resume/v1/upload`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });

            if (!res.ok) {
                const txt = await res.text();
                throw new Error(txt || `Upload failed (${res.status})`);
            }

            const data = await res.json();
            setResult(data.data || data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    const reset = () => {
        setFile(null);
        setPreview(null);
        setResult(null);
        setError(null);
    };

    // ── Success state ─────────────────────────────────────
    if (result) {
        return (
            <div className="px-4 py-6 max-w-lg mx-auto">
                <div className="text-center mb-6">
                    <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-3" />
                    <h2 className="text-xl font-bold text-gray-900">CV Uploaded!</h2>
                    <p className="text-sm text-gray-500 mt-1">Your CV is being analysed by our AI.</p>
                </div>

                {result.score && (
                    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-600">ATS Score</span>
                            <span className="text-2xl font-bold text-indigo-600">{result.score}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                                className="bg-indigo-600 h-2 rounded-full transition-all duration-1000"
                                style={{ width: `${result.score}%` }}
                            />
                        </div>
                    </div>
                )}

                {result.suggestions && result.suggestions.length > 0 && (
                    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-4">
                        <h3 className="text-sm font-semibold text-gray-800 mb-3">AI Suggestions</h3>
                        <ul className="space-y-2">
                            {result.suggestions.map((s: string, i: number) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                                    <span className="text-indigo-500 mt-0.5">•</span>
                                    <span>{s}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <button
                    onClick={reset}
                    className="w-full py-3 bg-gray-100 text-gray-700 rounded-xl text-sm font-semibold hover:bg-gray-200 transition-colors touch-target"
                >
                    Upload Another
                </button>
            </div>
        );
    }

    // ── Upload state ──────────────────────────────────────
    return (
        <div className="px-4 py-6 max-w-lg mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Upload CV</h1>
            <p className="text-sm text-gray-500 mb-6">PDF, DOCX, TXT, or take a photo</p>

            {/* File selected preview */}
            {file ? (
                <div className="mb-6">
                    {preview ? (
                        <div className="relative rounded-xl overflow-hidden border border-gray-200 mb-3">
                            <img src={preview} alt="CV preview" className="w-full max-h-60 object-contain bg-gray-50" />
                        </div>
                    ) : (
                        <div className="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200 rounded-xl mb-3">
                            <FileText className="w-8 h-8 text-indigo-500" />
                            <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                                <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(0)} KB</p>
                            </div>
                        </div>
                    )}

                    <div className="flex gap-3">
                        <button
                            onClick={handleUpload}
                            disabled={uploading}
                            className="flex-1 py-3 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50 touch-target flex items-center justify-center gap-2"
                        >
                            {uploading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Analysing...
                                </>
                            ) : (
                                'Upload & Analyse'
                            )}
                        </button>
                        <button
                            onClick={reset}
                            disabled={uploading}
                            className="px-4 py-3 border border-gray-300 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50 touch-target"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            ) : (
                /* File selection buttons */
                <div className="space-y-3 mb-6">
                    {/* Camera capture */}
                    <button
                        onClick={() => cameraInputRef.current?.click()}
                        className="w-full flex items-center gap-4 p-4 bg-white border-2 border-dashed border-gray-300 rounded-xl hover:border-indigo-400 hover:bg-indigo-50/50 transition-colors touch-target"
                    >
                        <div className="p-3 bg-indigo-100 rounded-lg">
                            <Camera className="w-6 h-6 text-indigo-600" />
                        </div>
                        <div className="text-left">
                            <p className="text-sm font-semibold text-gray-900">Take a Photo</p>
                            <p className="text-xs text-gray-500">Photograph your printed CV</p>
                        </div>
                    </button>
                    <input
                        ref={cameraInputRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        className="hidden"
                        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                    />

                    {/* File picker */}
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full flex items-center gap-4 p-4 bg-white border-2 border-dashed border-gray-300 rounded-xl hover:border-indigo-400 hover:bg-indigo-50/50 transition-colors touch-target"
                    >
                        <div className="p-3 bg-emerald-100 rounded-lg">
                            <Upload className="w-6 h-6 text-emerald-600" />
                        </div>
                        <div className="text-left">
                            <p className="text-sm font-semibold text-gray-900">Choose File</p>
                            <p className="text-xs text-gray-500">PDF, DOCX, or TXT (max 5 MB)</p>
                        </div>
                    </button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.docx,.doc,.txt"
                        className="hidden"
                        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                    />
                </div>
            )}

            {/* Error */}
            {error && (
                <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 animate-fade-in">
                    <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{error}</span>
                </div>
            )}
        </div>
    );
}

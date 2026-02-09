import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Sparkles, Copy, RefreshCw } from 'lucide-react';

export default function AIContentGenerator() {
    const [prompt, setPrompt] = useState('');
    const [generating, setGenerating] = useState(false);
    const [generatedContent, setGeneratedContent] = useState('');

    const handleGenerate = async () => {
        setGenerating(true);
        // Simulate AI generation
        setTimeout(() => {
            setGeneratedContent(`Generated content based on: "${prompt}"\n\nThis is AI-generated placeholder content that would be created by the actual AI model.`);
            setGenerating(false);
        }, 2000);
    };

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">✨ AI Content Generator</h1>
                    <p className="text-slate-400">Generate content using AI</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Content Prompt
                    </label>
                    <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder="Enter your prompt here..."
                        rows={4}
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-500 mb-4"
                    />
                    <button
                        onClick={handleGenerate}
                        disabled={generating || !prompt}
                        className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 rounded-lg transition"
                    >
                        {generating ? (
                            <>
                                <RefreshCw size={18} className="animate-spin" />
                                Generating...
                            </>
                        ) : (
                            <>
                                <Sparkles size={18} />
                                Generate Content
                            </>
                        )}
                    </button>
                </div>

                {generatedContent && (
                    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-white">Generated Content</h3>
                            <button className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded transition">
                                <Copy size={16} />
                                Copy
                            </button>
                        </div>
                        <div className="bg-slate-800 rounded-lg p-4 text-slate-300 whitespace-pre-wrap">
                            {generatedContent}
                        </div>
                    </div>
                )}
            </div>
        </AdminLayout>
    );
}

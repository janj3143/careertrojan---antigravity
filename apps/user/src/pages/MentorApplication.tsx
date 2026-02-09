import React, { useState } from 'react';
import { User, Mail, Linkedin, Briefcase, FileText, Send, CheckCircle } from 'lucide-react';

const API_CONFIG = { baseUrl: "http://localhost:8500" };

export default function MentorApplication() {
    const [formData, setFormData] = useState({
        full_name: "",
        email: "",
        linkedin_url: "",
        expertise: "",
        bio: "",
        experience_years: ""
    });
    const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
    const [errorMsg, setErrorMsg] = useState("");

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setStatus("submitting");

        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`${API_CONFIG.baseUrl}/mentorship/applications`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    applicant_user_id: "current_user", // Backend handles this via token mostly, but endpoint asks for it. We'll use a placeholder or handle in backend if optimized.
                    email: formData.email,
                    full_name: formData.full_name,
                    application_data: {
                        linkedin: formData.linkedin_url,
                        expertise: formData.expertise.split(",").map(s => s.trim()),
                        bio: formData.bio,
                        experience: formData.experience_years
                    }
                })
            });

            if (res.ok) {
                setStatus("success");
            } else {
                const data = await res.json();
                setStatus("error");
                setErrorMsg(data.detail || "Failed to submit application");
            }
        } catch (err) {
            setStatus("error");
            setErrorMsg("Network error occurred.");
        }
    };

    if (status === "success") {
        return (
            <div className="p-8 max-w-2xl mx-auto text-center">
                <div className="bg-green-50 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="w-10 h-10 text-green-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Application Submitted!</h2>
                <p className="text-gray-600 mb-8">
                    Thank you for applying to be a mentor. Our team of Guardians will review your profile
                    and get back to you within 48 hours.
                </p>
                <button
                    onClick={() => window.location.href = '/dashboard'}
                    className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700"
                >
                    Return to Dashboard
                </button>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">🎓 Become A Mentor</h1>
                <p className="text-gray-600 mt-2">Share your expertise, guide the next generation, and earn rewards.</p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border p-8">
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                            <div className="relative">
                                <User className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    name="full_name"
                                    required
                                    className="pl-10 w-full border rounded-lg py-2 px-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    value={formData.full_name}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
                                <input
                                    type="email"
                                    name="email"
                                    required
                                    className="pl-10 w-full border rounded-lg py-2 px-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    value={formData.email}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">LinkedIn Profile URL</label>
                        <div className="relative">
                            <Linkedin className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
                            <input
                                type="url"
                                name="linkedin_url"
                                required
                                placeholder="https://linkedin.com/in/..."
                                className="pl-10 w-full border rounded-lg py-2 px-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                                value={formData.linkedin_url}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Areas of Expertise</label>
                            <div className="relative">
                                <Briefcase className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    name="expertise"
                                    required
                                    placeholder="e.g. Sales, Python, Marketing (comma separated)"
                                    className="pl-10 w-full border rounded-lg py-2 px-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    value={formData.expertise}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Years of Experience</label>
                            <input
                                type="number"
                                name="experience_years"
                                required
                                min="1"
                                className="w-full border rounded-lg py-2 px-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                                value={formData.experience_years}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Why do you want to mentor?</label>
                        <div className="relative">
                            <FileText className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                            <textarea
                                name="bio"
                                required
                                rows={4}
                                className="pl-10 w-full border rounded-lg py-2 px-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="Tell us about your motivation..."
                                value={formData.bio}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    {status === "error" && (
                        <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
                            {errorMsg}
                        </div>
                    )}

                    <div className="flex justify-end">
                        <button
                            type="submit"
                            disabled={status === "submitting"}
                            className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 flex items-center gap-2"
                        >
                            {status === "submitting" ? "Submitting..." : (
                                <>Submit Application <Send className="w-4 h-4" /></>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

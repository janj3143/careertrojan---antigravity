
import React, { useState, useEffect } from 'react';
import { User, Mail, Briefcase, MapPin, Linkedin, Github, Save, CheckCircle } from 'lucide-react';
import { API } from '../lib/apiConfig';

// Helper to interact with the profile endpoint
async function userProfile(method: "GET" | "PUT", body?: any) {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No token found");

    const headers: any = {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };

    const res = await fetch(`${API.user}/profile`, {
        method, headers, body: body ? JSON.stringify(body) : undefined
    });

    if (!res.ok) {
        if (res.status === 401) {
            // Handle token expiry
            window.location.href = "/login";
            throw new Error("Session expired");
        }
        throw new Error("Profile API failed");
    }
    return res.json();
}

export default function ProfilePage() {
    const [profile, setProfile] = useState<any>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [msg, setMsg] = useState("");

    // Load Profile
    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        try {
            const data = await userProfile("GET");
            setProfile(data || {});
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setMsg("");
        try {
            const updated = await userProfile("PUT", profile);
            setProfile(updated);
            setMsg("Profile saved successfully!");
            setTimeout(() => setMsg(""), 3000);
        } catch (e) {
            setMsg("Error saving profile.");
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setProfile({ ...profile, [e.target.name]: e.target.value });
    };

    if (loading) return <div className="p-10 text-center">Loading profile...</div>;

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Your Profile</h1>
                <p className="text-gray-600 mt-2">Manage your professional identity and preferences.</p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                {/* Header Banner */}
                <div className="h-32 bg-gradient-to-r from-indigo-600 to-purple-600"></div>

                <div className="px-8 pb-8">
                    {/* Avatar / Initials */}
                    <div className="relative -mt-12 mb-6">
                        <div className="w-24 h-24 rounded-full bg-white p-1 shadow-md inline-block">
                            <div className="w-full h-full rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-2xl font-bold">
                                {profile.full_name ? profile.full_name.charAt(0) : "U"}
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSave} className="space-y-6">
                        {/* Section: Basic Info */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                    <input
                                        type="text"
                                        className="pl-10 w-full rounded-md border-gray-300 shadow-sm border p-2 bg-gray-50 text-gray-500"
                                        value={profile.full_name || ""}
                                        disabled // Name is often managed by Auth/Account, simple profile endpoint might not update it
                                    />
                                </div>
                                <p className="text-xs text-gray-400 mt-1">Managed in Account Settings</p>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                    <input
                                        type="email"
                                        className="pl-10 w-full rounded-md border-gray-300 shadow-sm border p-2 bg-gray-50 text-gray-500"
                                        value={profile.email || ""}
                                        disabled
                                    />
                                </div>
                            </div>

                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Professional Bio</label>
                                <textarea
                                    name="bio"
                                    rows={3}
                                    className="w-full rounded-md border-gray-300 shadow-sm border p-2"
                                    placeholder="Tell us about your professional background..."
                                    value={profile.bio || ""}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        <hr className="border-gray-100" />

                        {/* Section: Professional Links */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                                <div className="relative">
                                    <MapPin className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                    <input
                                        name="location"
                                        type="text"
                                        className="pl-10 w-full rounded-md border-gray-300 shadow-sm border p-2"
                                        placeholder="e.g. London, UK"
                                        value={profile.location || ""}
                                        onChange={handleChange}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">LinkedIn URL</label>
                                <div className="relative">
                                    <Linkedin className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                    <input
                                        name="linkedin"
                                        type="url"
                                        className="pl-10 w-full rounded-md border-gray-300 shadow-sm border p-2"
                                        placeholder="https://linkedin.com/in/..."
                                        value={profile.linkedin_url || ""}
                                        onChange={handleChange}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">GitHub URL</label>
                                <div className="relative">
                                    <Github className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                    <input
                                        name="github"
                                        type="url"
                                        className="pl-10 w-full rounded-md border-gray-300 shadow-sm border p-2"
                                        placeholder="https://github.com/..."
                                        value={profile.github_url || ""}
                                        onChange={handleChange}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="pt-4 flex items-center gap-4">
                            <button
                                type="submit"
                                disabled={saving}
                                className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 font-medium flex items-center gap-2 disabled:opacity-50"
                            >
                                {saving ? 'Saving...' : <><Save className="w-4 h-4" /> Save Changes</>}
                            </button>

                            {msg && (
                                <span className={`text-sm ${msg.includes('Error') ? 'text-red-600' : 'text-green-600'} flex items-center gap-1`}>
                                    {msg.includes('Error') ? null : <CheckCircle className="w-4 h-4" />}
                                    {msg}
                                </span>
                            )}
                        </div>

                    </form>
                </div>
            </div>
        </div>
    );
}

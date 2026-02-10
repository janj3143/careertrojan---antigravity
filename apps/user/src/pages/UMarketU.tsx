import React, { useEffect, useState } from 'react';
import { Briefcase, MapPin, DollarSign, Search, TrendingUp, Clock, ArrowRight } from 'lucide-react';
import { API } from '../lib/apiConfig';

export default function UMarketU() {
    const [jobs, setJobs] = useState<any[]>([]);
    const [industries, setIndustries] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const token = localStorage.getItem("token");
            const headers: any = {};
            if (token) headers["Authorization"] = `Bearer ${token}`;

            // Parallel fetch
            const [jobsRes, indRes] = await Promise.all([
                fetch(`${API.jobs}/index`, { headers }),
                fetch(`${API.taxonomy}/industries`, { headers })
            ]);

            if (jobsRes.ok) {
                const data = await jobsRes.json();
                setJobs(data.jobs || []);
            }
            if (indRes.ok) {
                const data = await indRes.json();
                setIndustries(data.data || []);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">🎯 MarketU Suite</h1>
                <p className="text-gray-600 mt-2">Real-time job market insights and opportunities.</p>
            </div>

            {/* Market Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
                    <div className="flex items-center gap-3 mb-2">
                        <TrendingUp className="w-6 h-6" />
                        <h3 className="font-bold">Top Industry</h3>
                    </div>
                    <p className="text-2xl font-bold">Technology</p>
                    <p className="text-white/80 text-sm">+12% growth this month</p>
                </div>
                <div className="bg-white border rounded-xl p-6">
                    <h3 className="text-gray-500 text-sm font-medium mb-1">Active Job Listings</h3>
                    <p className="text-3xl font-bold text-gray-900">{jobs.length}</p>
                </div>
                <div className="bg-white border rounded-xl p-6">
                    <h3 className="text-gray-500 text-sm font-medium mb-1">Tracked Industries</h3>
                    <p className="text-3xl font-bold text-gray-900">{industries.length}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Job Listings */}
                <div className="lg:col-span-2">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-gray-900">Featured Opportunities</h2>
                        <div className="relative">
                            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search jobs..."
                                className="pl-9 pr-4 py-2 border rounded-lg text-sm w-64 focus:ring-2 focus:ring-indigo-500 outline-none"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-4">
                        {jobs.map((job) => (
                            <div key={job.id} className="bg-white p-4 rounded-xl border hover:border-indigo-300 transition-colors cursor-pointer group">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="font-bold text-gray-900 group-hover:text-indigo-600">{job.title}</h3>
                                        <p className="text-gray-600 text-sm">{job.company}</p>
                                    </div>
                                    <span className="bg-green-50 text-green-700 px-2 py-1 rounded text-xs font-medium">New</span>
                                </div>
                                <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                                    <span className="flex items-center gap-1"><MapPin className="w-4 h-4" /> {job.location}</span>
                                    <span className="flex items-center gap-1"><DollarSign className="w-4 h-4" /> {job.salary_range}</span>
                                    <span className="flex items-center gap-1"><Clock className="w-4 h-4" /> {job.posted_at}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Industry Taxonomy Sidebar */}
                <div>
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Industries</h2>
                    <div className="bg-white rounded-xl border p-4">
                        <div className="space-y-2">
                            {industries.length > 0 ? industries.slice(0, 10).map((ind: string, idx: number) => (
                                <div key={idx} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer group">
                                    <span className="text-sm text-gray-700 group-hover:text-indigo-600">{ind}</span>
                                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-indigo-600" />
                                </div>
                            )) : (
                                <p className="text-sm text-gray-500 p-2">No industries loaded.</p>
                            )}
                        </div>
                        <button className="w-full mt-4 text-center text-indigo-600 text-sm font-medium hover:underline">
                            View All Industries
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

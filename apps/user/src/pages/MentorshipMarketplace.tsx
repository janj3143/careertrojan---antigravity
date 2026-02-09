import React, { useEffect, useState } from 'react';
import { User, Star, Clock, DollarSign, ArrowRight } from 'lucide-react';

const API_CONFIG = { baseUrl: "http://localhost:8500" };

export default function MentorshipMarketplace() {
    const [mentors, setMentors] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchMentors();
    }, []);

    const fetchMentors = async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`${API_CONFIG.baseUrl}/mentor/list`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setMentors(data);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="flex justify-between items-end mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">🤝 Mentorship Marketplace</h1>
                    <p className="text-gray-600 mt-2">Connect with industry experts to accelerate your career.</p>
                </div>
                <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
                    Become a Mentor
                </button>
            </div>

            {loading ? (
                <div className="text-center p-10">Loading mentors...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {mentors.map((mentor) => (
                        <div key={mentor.mentor_profile_id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-xl">
                                        {mentor.display_name.charAt(0)}
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-gray-900">{mentor.display_name}</h3>
                                        <p className="text-sm text-gray-500">{mentor.expertise_areas?.[0] || "Career Mentor"}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1 text-yellow-500 text-sm font-medium">
                                    <Star className="w-4 h-4 fill-current" />
                                    {mentor.rating}
                                </div>
                            </div>

                            <p className="text-gray-600 text-sm line-clamp-2 mb-4 h-10">
                                {mentor.bio || "Experienced mentor ready to help you achieve your career goals."}
                            </p>

                            <div className="flex flex-wrap gap-2 mb-4">
                                {mentor.expertise_areas?.slice(0, 3).map((area: string) => (
                                    <span key={area} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                                        {area}
                                    </span>
                                ))}
                            </div>

                            <div className="flex items-center justify-between pt-4 border-t border-gray-50">
                                <div className="text-sm text-gray-500 flex items-center gap-1">
                                    <DollarSign className="w-4 h-4" />
                                    {mentor.hourly_rate ? `$${mentor.hourly_rate}/hr` : "Free / Pro Bono"}
                                </div>
                                <button className="text-indigo-600 font-medium text-sm flex items-center gap-1 hover:text-indigo-800">
                                    View Profile <ArrowRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}

                    {mentors.length === 0 && (
                        <div className="col-span-full text-center p-10 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                            <p className="text-gray-500">No mentors found. Be the first to join!</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

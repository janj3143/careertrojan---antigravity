import React, { useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { Building2, Search, ExternalLink } from 'lucide-react';

interface Company {
    name: string;
    industry: string;
    size: string;
    website: string;
    hiring_status: 'active' | 'limited' | 'frozen';
}

export default function WebCompanyIntel() {
    const [searchTerm, setSearchTerm] = useState('');
    const [companies] = useState<Company[]>([
        {
            name: 'Google',
            industry: 'Technology',
            size: '100,000+',
            website: 'google.com',
            hiring_status: 'active'
        }
    ]);

    return (
        <AdminLayout>
            <div className="max-w-7xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🏢 Web Company Intel</h1>
                    <p className="text-slate-400">Company intelligence and hiring data</p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" size={18} />
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Search companies..."
                            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {companies.map((company, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                            <div className="flex items-start justify-between">
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-1">{company.name}</h3>
                                    <div className="text-sm text-slate-400">{company.industry} • {company.size} employees</div>
                                </div>
                                <a href={`https://${company.website}`} target="_blank" rel="noopener noreferrer" className="p-2 hover:bg-slate-800 rounded transition">
                                    <ExternalLink size={16} className="text-blue-400" />
                                </a>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AdminLayout>
    );
}

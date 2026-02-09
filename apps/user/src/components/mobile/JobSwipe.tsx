import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    MapPin, Briefcase, DollarSign, Building2, Clock,
    Heart, X, ChevronDown, ExternalLink
} from 'lucide-react';

const API_BASE = '/api';

interface Job {
    id: string;
    title: string;
    company: string;
    location: string;
    salary_range?: string;
    type?: string;
    posted?: string;
    description?: string;
    match_score?: number;
}

/**
 * JobSwipe — Phase 3 Tinder-style job browser.
 * Swipe right = save, swipe left = skip, tap = expand details.
 * Route: /jobs/swipe
 */
export default function JobSwipe() {
    const navigate = useNavigate();
    const [jobs, setJobs] = useState<Job[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [expanded, setExpanded] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saved, setSaved] = useState<Set<string>>(new Set());
    const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null);

    // Touch tracking
    const touchStartX = useRef(0);
    const touchDeltaX = useRef(0);
    const cardRef = useRef<HTMLDivElement>(null);

    useEffect(() => { loadJobs(); }, []);

    const loadJobs = async () => {
        try {
            const token = localStorage.getItem('token');
            const headers: any = token ? { Authorization: `Bearer ${token}` } : {};
            const res = await fetch(`${API_BASE}/jobs/v1/index`, { headers });
            if (res.ok) {
                const data = await res.json();
                setJobs(data.jobs || []);
            }
        } catch (e) {
            console.error('Failed to load jobs', e);
        } finally {
            setLoading(false);
        }
    };

    const currentJob = jobs[currentIndex];
    const remaining = jobs.length - currentIndex;

    const handleSwipe = (direction: 'left' | 'right') => {
        if (!currentJob) return;

        setSwipeDirection(direction);

        if (direction === 'right') {
            setSaved(prev => new Set(prev).add(currentJob.id));
        }

        // Animate out, then advance
        setTimeout(() => {
            setSwipeDirection(null);
            setExpanded(false);
            setCurrentIndex(prev => prev + 1);
        }, 300);
    };

    // Touch handlers
    const onTouchStart = (e: React.TouchEvent) => {
        touchStartX.current = e.touches[0].clientX;
        touchDeltaX.current = 0;
    };

    const onTouchMove = (e: React.TouchEvent) => {
        touchDeltaX.current = e.touches[0].clientX - touchStartX.current;
        if (cardRef.current) {
            const rotation = touchDeltaX.current * 0.05;
            cardRef.current.style.transform = `translateX(${touchDeltaX.current}px) rotate(${rotation}deg)`;
            cardRef.current.style.transition = 'none';
        }
    };

    const onTouchEnd = () => {
        const threshold = 100;
        if (cardRef.current) {
            cardRef.current.style.transition = 'transform 0.3s ease';
            cardRef.current.style.transform = '';
        }

        if (touchDeltaX.current > threshold) {
            handleSwipe('right');
        } else if (touchDeltaX.current < -threshold) {
            handleSwipe('left');
        }
        touchDeltaX.current = 0;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center">
                    <div className="skeleton w-64 h-80 rounded-2xl mx-auto mb-4" />
                    <p className="text-sm text-gray-500">Loading jobs...</p>
                </div>
            </div>
        );
    }

    if (!currentJob) {
        return (
            <div className="flex items-center justify-center min-h-[60vh] px-4">
                <div className="text-center max-w-xs">
                    <div className="text-5xl mb-4">🎉</div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">All caught up!</h2>
                    <p className="text-sm text-gray-500 mb-6">
                        You've seen all {jobs.length} jobs. {saved.size} saved.
                    </p>
                    <button
                        onClick={() => { setCurrentIndex(0); setSaved(new Set()); }}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-colors touch-target"
                    >
                        Start Over
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="px-4 py-4 max-w-lg mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h1 className="text-lg font-bold text-gray-900">Job Browser</h1>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span>{remaining} remaining</span>
                    <span className="text-indigo-600 font-semibold">{saved.size} saved</span>
                </div>
            </div>

            {/* Card Stack */}
            <div className="relative" style={{ minHeight: '420px' }}>
                {/* Next card peek */}
                {jobs[currentIndex + 1] && (
                    <div className="absolute inset-x-2 top-2 bg-gray-100 rounded-2xl h-[400px] opacity-60" />
                )}

                {/* Current card */}
                <div
                    ref={cardRef}
                    className={`relative bg-white border-2 border-gray-100 rounded-2xl shadow-lg overflow-hidden transition-transform duration-300 ${
                        swipeDirection === 'right' ? 'translate-x-[120%] rotate-12' :
                        swipeDirection === 'left' ? '-translate-x-[120%] -rotate-12' : ''
                    }`}
                    onTouchStart={onTouchStart}
                    onTouchMove={onTouchMove}
                    onTouchEnd={onTouchEnd}
                >
                    {/* Match score */}
                    {currentJob.match_score && (
                        <div className="absolute top-4 right-4 bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold">
                            {currentJob.match_score}% match
                        </div>
                    )}

                    <div className="p-5">
                        {/* Company */}
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center">
                                <Building2 className="w-6 h-6 text-indigo-600" />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">{currentJob.company}</p>
                                <h2 className="text-lg font-bold text-gray-900">{currentJob.title}</h2>
                            </div>
                        </div>

                        {/* Meta */}
                        <div className="space-y-2 mb-4">
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <MapPin className="w-4 h-4 text-gray-400" />
                                <span>{currentJob.location || 'Remote'}</span>
                            </div>
                            {currentJob.salary_range && (
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <DollarSign className="w-4 h-4 text-gray-400" />
                                    <span>{currentJob.salary_range}</span>
                                </div>
                            )}
                            {currentJob.type && (
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <Briefcase className="w-4 h-4 text-gray-400" />
                                    <span>{currentJob.type}</span>
                                </div>
                            )}
                            {currentJob.posted && (
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <Clock className="w-4 h-4 text-gray-400" />
                                    <span>{currentJob.posted}</span>
                                </div>
                            )}
                        </div>

                        {/* Expandable description */}
                        <button
                            onClick={() => setExpanded(!expanded)}
                            className="flex items-center gap-1 text-sm text-indigo-600 font-medium mb-3 touch-target"
                        >
                            <span>{expanded ? 'Less' : 'More details'}</span>
                            <ChevronDown className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
                        </button>

                        {expanded && currentJob.description && (
                            <div className="text-sm text-gray-600 leading-relaxed mb-4 max-h-40 overflow-y-auto animate-fade-in">
                                {currentJob.description}
                            </div>
                        )}
                    </div>

                    {/* Swipe indicators */}
                    <div className="flex items-center justify-center gap-8 pb-6">
                        <button
                            onClick={() => handleSwipe('left')}
                            className="w-14 h-14 rounded-full border-2 border-red-200 flex items-center justify-center text-red-400 hover:bg-red-50 transition-colors touch-target active:scale-90"
                            aria-label="Skip job"
                        >
                            <X className="w-6 h-6" />
                        </button>
                        <button
                            onClick={() => handleSwipe('right')}
                            className="w-14 h-14 rounded-full border-2 border-green-200 flex items-center justify-center text-green-500 hover:bg-green-50 transition-colors touch-target active:scale-90"
                            aria-label="Save job"
                        >
                            <Heart className="w-6 h-6" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Hint text */}
            <p className="text-center text-xs text-gray-400 mt-4">
                Swipe right to save · Swipe left to skip
            </p>
        </div>
    );
}

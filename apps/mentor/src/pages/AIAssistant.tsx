import React, { useState } from 'react';
import MentorLayout from '../components/MentorLayout';
import { Bot, Send, Sparkles, FileText, Users, TrendingUp } from 'lucide-react';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export default function AIAssistant() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: 'Hello! I\'m your AI Mentorship Assistant. I can help you with mentee progress analysis, session planning, and personalized coaching strategies. How can I assist you today?',
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    const quickActions = [
        { icon: <Users size={20} />, label: 'Analyze Mentee Progress', prompt: 'Analyze my current mentees\' progress and suggest focus areas' },
        { icon: <FileText size={20} />, label: 'Session Plan', prompt: 'Help me create a session plan for career transition coaching' },
        { icon: <TrendingUp size={20} />, label: 'Improvement Tips', prompt: 'What can I do to improve my mentorship effectiveness?' },
        { icon: <Sparkles size={20} />, label: 'Best Practices', prompt: 'Share best practices for remote mentorship sessions' }
    ];

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = {
            role: 'user',
            content: input,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        // Simulate AI response
        setTimeout(() => {
            const aiResponse: Message = {
                role: 'assistant',
                content: `I understand you're asking about: "${input}". Based on your mentorship history and best practices, here are some insights:\n\n1. **Focus on Active Listening**: Ensure you're fully present during sessions\n2. **Set Clear Goals**: Work with your mentee to establish SMART objectives\n3. **Track Progress**: Use our progress tracking tools to monitor development\n4. **Provide Actionable Feedback**: Be specific and constructive\n\nWould you like me to elaborate on any of these points?`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, aiResponse]);
            setLoading(false);
        }, 1500);
    };

    const handleQuickAction = (prompt: string) => {
        setInput(prompt);
    };

    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto h-[calc(100vh-200px)] flex flex-col">
                {/* Header */}
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                        <Bot className="text-purple-400" size={32} />
                        Mentorship AI Assistant
                    </h1>
                    <p className="text-slate-400">
                        AI-powered insights and recommendations for effective mentorship
                    </p>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
                    {quickActions.map((action, idx) => (
                        <button
                            key={idx}
                            onClick={() => handleQuickAction(action.prompt)}
                            className="bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg p-4 text-left transition flex items-start gap-3"
                        >
                            <div className="text-purple-400 mt-1">{action.icon}</div>
                            <div>
                                <div className="text-sm font-semibold text-white mb-1">{action.label}</div>
                                <div className="text-xs text-slate-400 line-clamp-2">{action.prompt}</div>
                            </div>
                        </button>
                    ))}
                </div>

                {/* Chat Messages */}
                <div className="flex-1 bg-slate-900 border border-slate-700 rounded-lg overflow-hidden flex flex-col">
                    <div className="flex-1 overflow-y-auto p-6 space-y-4">
                        {messages.map((message, idx) => (
                            <div
                                key={idx}
                                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-[80%] rounded-lg p-4 ${message.role === 'user'
                                            ? 'bg-green-600 text-white'
                                            : 'bg-slate-800 text-slate-200 border border-slate-700'
                                        }`}
                                >
                                    {message.role === 'assistant' && (
                                        <div className="flex items-center gap-2 mb-2 text-purple-400">
                                            <Bot size={16} />
                                            <span className="text-xs font-semibold">AI Assistant</span>
                                        </div>
                                    )}
                                    <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                                    <div className="text-xs opacity-60 mt-2">
                                        {message.timestamp.toLocaleTimeString()}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex justify-start">
                                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                                    <div className="flex items-center gap-2 text-purple-400">
                                        <Bot size={16} className="animate-pulse" />
                                        <span className="text-sm">AI is thinking...</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Input Area */}
                    <div className="border-t border-slate-700 p-4 bg-slate-800">
                        <div className="flex gap-3">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                                placeholder="Ask me anything about mentorship..."
                                className="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || loading}
                                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg transition flex items-center gap-2 text-white font-semibold"
                            >
                                <Send size={18} />
                                Send
                            </button>
                        </div>
                        <div className="text-xs text-slate-500 mt-2">
                            💡 Tip: Ask about mentee progress, session planning, or best practices
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="text-center text-sm text-slate-500 mt-4">
                    🤖 AI-Powered Mentorship Assistant | CareerTrojan Mentor Portal
                </div>
            </div>
        </MentorLayout>
    );
}

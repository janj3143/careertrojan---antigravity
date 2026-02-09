import React, { useState } from 'react';
import MentorLayout from '../components/MentorLayout';
import { MessageSquare, Send, Inbox, Archive, Search } from 'lucide-react';

interface Message {
    id: string;
    from: string;
    subject: string;
    preview: string;
    timestamp: string;
    unread: boolean;
}

export default function CommunicationCenter() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            from: 'Mentee #12345',
            subject: 'Question about next session',
            preview: 'Hi, I wanted to ask about the topics we\'ll cover in our next session...',
            timestamp: '2 hours ago',
            unread: true
        }
    ]);
    const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
    const [replyText, setReplyText] = useState('');

    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto">
                <h1 className="text-3xl font-bold text-white mb-6">💬 Communication Center</h1>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Message List */}
                    <div className="lg:col-span-1 bg-slate-900 border border-slate-700 rounded-lg">
                        <div className="p-4 border-b border-slate-700">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" size={18} />
                                <input
                                    type="text"
                                    placeholder="Search messages..."
                                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500"
                                />
                            </div>
                        </div>
                        <div className="divide-y divide-slate-700 max-h-[600px] overflow-y-auto">
                            {messages.map(msg => (
                                <div
                                    key={msg.id}
                                    onClick={() => setSelectedMessage(msg)}
                                    className={`p-4 cursor-pointer transition ${msg.unread ? 'bg-blue-900/20' : 'hover:bg-slate-800'
                                        } ${selectedMessage?.id === msg.id ? 'bg-slate-800' : ''}`}
                                >
                                    <div className="flex items-start justify-between mb-1">
                                        <div className="font-semibold text-white">{msg.from}</div>
                                        {msg.unread && <div className="w-2 h-2 bg-blue-500 rounded-full" />}
                                    </div>
                                    <div className="text-sm text-slate-300 font-medium mb-1">{msg.subject}</div>
                                    <div className="text-xs text-slate-400 truncate">{msg.preview}</div>
                                    <div className="text-xs text-slate-500 mt-1">{msg.timestamp}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Message Detail */}
                    <div className="lg:col-span-2 bg-slate-900 border border-slate-700 rounded-lg">
                        {selectedMessage ? (
                            <div className="flex flex-col h-[600px]">
                                <div className="p-6 border-b border-slate-700">
                                    <h2 className="text-xl font-bold text-white mb-2">{selectedMessage.subject}</h2>
                                    <div className="flex items-center gap-4 text-sm text-slate-400">
                                        <span>From: {selectedMessage.from}</span>
                                        <span>{selectedMessage.timestamp}</span>
                                    </div>
                                </div>
                                <div className="flex-1 p-6 overflow-y-auto">
                                    <p className="text-slate-300">{selectedMessage.preview}</p>
                                </div>
                                <div className="p-6 border-t border-slate-700">
                                    <textarea
                                        value={replyText}
                                        onChange={(e) => setReplyText(e.target.value)}
                                        placeholder="Type your reply..."
                                        rows={4}
                                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-500 mb-3"
                                    />
                                    <button className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 rounded transition">
                                        <Send size={18} />
                                        Send Reply
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-[600px] text-slate-400">
                                <div className="text-center">
                                    <MessageSquare size={64} className="mx-auto mb-4 text-slate-600" />
                                    <p>Select a message to view</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </MentorLayout>
    );
}

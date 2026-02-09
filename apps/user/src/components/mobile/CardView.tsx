import React from 'react';

interface CardField {
    label: string;
    value: React.ReactNode;
}

interface CardViewProps {
    items: Array<{
        id: string | number;
        title: string;
        subtitle?: string;
        fields?: CardField[];
        badge?: { text: string; color?: string };
        actions?: React.ReactNode;
        onClick?: () => void;
    }>;
    className?: string;
}

/**
 * CardView — Replaces wide data tables on mobile.
 * 
 * Desktop: consumers use <table> as normal.
 * Mobile (≤1024px): pass data here for stacked card layout.
 * 
 * Usage:
 *   <div className="hidden lg:block"><YourTable /></div>
 *   <div className="lg:hidden"><CardView items={...} /></div>
 */
export default function CardView({ items, className = '' }: CardViewProps) {
    if (!items.length) {
        return (
            <div className="text-center py-12 text-gray-500">
                <p className="text-sm">No items to display</p>
            </div>
        );
    }

    return (
        <div className={`space-y-3 ${className}`}>
            {items.map((item) => (
                <div
                    key={item.id}
                    className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${
                        item.onClick ? 'cursor-pointer active:bg-gray-50 transition-colors' : ''
                    }`}
                    onClick={item.onClick}
                    role={item.onClick ? 'button' : undefined}
                    tabIndex={item.onClick ? 0 : undefined}
                >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-2">
                        <div className="min-w-0 flex-1">
                            <h3 className="text-base font-semibold text-gray-900 truncate">
                                {item.title}
                            </h3>
                            {item.subtitle && (
                                <p className="text-sm text-gray-500 mt-0.5 truncate">{item.subtitle}</p>
                            )}
                        </div>
                        {item.badge && (
                            <span className={`ml-2 flex-shrink-0 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                item.badge.color || 'bg-gray-100 text-gray-800'
                            }`}>
                                {item.badge.text}
                            </span>
                        )}
                    </div>

                    {/* Fields */}
                    {item.fields && item.fields.length > 0 && (
                        <div className="space-y-1.5 mt-3">
                            {item.fields.map((field, i) => (
                                <div key={i} className="flex justify-between items-center text-sm">
                                    <span className="text-gray-500">{field.label}</span>
                                    <span className="text-gray-900 font-medium text-right">{field.value}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Actions */}
                    {item.actions && (
                        <div className="mt-3 pt-3 border-t border-gray-100 flex gap-2">
                            {item.actions}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}

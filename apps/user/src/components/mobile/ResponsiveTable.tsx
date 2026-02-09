import React from 'react';
import CardView from './CardView';

interface Column {
    key: string;
    header: string;
    render?: (value: any, row: any) => React.ReactNode;
}

interface ResponsiveTableProps {
    columns: Column[];
    data: any[];
    idKey?: string;
    titleKey?: string;
    subtitleKey?: string;
    badgeKey?: string;
    badgeColorFn?: (value: any) => string;
    onRowClick?: (row: any) => void;
    actions?: (row: any) => React.ReactNode;
    className?: string;
}

/**
 * ResponsiveTable — Automatically switches between table (desktop) and cards (mobile).
 * 
 * On lg+ screens: renders a proper <table>.
 * On smaller screens: renders stacked CardView cards.
 */
export default function ResponsiveTable({
    columns, data, idKey = 'id', titleKey, subtitleKey, badgeKey,
    badgeColorFn, onRowClick, actions, className = ''
}: ResponsiveTableProps) {
    // Determine title column
    const titleCol = titleKey || columns[0]?.key || 'id';
    const subtitleCol = subtitleKey || (columns.length > 1 ? columns[1].key : undefined);

    // Card items for mobile
    const cardItems = data.map((row) => ({
        id: row[idKey] ?? Math.random(),
        title: String(row[titleCol] ?? ''),
        subtitle: subtitleCol ? String(row[subtitleCol] ?? '') : undefined,
        badge: badgeKey && row[badgeKey] ? {
            text: String(row[badgeKey]),
            color: badgeColorFn ? badgeColorFn(row[badgeKey]) : undefined,
        } : undefined,
        fields: columns
            .filter(col => col.key !== titleCol && col.key !== subtitleCol && col.key !== badgeKey)
            .map(col => ({
                label: col.header,
                value: col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '—'),
            })),
        actions: actions ? actions(row) : undefined,
        onClick: onRowClick ? () => onRowClick(row) : undefined,
    }));

    return (
        <div className={className}>
            {/* Desktop: Table */}
            <div className="hidden lg:block overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                        <tr>
                            {columns.map(col => (
                                <th key={col.key} className="px-4 py-3 font-medium">{col.header}</th>
                            ))}
                            {actions && <th className="px-4 py-3 font-medium">Actions</th>}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {data.map((row, i) => (
                            <tr
                                key={row[idKey] ?? i}
                                className={`${onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''}`}
                                onClick={onRowClick ? () => onRowClick(row) : undefined}
                            >
                                {columns.map(col => (
                                    <td key={col.key} className="px-4 py-3 text-gray-900">
                                        {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '')}
                                    </td>
                                ))}
                                {actions && <td className="px-4 py-3">{actions(row)}</td>}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Mobile: Cards */}
            <div className="lg:hidden">
                <CardView items={cardItems} />
            </div>
        </div>
    );
}

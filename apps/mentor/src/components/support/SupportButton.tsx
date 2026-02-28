/**
 * SupportButton — Floating Help Button
 * 
 * Fixed-position button in the bottom-right corner that opens the support modal.
 * Appears on all pages for easy access.
 */

import React, { useState } from 'react';
import SupportModal from './SupportModal';

interface SupportButtonProps {
  requestId?: string;  // Pass from page context if relevant
  resumeVersionId?: number;  // Pass from resume pages
}

export function SupportButton({ requestId, resumeVersionId }: SupportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setIsOpen(true)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className="group flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-3 rounded-full shadow-lg hover:shadow-xl transition-all duration-200"
          aria-label="Get Support"
        >
          {/* Help Icon */}
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          
          {/* Text - slides in on hover */}
          <span
            className={`overflow-hidden transition-all duration-200 ${
              isHovered ? 'max-w-[100px] opacity-100' : 'max-w-0 opacity-0'
            }`}
          >
            Help
          </span>
        </button>
      </div>

      {/* Support Modal */}
      <SupportModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        requestId={requestId}
        resumeVersionId={resumeVersionId}
      />
    </>
  );
}

export default SupportButton;

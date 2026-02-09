import React from 'react';
import { PackageCard } from './PackageCard';
import { ServicePackage } from '../App';
import { Package as PackageIcon } from 'lucide-react';

interface PackageListProps {
  packages: ServicePackage[];
  onToggleActive: (id: string) => void;
  onDelete: (id: string) => void;
}

export function PackageList({ packages, onToggleActive, onDelete }: PackageListProps) {
  if (packages.length === 0) {
    return (
      <div className="bg-gray-900/60 backdrop-blur-md border border-cyan-500/20 rounded-lg p-8 text-center">
        <PackageIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h3 className="text-gray-300 mb-2">No packages yet</h3>
        <p className="text-gray-500 text-sm">Create your first offering above to get started.</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-white mb-6 flex items-center gap-2">
        <PackageIcon className="w-6 h-6 text-cyan-400" />
        Existing Packages
      </h2>
      <div className="space-y-4">
        {packages.map((pkg) => (
          <PackageCard
            key={pkg.id}
            package={pkg}
            onToggleActive={onToggleActive}
            onDelete={onDelete}
          />
        ))}
      </div>
    </div>
  );
}

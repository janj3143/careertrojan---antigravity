import React, { useState } from 'react';
import { PackageForm } from './components/PackageForm';
import { PackageList } from './components/PackageList';
import { Package as PackageIcon } from 'lucide-react';
import { Toaster } from './components/ui/sonner';
import backgroundImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';

export interface ServicePackage {
  id: string;
  package_name: string;
  description: string;
  session_count: number;
  session_duration: number;
  price_per_session: number;
  total_package_price: number;
  deliverables: string[];
  expected_outcomes: string;
  is_active: boolean;
  guardian_assessed: boolean;
}

function App() {
  const [packages, setPackages] = useState<ServicePackage[]>([]);

  const handleAddPackage = (newPackage: Omit<ServicePackage, 'id' | 'total_package_price' | 'guardian_assessed'>) => {
    const packageWithId: ServicePackage = {
      ...newPackage,
      id: Date.now().toString(),
      total_package_price: newPackage.price_per_session * newPackage.session_count,
      guardian_assessed: false,
    };
    setPackages([...packages, packageWithId]);
  };

  const handleToggleActive = (id: string) => {
    setPackages(packages.map(pkg =>
      pkg.id === id ? { ...pkg, is_active: !pkg.is_active } : pkg
    ));
  };

  const handleDelete = (id: string) => {
    setPackages(packages.filter(pkg => pkg.id !== id));
  };

  return (
    <div className="min-h-screen relative">
      {/* Background Image */}
      <div 
        className="fixed inset-0 z-0"
        style={{
          backgroundImage: `url(${backgroundImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
      ></div>

      {/* Content */}
      <div className="relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <PackageIcon className="w-10 h-10 text-cyan-400" />
              <h1 className="text-white">Service Packages Manager</h1>
            </div>
            <p className="text-gray-300">IntelliCV AI Platform</p>
            <p className="text-sm text-gray-400 mt-2">
              Mentors define, edit and manage monetized session offerings.
            </p>
          </div>

          {/* Package Form */}
          <div className="mb-8">
            <PackageForm onAddPackage={handleAddPackage} />
          </div>

          {/* Package List */}
          <div>
            <PackageList 
              packages={packages}
              onToggleActive={handleToggleActive}
              onDelete={handleDelete}
            />
          </div>

          {/* Footer */}
          <div className="mt-12 text-center">
            <p className="text-sm text-gray-400">Mentor Portal • Package Manager</p>
          </div>
        </div>
      </div>
      
      {/* Toaster for notifications */}
      <Toaster position="top-center" richColors />
    </div>
  );
}

export default App;
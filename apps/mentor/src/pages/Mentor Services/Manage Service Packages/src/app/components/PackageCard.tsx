import React, { useState } from 'react';
import { ServicePackage } from '../App';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { 
  Edit, 
  Power, 
  Trash2, 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  DollarSign, 
  CheckCircle,
  XCircle 
} from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';

interface PackageCardProps {
  package: ServicePackage;
  onToggleActive: (id: string) => void;
  onDelete: (id: string) => void;
}

export function PackageCard({ package: pkg, onToggleActive, onDelete }: PackageCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleEdit = () => {
    toast.info('Edit functionality will be implemented in a future update');
  };

  const handleToggle = () => {
    onToggleActive(pkg.id);
    toast.success(pkg.is_active ? 'Package deactivated' : 'Package activated');
  };

  const handleDeleteConfirm = () => {
    onDelete(pkg.id);
    toast.success('Package deleted successfully');
    setShowDeleteDialog(false);
  };

  return (
    <>
      <div className="bg-gray-900/80 backdrop-blur-md border border-cyan-500/20 rounded-lg overflow-hidden hover:border-cyan-500/40 transition-all">
        {/* Header - Always Visible */}
        <div 
          className="p-4 cursor-pointer flex items-center justify-between"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-white">{pkg.package_name}</h3>
              {!pkg.is_active && (
                <Badge variant="secondary" className="bg-red-500/20 text-red-300 border-red-500/30">
                  Inactive
                </Badge>
              )}
              {pkg.guardian_assessed && (
                <Badge variant="secondary" className="bg-green-500/20 text-green-300 border-green-500/30">
                  Guardian Assessed
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span className="flex items-center gap-1">
                <DollarSign className="w-4 h-4" />
                £{pkg.price_per_session}/session
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {pkg.session_count} sessions
              </span>
            </div>
          </div>
          <div>
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-cyan-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-cyan-400" />
            )}
          </div>
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-700/50">
            <div className="pt-4 space-y-4">
              {/* Description */}
              <div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {pkg.description}
                </p>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                  <div className="text-xs text-gray-400 mb-1">Total Price</div>
                  <div className="text-xl text-white">£{pkg.total_package_price}</div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                  <div className="text-xs text-gray-400 mb-1">Duration / Session</div>
                  <div className="text-xl text-white">{pkg.session_duration} min</div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                  <div className="text-xs text-gray-400 mb-1">Guardian Assessed</div>
                  <div className="text-xl text-white flex items-center gap-1">
                    {pkg.guardian_assessed ? (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <span className="text-base">Yes</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-gray-500" />
                        <span className="text-base">No</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Deliverables */}
              <div>
                <h4 className="text-sm text-gray-300 mb-2">Deliverables:</h4>
                {pkg.deliverables.length === 0 ? (
                  <p className="text-sm text-gray-500">None specified</p>
                ) : (
                  <ul className="space-y-1">
                    {pkg.deliverables.map((deliverable, index) => (
                      <li key={index} className="text-sm text-gray-400 flex items-start gap-2">
                        <span className="text-cyan-400 mt-1">•</span>
                        <span>{deliverable}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Expected Outcomes */}
              <div>
                <h4 className="text-sm text-gray-300 mb-2">Expected Outcomes:</h4>
                {pkg.expected_outcomes ? (
                  <p className="text-sm text-gray-400">{pkg.expected_outcomes}</p>
                ) : (
                  <p className="text-sm text-gray-500">Not specified</p>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleEdit}
                  className="flex-1 bg-gray-800/50 border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleToggle}
                  className={`flex-1 border-gray-600 ${
                    pkg.is_active 
                      ? 'bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20' 
                      : 'bg-green-500/10 text-green-400 hover:bg-green-500/20'
                  }`}
                >
                  <Power className="w-4 h-4 mr-2" />
                  {pkg.is_active ? 'Deactivate' : 'Activate'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDeleteDialog(true)}
                  className="flex-1 bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20 hover:text-red-300"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="bg-gray-900 border-gray-700">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">Delete Package</AlertDialogTitle>
            <AlertDialogDescription className="text-gray-400">
              Are you sure you want to delete "{pkg.package_name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-gray-800 text-gray-300 border-gray-700 hover:bg-gray-700">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-red-500 hover:bg-red-600 text-white"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AdminAuthProvider, useAdminAuth } from './context/AdminAuthContext';
import AdminLogin from './pages/AdminLogin';

// Main Pages
import AdminHome from './pages/AdminHome';
import ServiceStatus from './pages/ServiceStatus';
import Analytics from './pages/Analytics';
import UserManagement from './pages/UserManagement';
import ComplianceAudit from './pages/ComplianceAudit';
import EmailIntegration from './pages/EmailIntegration';
import DataParser from './pages/DataParser';
import BatchProcessing from './pages/BatchProcessing';
import AIEnrichment from './pages/AIEnrichment';
import AIContentGenerator from './pages/AIContentGenerator';
import MarketIntelligence from './pages/MarketIntelligence';
import TokenManagement from './pages/TokenManagement';
import CompetitiveIntel from './pages/CompetitiveIntel';
import WebCompanyIntel from './pages/WebCompanyIntel';
import APIIntegration from './pages/APIIntegration';
import ContactComm from './pages/ContactComm';
import AdvancedSettings from './pages/AdvancedSettings';
import LoggingErrors from './pages/LoggingErrors';
import JobTitleAI from './pages/JobTitleAI';
import JobTitleCloud from './pages/JobTitleCloud';
import MentorManagement from './pages/MentorManagement';
import ModelTraining from './pages/ModelTraining';
import RequirementsMgmt from './pages/RequirementsMgmt';
import TokenManagementAlt from './pages/TokenManagementAlt';
import IntelligenceHub from './pages/IntelligenceHub';
import CareerPatterns from './pages/CareerPatterns';
import ExaWebIntel from './pages/ExaWebIntel';
import UnifiedAnalytics from './pages/UnifiedAnalytics';
import MentorAppReview from './pages/MentorAppReview';
import ConnectivityAudit from './pages/ConnectivityAudit';
import BlockerDetectionTest from './pages/BlockerDetectionTest';
import AdminPortalEntry from './pages/AdminPortalEntry';

// Tools Pages
import DataRootsHealth from './pages/tools/DataRootsHealth';
import DatasetsBrowser from './pages/tools/DatasetsBrowser';
import ResumeJSONViewer from './pages/tools/ResumeJSONViewer';
import ParserRuns from './pages/tools/ParserRuns';
import EnrichmentRuns from './pages/tools/EnrichmentRuns';
import KeywordOntology from './pages/tools/KeywordOntology';
import PhraseManager from './pages/tools/PhraseManager';
import EmailCapture from './pages/tools/EmailCapture';
import EmailAnalytics from './pages/tools/EmailAnalytics';
import JobIndex from './pages/tools/JobIndex';
import RoleTaxonomy from './pages/tools/RoleTaxonomy';
import ScoringAnalytics from './pages/tools/ScoringAnalytics';
import BiasAndFairness from './pages/tools/BiasAndFairness';
import ModelRegistry from './pages/tools/ModelRegistry';
import PromptRegistry from './pages/tools/PromptRegistry';
import EvaluationHarness from './pages/tools/EvaluationHarness';
import QueueMonitor from './pages/tools/QueueMonitor';
import BlobStorage from './pages/tools/BlobStorage';
import UserAudit from './pages/tools/UserAudit';
import AdminAudit from './pages/tools/AdminAudit';
import Notifications from './pages/tools/Notifications';
import SystemConfig from './pages/tools/SystemConfig';
import LogsViewer from './pages/tools/LogsViewer';
import Diagnostics from './pages/tools/Diagnostics';
import Exports from './pages/tools/Exports';
import BackupRestore from './pages/tools/BackupRestore';
import RouteMap from './pages/tools/RouteMap';
import APIExplorer from './pages/tools/APIExplorer';
import About from './pages/tools/About';

// Operations Pages
import OpsAdminAudit from './pages/ops/OpsAdminAudit';
import OpsNotifications from './pages/ops/OpsNotifications';
import OpsSystemConfig from './pages/ops/OpsSystemConfig';
import OpsLogsViewer from './pages/ops/OpsLogsViewer';
import OpsDiagnostics from './pages/ops/OpsDiagnostics';
import OpsExports from './pages/ops/OpsExports';
import OpsBackupRestore from './pages/ops/OpsBackupRestore';
import OpsRouteMap from './pages/ops/OpsRouteMap';
import OpsAPIExplorer from './pages/ops/OpsAPIExplorer';
import OpsAbout from './pages/ops/OpsAbout';

function PrivateRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, loading } = useAdminAuth();

    if (loading) return <div className="p-10 text-center text-white">Loading...</div>;

    return isAuthenticated ? <>{children}</> : <Navigate to="/admin/login" />;
}

export default function App() {
    return (
        <AdminAuthProvider>
            <BrowserRouter>
                <Routes>
                    {/* Public Route */}
                    <Route path="/admin/login" element={<AdminLogin />} />

                    {/* Main Admin Pages (00-30) */}
                    <Route path="/admin" element={<PrivateRoute><AdminHome /></PrivateRoute>} />
                    <Route path="/admin/status" element={<PrivateRoute><ServiceStatus /></PrivateRoute>} />
                    <Route path="/admin/analytics" element={<PrivateRoute><Analytics /></PrivateRoute>} />
                    <Route path="/admin/users" element={<PrivateRoute><UserManagement /></PrivateRoute>} />
                    <Route path="/admin/compliance" element={<PrivateRoute><ComplianceAudit /></PrivateRoute>} />
                    <Route path="/admin/email" element={<PrivateRoute><EmailIntegration /></PrivateRoute>} />
                    <Route path="/admin/parser" element={<PrivateRoute><DataParser /></PrivateRoute>} />
                    <Route path="/admin/batch" element={<PrivateRoute><BatchProcessing /></PrivateRoute>} />
                    <Route path="/admin/ai-enrich" element={<PrivateRoute><AIEnrichment /></PrivateRoute>} />
                    <Route path="/admin/ai-content" element={<PrivateRoute><AIContentGenerator /></PrivateRoute>} />
                    <Route path="/admin/market-intel" element={<PrivateRoute><MarketIntelligence /></PrivateRoute>} />
                    <Route path="/admin/tokens" element={<PrivateRoute><TokenManagement /></PrivateRoute>} />
                    <Route path="/admin/competitive" element={<PrivateRoute><CompetitiveIntel /></PrivateRoute>} />
                    <Route path="/admin/web-intel" element={<PrivateRoute><WebCompanyIntel /></PrivateRoute>} />
                    <Route path="/admin/api-integration" element={<PrivateRoute><APIIntegration /></PrivateRoute>} />
                    <Route path="/admin/contact" element={<PrivateRoute><ContactComm /></PrivateRoute>} />
                    <Route path="/admin/settings" element={<PrivateRoute><AdvancedSettings /></PrivateRoute>} />
                    <Route path="/admin/logs" element={<PrivateRoute><LoggingErrors /></PrivateRoute>} />
                    <Route path="/admin/job-title-ai" element={<PrivateRoute><JobTitleAI /></PrivateRoute>} />
                    <Route path="/admin/job-cloud" element={<PrivateRoute><JobTitleCloud /></PrivateRoute>} />
                    <Route path="/admin/mentors" element={<PrivateRoute><MentorManagement /></PrivateRoute>} />
                    <Route path="/admin/model-training" element={<PrivateRoute><ModelTraining /></PrivateRoute>} />
                    <Route path="/admin/requirements" element={<PrivateRoute><RequirementsMgmt /></PrivateRoute>} />
                    <Route path="/admin/tokens-alt" element={<PrivateRoute><TokenManagementAlt /></PrivateRoute>} />
                    <Route path="/admin/intel-hub" element={<PrivateRoute><IntelligenceHub /></PrivateRoute>} />
                    <Route path="/admin/career-patterns" element={<PrivateRoute><CareerPatterns /></PrivateRoute>} />
                    <Route path="/admin/exa-web" element={<PrivateRoute><ExaWebIntel /></PrivateRoute>} />
                    <Route path="/admin/unified-analytics" element={<PrivateRoute><UnifiedAnalytics /></PrivateRoute>} />
                    <Route path="/admin/mentor-review" element={<PrivateRoute><MentorAppReview /></PrivateRoute>} />
                    <Route path="/admin/connectivity" element={<PrivateRoute><ConnectivityAudit /></PrivateRoute>} />
                    <Route path="/admin/blocker-test" element={<PrivateRoute><BlockerDetectionTest /></PrivateRoute>} />
                    <Route path="/admin/portal-entry" element={<PrivateRoute><AdminPortalEntry /></PrivateRoute>} />

                    {/* Tools Pages (99_tools - 29 pages) */}
                    <Route path="/admin/tools/data-health" element={<PrivateRoute><DataRootsHealth /></PrivateRoute>} />
                    <Route path="/admin/tools/datasets" element={<PrivateRoute><DatasetsBrowser /></PrivateRoute>} />
                    <Route path="/admin/tools/resume-viewer" element={<PrivateRoute><ResumeJSONViewer /></PrivateRoute>} />
                    <Route path="/admin/tools/parser-runs" element={<PrivateRoute><ParserRuns /></PrivateRoute>} />
                    <Route path="/admin/tools/enrichment" element={<PrivateRoute><EnrichmentRuns /></PrivateRoute>} />
                    <Route path="/admin/tools/keywords" element={<PrivateRoute><KeywordOntology /></PrivateRoute>} />
                    <Route path="/admin/tools/phrases" element={<PrivateRoute><PhraseManager /></PrivateRoute>} />
                    <Route path="/admin/tools/email-capture" element={<PrivateRoute><EmailCapture /></PrivateRoute>} />
                    <Route path="/admin/tools/email-analytics" element={<PrivateRoute><EmailAnalytics /></PrivateRoute>} />
                    <Route path="/admin/tools/job-index" element={<PrivateRoute><JobIndex /></PrivateRoute>} />
                    <Route path="/admin/tools/taxonomy" element={<PrivateRoute><RoleTaxonomy /></PrivateRoute>} />
                    <Route path="/admin/tools/scoring" element={<PrivateRoute><ScoringAnalytics /></PrivateRoute>} />
                    <Route path="/admin/tools/fairness" element={<PrivateRoute><BiasAndFairness /></PrivateRoute>} />
                    <Route path="/admin/tools/models" element={<PrivateRoute><ModelRegistry /></PrivateRoute>} />
                    <Route path="/admin/tools/prompts" element={<PrivateRoute><PromptRegistry /></PrivateRoute>} />
                    <Route path="/admin/tools/evaluation" element={<PrivateRoute><EvaluationHarness /></PrivateRoute>} />
                    <Route path="/admin/tools/queue" element={<PrivateRoute><QueueMonitor /></PrivateRoute>} />
                    <Route path="/admin/tools/blob" element={<PrivateRoute><BlobStorage /></PrivateRoute>} />
                    <Route path="/admin/tools/user-audit" element={<PrivateRoute><UserAudit /></PrivateRoute>} />
                    <Route path="/admin/tools/admin-audit" element={<PrivateRoute><AdminAudit /></PrivateRoute>} />
                    <Route path="/admin/tools/notifications" element={<PrivateRoute><Notifications /></PrivateRoute>} />
                    <Route path="/admin/tools/config" element={<PrivateRoute><SystemConfig /></PrivateRoute>} />
                    <Route path="/admin/tools/logs-viewer" element={<PrivateRoute><LogsViewer /></PrivateRoute>} />
                    <Route path="/admin/tools/diagnostics" element={<PrivateRoute><Diagnostics /></PrivateRoute>} />
                    <Route path="/admin/tools/exports" element={<PrivateRoute><Exports /></PrivateRoute>} />
                    <Route path="/admin/tools/backup" element={<PrivateRoute><BackupRestore /></PrivateRoute>} />
                    <Route path="/admin/tools/route-map" element={<PrivateRoute><RouteMap /></PrivateRoute>} />
                    <Route path="/admin/tools/api-explorer" element={<PrivateRoute><APIExplorer /></PrivateRoute>} />
                    <Route path="/admin/tools/about" element={<PrivateRoute><About /></PrivateRoute>} />

                    {/* Operations Pages (10 pages) */}
                    <Route path="/admin/ops/admin-audit" element={<PrivateRoute><OpsAdminAudit /></PrivateRoute>} />
                    <Route path="/admin/ops/notifications" element={<PrivateRoute><OpsNotifications /></PrivateRoute>} />
                    <Route path="/admin/ops/config" element={<PrivateRoute><OpsSystemConfig /></PrivateRoute>} />
                    <Route path="/admin/ops/logs" element={<PrivateRoute><OpsLogsViewer /></PrivateRoute>} />
                    <Route path="/admin/ops/diagnostics" element={<PrivateRoute><OpsDiagnostics /></PrivateRoute>} />
                    <Route path="/admin/ops/exports" element={<PrivateRoute><OpsExports /></PrivateRoute>} />
                    <Route path="/admin/ops/backup" element={<PrivateRoute><OpsBackupRestore /></PrivateRoute>} />
                    <Route path="/admin/ops/route-map" element={<PrivateRoute><OpsRouteMap /></PrivateRoute>} />
                    <Route path="/admin/ops/api-explorer" element={<PrivateRoute><OpsAPIExplorer /></PrivateRoute>} />
                    <Route path="/admin/ops/about" element={<PrivateRoute><OpsAbout /></PrivateRoute>} />

                    {/* Fallback */}
                    <Route path="*" element={<Navigate to="/admin" />} />
                </Routes>
            </BrowserRouter>
        </AdminAuthProvider>
    );
}

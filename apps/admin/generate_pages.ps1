# Generate all Admin Portal pages
$basePath = "C:\careertrojan\apps\admin\src\pages"

# Main pages (00-30)
$mainPages = @(
    @{Name = "AdminHome"; Title = "Admin Home"; Endpoint = "/admin/health" },
    @{Name = "ServiceStatus"; Title = "Service Status Monitor"; Endpoint = "/admin/status" },
    @{Name = "Analytics"; Title = "Analytics Dashboard"; Endpoint = "/analytics/summary" },
    @{Name = "UserManagement"; Title = "User Management"; Endpoint = "/admin/users" },
    @{Name = "ComplianceAudit"; Title = "Compliance Audit"; Endpoint = "/admin/compliance" },
    @{Name = "EmailIntegration"; Title = "Email Integration"; Endpoint = "/email/analytics" },
    @{Name = "DataParser"; Title = "Complete Data Parser"; Endpoint = "/admin/parser" },
    @{Name = "BatchProcessing"; Title = "Batch Processing"; Endpoint = "/admin/batch" },
    @{Name = "AIEnrichment"; Title = "AI Enrichment"; Endpoint = "/admin/ai-enrich" },
    @{Name = "AIContentGenerator"; Title = "AI Content Generator"; Endpoint = "/admin/ai-content" },
    @{Name = "MarketIntelligence"; Title = "Market Intelligence Center"; Endpoint = "/admin/market-intel" },
    @{Name = "TokenManagement"; Title = "Token Management"; Endpoint = "/admin/tokens" },
    @{Name = "CompetitiveIntel"; Title = "Competitive Intelligence"; Endpoint = "/admin/competitive" },
    @{Name = "WebCompanyIntel"; Title = "Web Company Intelligence"; Endpoint = "/admin/web-intel" },
    @{Name = "APIIntegration"; Title = "API Integration"; Endpoint = "/admin/api-integration" },
    @{Name = "ContactComm"; Title = "Contact Communication"; Endpoint = "/admin/contact" },
    @{Name = "AdvancedSettings"; Title = "Advanced Settings"; Endpoint = "/admin/settings" },
    @{Name = "LoggingErrors"; Title = "Logging & Error Snapshot"; Endpoint = "/admin/logs" },
    @{Name = "JobTitleAI"; Title = "Job Title AI Integration"; Endpoint = "/admin/job-title-ai" },
    @{Name = "JobTitleCloud"; Title = "Job Title Overlap Cloud"; Endpoint = "/admin/job-cloud" },
    @{Name = "MentorManagement"; Title = "Mentor Management"; Endpoint = "/admin/mentors" },
    @{Name = "ModelTraining"; Title = "AI Model Training Review"; Endpoint = "/models/registry" },
    @{Name = "RequirementsMgmt"; Title = "Software Requirements Management"; Endpoint = "/admin/requirements" },
    @{Name = "TokenManagementAlt"; Title = "Token Management (Alt)"; Endpoint = "/admin/tokens-alt" },
    @{Name = "IntelligenceHub"; Title = "Intelligence Hub"; Endpoint = "/admin/intel-hub" },
    @{Name = "CareerPatterns"; Title = "Career Pattern Intelligence"; Endpoint = "/admin/career-patterns" },
    @{Name = "ExaWebIntel"; Title = "Exa Web Intelligence"; Endpoint = "/admin/exa-web" },
    @{Name = "UnifiedAnalytics"; Title = "Unified Analytics Dashboard"; Endpoint = "/analytics/unified" },
    @{Name = "MentorAppReview"; Title = "Mentor Application Review"; Endpoint = "/mentorship/applications" },
    @{Name = "ConnectivityAudit"; Title = "System Connectivity Audit"; Endpoint = "/admin/connectivity" },
    @{Name = "BlockerDetectionTest"; Title = "Blocker Detection Test"; Endpoint = "/admin/blocker-test" }
)

# Tools pages (01-29)
$toolsPages = @(
    @{Name = "DataRootsHealth"; Title = "Data Roots & Health"; Endpoint = "/admin/data-health" },
    @{Name = "DatasetsBrowser"; Title = "Datasets Browser"; Endpoint = "/fs/list" },
    @{Name = "ResumeJSONViewer"; Title = "Resume JSON Viewer"; Endpoint = "/admin/resume-viewer" },
    @{Name = "ParserRuns"; Title = "Parser Runs"; Endpoint = "/runs/parser" },
    @{Name = "EnrichmentRuns"; Title = "Enrichment Runs"; Endpoint = "/runs/enrichment" },
    @{Name = "KeywordOntology"; Title = "Keyword Ontology"; Endpoint = "/ontology/keywords" },
    @{Name = "PhraseManager"; Title = "Phrase Manager"; Endpoint = "/ontology/phrases" },
    @{Name = "EmailCapture"; Title = "Email Capture"; Endpoint = "/email/captured" },
    @{Name = "EmailAnalytics"; Title = "Email Analytics"; Endpoint = "/email/analytics" },
    @{Name = "JobIndex"; Title = "Job Index"; Endpoint = "/jobs/index" },
    @{Name = "RoleTaxonomy"; Title = "Role Taxonomy"; Endpoint = "/taxonomy/summary" },
    @{Name = "ScoringAnalytics"; Title = "Scoring Analytics"; Endpoint = "/analytics/scoring" },
    @{Name = "BiasAndFairness"; Title = "Bias and Fairness"; Endpoint = "/analytics/fairness" },
    @{Name = "ModelRegistry"; Title = "Model Registry"; Endpoint = "/models/registry" },
    @{Name = "PromptRegistry"; Title = "Prompt Registry"; Endpoint = "/prompts/registry" },
    @{Name = "EvaluationHarness"; Title = "Evaluation Harness"; Endpoint = "/eval/runs" },
    @{Name = "QueueMonitor"; Title = "Queue Monitor"; Endpoint = "/ops/queue" },
    @{Name = "BlobStorage"; Title = "Blob Storage"; Endpoint = "/ops/blob" },
    @{Name = "UserAudit"; Title = "User Audit"; Endpoint = "/audit/users" },
    @{Name = "AdminAudit"; Title = "Admin Audit"; Endpoint = "/audit/admin" },
    @{Name = "Notifications"; Title = "Notifications"; Endpoint = "/admin/notifications" },
    @{Name = "SystemConfig"; Title = "System Config"; Endpoint = "/admin/config" },
    @{Name = "LogsViewer"; Title = "Logs Viewer"; Endpoint = "/admin/logs-viewer" },
    @{Name = "Diagnostics"; Title = "Diagnostics"; Endpoint = "/admin/diagnostics" },
    @{Name = "Exports"; Title = "Exports"; Endpoint = "/admin/exports" },
    @{Name = "BackupRestore"; Title = "Backup & Restore"; Endpoint = "/admin/backup" },
    @{Name = "RouteMap"; Title = "Route Map"; Endpoint = "/admin/route-map" },
    @{Name = "APIExplorer"; Title = "API Explorer"; Endpoint = "/admin/api-explorer" },
    @{Name = "About"; Title = "About"; Endpoint = "/admin/about" }
)

# Operations pages (10 pages)
$opsPages = @(
    @{Name = "OpsAdminAudit"; Title = "Admin Audit (Ops)"; Endpoint = "/audit/admin" },
    @{Name = "OpsNotifications"; Title = "Notifications (Ops)"; Endpoint = "/ops/notifications" },
    @{Name = "OpsSystemConfig"; Title = "System Config (Ops)"; Endpoint = "/ops/config" },
    @{Name = "OpsLogsViewer"; Title = "Logs Viewer (Ops)"; Endpoint = "/ops/logs" },
    @{Name = "OpsDiagnostics"; Title = "Diagnostics (Ops)"; Endpoint = "/ops/diagnostics" },
    @{Name = "OpsExports"; Title = "Exports (Ops)"; Endpoint = "/ops/exports" },
    @{Name = "OpsBackupRestore"; Title = "Backup & Restore (Ops)"; Endpoint = "/ops/backup" },
    @{Name = "OpsRouteMap"; Title = "Route Map (Ops)"; Endpoint = "/ops/route-map" },
    @{Name = "OpsAPIExplorer"; Title = "API Explorer (Ops)"; Endpoint = "/ops/api-explorer" },
    @{Name = "OpsAbout"; Title = "About (Ops)"; Endpoint = "/ops/about" }
)

function Create-PageFile {
    param($Name, $Title, $Endpoint, $Path)
    
    $content = @"
import React from 'react';
import AdminLayout from '../components/AdminLayout';
import PageTemplate from '../components/PageTemplate';

export default function $Name() {
    return (
        <AdminLayout>
            <PageTemplate 
                title="$Title"
                subtitle="Admin portal page"
                endpoint="$Endpoint"
            />
        </AdminLayout>
    );
}
"@
    
    Set-Content -Path $Path -Value $content -Encoding UTF8
    Write-Host "Created: $Path"
}

# Create main pages
foreach ($page in $mainPages) {
    $path = Join-Path $basePath "$($page.Name).tsx"
    Create-PageFile -Name $page.Name -Title $page.Title -Endpoint $page.Endpoint -Path $path
}

# Create tools pages
$toolsPath = Join-Path $basePath "tools"
New-Item -ItemType Directory -Force -Path $toolsPath | Out-Null
foreach ($page in $toolsPages) {
    $path = Join-Path $toolsPath "$($page.Name).tsx"
    Create-PageFile -Name $page.Name -Title $page.Title -Endpoint $page.Endpoint -Path $path
}

# Create ops pages
$opsPath = Join-Path $basePath "ops"
New-Item -ItemType Directory -Force -Path $opsPath | Out-Null
foreach ($page in $opsPages) {
    $path = Join-Path $opsPath "$($page.Name).tsx"
    Create-PageFile -Name $page.Name -Title $page.Title -Endpoint $page.Endpoint -Path $path
}

Write-Host "`nGenerated all 69 Admin pages successfully!"

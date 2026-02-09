# Generate all Mentor Portal pages
$basePath = "C:\careertrojan\apps\mentor\src\pages"

$mentorPages = @(
    @{Name = "Dashboard"; Title = "Mentor Dashboard"; Endpoint = "/mentor/dashboard" },
    @{Name = "MentorDashboard"; Title = "Mentor Overview"; Endpoint = "/mentor/overview" },
    @{Name = "FinancialDashboard"; Title = "Financial Dashboard"; Endpoint = "/mentor/financials" },
    @{Name = "MenteeAgreements"; Title = "Mentee Agreements & Progress"; Endpoint = "/mentorship/agreements" },
    @{Name = "CommunicationCenter"; Title = "Communication Center"; Endpoint = "/mentor/messages" },
    @{Name = "GuardianFeedback"; Title = "Guardian Feedback"; Endpoint = "/mentor/guardian-feedback" },
    @{Name = "MenteeProgress"; Title = "Mentee Progress Tracking"; Endpoint = "/mentor/mentee-progress" },
    @{Name = "AIAssistant"; Title = "Mentorship AI Assistant"; Endpoint = "/mentor/ai-assistant" },
    @{Name = "MyAgreements"; Title = "My Mentorship Agreements"; Endpoint = "/mentor/my-agreements" },
    @{Name = "ServicePackages"; Title = "Service Packages"; Endpoint = "/mentor/packages" },
    @{Name = "ServicesAgreement"; Title = "Services Agreement"; Endpoint = "/mentor/services" },
    @{Name = "SessionsCalendar"; Title = "Sessions Calendar"; Endpoint = "/mentor/calendar" }
)

function Create-MentorPage {
    param($Name, $Title, $Endpoint, $Path)
    
    $content = @"
import React from 'react';
import MentorLayout from '../components/MentorLayout';

export default function $Name() {
    return (
        <MentorLayout>
            <div className="max-w-7xl mx-auto">
                <h1 className="text-3xl font-bold text-white mb-6">$Title</h1>
                <div className="bg-slate-900 rounded-lg p-6">
                    <p className="text-slate-300">
                        This page will connect to: <code className="text-green-400">$Endpoint</code>
                    </p>
                </div>
            </div>
        </MentorLayout>
    );
}
"@
    
    Set-Content -Path $Path -Value $content -Encoding UTF8
    Write-Host "Created: $Path"
}

# Create all mentor pages
foreach ($page in $mentorPages) {
    $path = Join-Path $basePath "$($page.Name).tsx"
    Create-MentorPage -Name $page.Name -Title $page.Title -Endpoint $page.Endpoint -Path $path
}

Write-Host "`nGenerated all 12 Mentor pages successfully!"

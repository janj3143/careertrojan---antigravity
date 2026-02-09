"""
Enhanced LinkedIn Industry Classification System
==============================================

This module provides comprehensive industry categorization based on LinkedIn's
official industry taxonomy with detailed subcategories and business software
classifications for advanced job title enrichment.

Author: IntelliCV-AI Team
Date: September 30, 2025
"""

import json
import sys
from typing import Dict, List, Set, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging, get_logger, LoggingMixin
from utils.exception_handler import ExceptionHandler, SafeOperationsMixin

# Initialize logging
setup_logging()
logger = get_logger(__name__)

class LinkedInIndustryClassifier(LoggingMixin, SafeOperationsMixin):
    """Enhanced industry classifier using LinkedIn's official taxonomy"""
    
    def __init__(self):
        super().__init__()
        self.linkedin_industries = self._load_linkedin_industries()
        self.business_software_categories = self._load_business_software()
        self.industry_keywords = self._build_keyword_mappings()
    
    def _load_linkedin_industries(self) -> Dict[str, List[str]]:
        """Load LinkedIn's official industry categories and subcategories"""
        return {
            "Agriculture": [
                "Dairy", "Farming", "Fishery", "Ranching",
                "Agricultural and forestry machinery and equipment",
                "Agriculture and forestry", "Beverages", "Food",
                "Food, drink, tobacco and catering industry machinery and equipment",
                "Livestock and fish", "Organic products"
            ],
            
            "Arts": [
                "Arts & Crafts", "Fine Art", "Performing Arts", "Photography",
                "Animation", "Broadcast Media", "Computer Games", "Entertainment",
                "Media Production", "Mobile Games", "Motion Pictures & Film", "Music"
            ],
            
            "Construction": [
                "Building Materials", "Civil Engineering", "Construction",
                "Building industry", "Civil and marine engineering contractors",
                "Civil engineering and building machinery and equipment",
                "Furniture and linen", "Hardware, ironmongery, cutlery and tools",
                "Heating, ventilation, air conditioning (HVAC) and refrigeration equipment",
                "Metal constructions for the building industry",
                "Metal pipework, valves and containers", "Security equipment",
                "Timber, wooden products, machinery and equipment for the woodworking industry"
            ],
            
            "Consumer Goods": [
                "Apparel & Fashion", "Consumer Electronics", "Consumer Goods",
                "Consumer Services", "Cosmetics", "Food & Beverages", "Furniture",
                "Luxury Goods & Jewelry", "Sporting Goods", "Tobacco", "Wine and Spirits"
            ],
            
            "Corporate Services": [
                "Accounting", "Business Supplies & Equipment", "Environmental Services",
                "Events Services", "Executive Office", "Facilities Services",
                "Human Resources", "Information Services", "Management Consulting",
                "Outsourcing/Offshoring", "Professional Training & Coaching",
                "Security & Investigations", "Staffing & Recruiting",
                "Financial and insurance services", "Hire and rental services",
                "Hygiene and cleaning", "Services to businesses"
            ],
            
            "Design": [
                "Architecture & Planning", "Design", "Graphic Design"
            ],
            
            "Education": [
                "Education Management", "E-Learning", "Higher Education",
                "Primary/Secondary Education", "Research",
                "Education and training",
                "International organisations, administrations and associations",
                "Social care, personal services"
            ],
            
            "Energy & Mining": [
                "Mining & Metals", "Oil & Energy", "Utilities",
                "Energy, fuel and water", "Environmental services, renewable energies",
                "Oil and gas industry plant and equipment"
            ],
            
            "Entertainment": [
                "Animation", "Broadcast Media", "Computer Games", "Entertainment",
                "Media Production", "Mobile Games", "Motion Pictures & Film", "Music",
                "Hospitality, tourism, hotel and catering industries",
                "Leisure, culture and entertainment",
                "Postal services, telecommunications, radio and television",
                "Sports and leisure equipment"
            ],
            
            "Finance": [
                "Banking", "Capital Markets", "Financial Services", "Insurance",
                "Investment Banking", "Investment Management", "Venture Capital & Private Equity"
            ],
            
            "Hardware & Networking": [
                "Computer Hardware", "Computer Networking", "Nanotechnology",
                "Semiconductors", "Telecommunications", "Wireless",
                "Electrical equipment. Nuclear equipment",
                "Electronic equipment. Telecommunications equipment",
                "Measuring and testing equipment",
                "Optical, photographic and cinematographic equipment"
            ],
            
            "Health Care": [
                "Biotechnology", "Hospital & Health Care", "Medical Device",
                "Medical Practice", "Mental Health Care", "Pharmaceuticals", "Veterinary",
                "Chemical base materials", "Chemical industry plant and equipment",
                "Chemical products", "Health, medical and pharmaceutical",
                "Plastic products", "Rubber and plastic industry plant and equipment",
                "Rubber products"
            ],
            
            "Legal": [
                "Alternative Dispute Resolution", "Law Practice", "Legal Services"
            ],
            
            "Manufacturing": [
                "Automotive", "Aviation & Aerospace", "Chemicals", "Defense & Space",
                "Electrical & Electronic Manufacturing", "Food Production",
                "Glass, Ceramics & Concrete", "Industrial Automation", "Machinery",
                "Mechanical or Industrial Engineering", "Packaging & Containers",
                "Paper & Forest Products", "Plastics", "Railroad Manufacture",
                "Renewables & Environment", "Shipbuilding", "Textiles",
                "Basic metal products", "Engines and mechanical parts",
                "Industrial subcontractors", "Machinery and equipment for metalworking"
            ],
            
            "Media & Communications": [
                "Market Research", "Marketing & Advertising", "Newspapers",
                "Online Media", "Printing", "Public Relations & Communications",
                "Publishing", "Translation & Localization", "Writing & Editing",
                "Paper and board", "Paper and board making plant and equipment",
                "Printing and publishing", "Printing equipment. Office and shop equipment"
            ],
            
            "Nonprofit": [
                "Civic & Social Organization", "Fundraising", "Individual & Family Services",
                "International Trade & Development", "Libraries", "Museums & Institutions",
                "Non-Profit Organization Management", "Philanthropy", "Program Development",
                "Religious Institutions", "Think Tanks"
            ],
            
            "Public Administration": [
                "Government Administration", "Government Relations", "International Affairs",
                "Judiciary", "Legislative Office", "Political Organization", "Public Policy"
            ],
            
            "Public Safety": [
                "Law Enforcement", "Military", "Public Safety"
            ],
            
            "Real Estate": [
                "Commercial Real Estate", "Real Estate"
            ],
            
            "Recreation & Travel": [
                "Airlines/Aviation", "Gambling & Casinos", "Hospitality",
                "Leisure, Travel & Tourism", "Restaurants", "Recreational Facilities & Services", "Sports"
            ],
            
            "Retail": [
                "Retail", "Supermarkets", "Wholesale",
                "General traders, department and retail stores"
            ],
            
            "Software & IT Services": [
                "Computer & Network Security", "Computer Software",
                "Information Technology & Services", "Internet",
                "Information technology (IT) and Internet", "Research and testing",
                "Technical offices and engineering consultancies, architects"
            ],
            
            "Transportation & Logistics": [
                "Import & Export", "Logistics & Supply Chain", "Maritime",
                "Package/Freight Delivery", "Transportation/Trucking/Railroad", "Warehousing",
                "Handling and storage plant and equipment", "Means of transport",
                "Packaging machinery, equipment and services",
                "Transportation and logistics services"
            ],
            
            "Wellness & Fitness": [
                "Alternative Medicine", "Health, Wellness & Fitness"
            ],
            
            "Textiles & Fashion": [
                "Clothing and footwear", "Leathers, furs and their products",
                "Precious stoneworking, watchmaking and jewellery",
                "Textile, clothing, leather and shoemaking machinery and equipment", "Textiles"
            ],
            
            "Minerals & Materials": [
                "Glass, cement and ceramics",
                "Mining, quarrying and stoneworking plant and equipment",
                "Ores and minerals", "Quarried stone"
            ]
        }
    
    def _load_business_software(self) -> Dict[str, List[str]]:
        """Load comprehensive business software categories"""
        return {
            "Business Management": [
                "360 Degree Feedback", "Absence Management", "Account Based Marketing",
                "Accounting", "Accounting Practice Management", "Accounts Payable",
                "Accounts Receivable", "Accreditation Management", "Advanced Planning and Scheduling (APS)",
                "Affiliate", "Agile Project Management", "All-in-One Marketing Platform",
                "Alumni Management", "AML", "Apartment Management Systems", "Applicant Tracking",
                "Application Development", "Application Lifecycle Management",
                "Application Performance Management", "Appointment Scheduling", "Asset Tracking",
                "Association Management", "Attendance Tracking", "Audit", "Benefits Administration",
                "Billing and Invoicing", "Board Management", "Budgeting", "Business Intelligence",
                "Business Management", "Business Performance Management", "Business Process Management",
                "Calendar", "Campaign Management", "Capacity Planning", "Career Management",
                "Change Management", "Channel Management", "Claims Processing", "Client Onboarding",
                "Collaboration", "Commission", "Community", "Company Secretarial",
                "Compensation Management", "Compliance", "Configuration Management Tools",
                "Contact Management", "Content Management", "Contract Management",
                "Contractor Management", "Corporate Social Responsibility (CSR)", "Corporate Tax",
                "Corporate Wellness", "Course Authoring", "Credentialing", "CRM",
                "Customer Communications Management", "Customer Data Platform", "Customer Engagement",
                "Customer Experience", "Customer Journey Mapping Tools", "Customer Loyalty",
                "Customer Reference Management", "Customer Retention", "Customer Satisfaction",
                "Customer Service", "Customer Success", "Customer Support", "Customer Training"
            ],
            
            "Technology & Development": [
                "3D Architecture", "3D CAD", "3D Rendering", "AB Testing", "Access Governance",
                "Ad Server", "Address Verification", "AI Code Generator", "AI Detection",
                "AI Image Generator", "AI Marketing Tools", "AI Sales Assistant", "AI Video Generator",
                "AI Writing Assistant", "AIOps Platforms", "Android Kiosk", "Animation",
                "Anti-spam", "AntiVirus", "API Management", "App Building", "App Design",
                "App Store Optimization Tools", "Application Development", "Application Lifecycle Management",
                "Application Performance Management", "Artificial Intelligence", "Augmented Reality",
                "Authentication", "Automated Testing", "Backup", "Barcoding", "Big Data",
                "BIM", "Blockchain Platforms", "Blog", "Bot Detection and Mitigation",
                "Browser", "Bug Tracking", "Business Card", "Business Continuity",
                "Business Phone Systems", "Call Accounting", "Call Center", "Call Recording",
                "Call Tracking", "Chatbot", "Click Fraud", "Cloud Access Security Broker (CASB)",
                "Cloud Communication Platform", "Cloud Management", "Cloud PBX", "Cloud Security",
                "Cloud Storage", "CMDB", "Code Enforcement", "Computer Security",
                "Configuration Management Tools", "Container Security", "Content Collaboration",
                "Content Delivery Network", "Continuous Integration", "Conversational AI Platform",
                "Cryptocurrency Exchange", "Cryptocurrency Wallets", "Cybersecurity",
                "Dashboard", "Data Analysis", "Data Catalog", "Data Collection", "Data Discovery",
                "Data Entry", "Data Extraction", "Data Governance", "Data Loss Prevention",
                "Data Management", "Data Management Platforms", "Data Mining", "Data Preparation",
                "Data Privacy", "Data Quality", "Data Visualization", "Data Warehouse",
                "Database", "Database Monitoring", "DDoS Protection", "Deep Learning",
                "Desktop as a Service (DaaS)", "DevOps", "Digital Adoption Platform",
                "Digital Asset Management", "Digital Experience Platforms (DXP)", "Digital Forensics",
                "Digital Rights Management", "Digital Signature", "Digital Workplace",
                "Directory", "Disaster Recovery", "Disk Imaging", "Document Control",
                "Document Generation", "Document Management", "Document Version Control",
                "EDI", "Email Archiving", "Email Management", "Email Security", "Email Signature",
                "Email Tracking", "Email Verification Tools", "Embedded Analytics",
                "Emergency Notification", "Employee Monitoring", "Encryption",
                "Endpoint Detection and Response", "Endpoint Protection", "Enterprise Architecture",
                "Enterprise Content Management", "Enterprise Legal Management",
                "Enterprise Resource Planning", "Enterprise Search", "Enterprise Service Bus (ESB)",
                "ETL", "Facial Recognition", "Fax Server", "File Sharing", "File Sync",
                "Firewall", "Form Builder", "Forms Automation", "Game Development",
                "Gamification", "GDPR Compliance", "Generative AI", "GIS", "Headless CMS",
                "Headless eCommerce", "Help Desk", "HIPAA Compliance", "Identity Management",
                "Identity Threat Detection and Response (ITDR)", "Identity Verification",
                "Image Recognition", "Incident Management", "Infrastructure as a Service (IaaS)",
                "Integration", "Integrated Development Environment (IDE)", "Internet",
                "IoT", "IoT Analytics", "iPaaS", "iPad Kiosk", "IT Asset Management",
                "IT Documentation", "IT Management", "IT Project Management", "IT Service",
                "IT Ticketing Systems", "ITSM", "IVR", "IWMS", "Java CMS", "Key Management",
                "Kiosk", "Knowledge Base", "Knowledge Management", "Language Learning",
                "Live Chat", "Live Streaming", "Load Balancing", "Load Testing",
                "Log Analysis", "Log Management", "Low Code Development Platform",
                "Machine Learning", "Managed Service Providers (MSP)", "Master Data Management",
                "Metadata Management", "Microlearning", "Mobile Analytics", "Mobile Banking",
                "Mobile Content Management System", "Mobile Device Management", "Mobile Event Apps",
                "Mobile Learning", "Mobile Marketing", "Mobility", "Multi-Factor Authentication",
                "Natural Language Processing (NLP)", "Network Access Control (NAC)",
                "Network Management", "Network Mapping", "Network Monitoring", "Network Security",
                "Network Troubleshooting", "NFT Creation", "No Code Platform", "NoSQL Databases",
                "Note-Taking", "Observability", "OCR", "Online Banking", "Operating Systems",
                "Password Management", "Patch Management", "PDF", "PDF Editor",
                "Penetration Testing", "Performance Testing", "Personalization",
                "Physical Security", "Plagiarism Checker", "Platform as a Service (PaaS)",
                "Polling", "Portal", "Predictive Analytics", "Predictive Dialer",
                "Predictive Lead Scoring", "Presentation", "Privileged Access Management",
                "Proctoring", "Product Analytics", "Product Configurator", "Product Data Management",
                "Product Lifecycle Management", "Product Management", "Product Roadmap",
                "Productivity", "Prototyping", "Push Notifications", "RDBMS",
                "Remote Desktop", "Remote Monitoring and Management", "Remote Support",
                "Remote Work", "Reporting", "Requirements Management", "Robotic Process Automation",
                "SaaS Management", "SCADA", "Screen Recording", "Screen Sharing",
                "Secure Email Gateway", "Security Awareness Training", "Self-Service Password Reset (SSPR)",
                "SEO", "Server Backup", "Server Management", "Server Monitoring", "Service Desk",
                "Shipment Tracking", "SIEM", "Simulation", "Single Sign On", "SMS Marketing",
                "SMS Survey", "SOAR", "Social CRM Tools", "Social Listening Tools",
                "Social Media Analytics Tools", "Social Media Management", "Social Media Marketing",
                "Social Media Monitoring", "Social Networking", "Social Selling", "Softphone",
                "Source Code Management", "Speech Analytics", "Speech Recognition",
                "Speech Therapy", "Static Application Security Testing (SAST)",
                "Statistical Analysis", "Survey", "Telecom Expense Management", "Telephony",
                "Test Management Tools", "Text Mining", "Text to Image", "Text-To-Speech",
                "Third Party Logistics (3PL)", "Threat Intelligence", "Time and Expense",
                "Time Clock", "Time Tracking", "Transcription", "Translation Management",
                "UGC Platform", "Unified Communications", "Unified Endpoint Management (UEM)",
                "URL Shortener", "User Experience (UX)", "User Testing", "VDI",
                "Vector Graphics", "Video Conferencing", "Video Editing", "Video Hosting",
                "Video Interviewing", "Video Making", "Video Management", "Video Marketing",
                "Video Surveillance", "Virtual Assistant", "Virtual Classroom",
                "Virtual Data Room", "Virtual Event", "Virtual Machine", "Virtual Private Server",
                "Virtual Reality (VR)", "Virtual Tour", "Virtualization", "Visitor Management",
                "Visual Search", "VoIP", "VPN", "Vulnerability Management", "Vulnerability Scanner",
                "Web Analytics", "Web Conferencing", "Web Content Management", "Web Scraping",
                "Web to Print", "Webinar", "Website Accessibility", "Website Builder",
                "Website Monitoring", "Website Optimization Tools", "Website Security",
                "Whiteboard", "Wireframe", "Wireless Expense Management", "Workflow Management",
                "XDR (Extended Detection & Response)"
            ],
            
            "Industry-Specific Solutions": [
                "Aerospace Manufacturing", "Advertising Agency", "Advocacy", "Airline Reservation System",
                "Animal Shelter", "Apparel Management", "Applied Behavior Analysis",
                "Appointment Reminder", "Arborist", "Architectural CAD", "Architecture",
                "Archiving", "Art Gallery", "Assisted Living", "Auction", "Audience Response",
                "Audio Conferencing", "Audio Editing", "Auto Body", "Auto Dealer",
                "Auto Dealer Accounting", "Auto Dialer", "Auto Repair", "Aviation Maintenance",
                "B2B eCommerce Platform", "Background Check", "Bakery", "Banking Systems",
                "Bankruptcy", "Bar POS", "Barbershop", "Benefits Administration", "Bookkeeper",
                "Brand Management", "Brand Protection", "Brewery", "Brokerage Management",
                "Building Maintenance", "Business Plan", "Buyer Intent", "Calibration Management",
                "Call Center Workforce Management", "Camp Management", "Campground Management",
                "Car Rental", "Cardiology EMR", "Carpet Cleaning", "Catalog Management",
                "Catering", "Cemetery", "Certification Tracking", "Chargeback Management",
                "Chemical", "Chemical Manufacturing", "Chiropractic", "Church Accounting",
                "Church Management", "Church Presentation", "Class Registration",
                "Classroom Management", "Clinical Trial Management", "Closed Captioning",
                "Club Management", "CMMS", "Coaching", "Commercial Insurance", "Commercial Loan",
                "Commercial Property Management", "Commercial Real Estate", "Competitive Intelligence",
                "Competitor Price Monitoring", "Complaint Management", "Computer Repair Shop",
                "Conference", "Conflict Checking", "Consignment", "Construction Accounting",
                "Construction Bid Management", "Construction CRM", "Construction Estimating",
                "Construction Management", "Construction Scheduling", "Contact Center",
                "Contact Center Quality Assurance", "Content Marketing", "Contest",
                "Convenience Store", "Conversational Marketing Platform", "Corrective and Preventive Action",
                "Courier", "Court Management", "CPQ", "Creative Management", "CTRM",
                "Currency Exchange", "Customer Advocacy", "Dance Studio", "Daycare",
                "Debt Collection", "Decision Support", "DEI (Diversity, Equity & Inclusion)",
                "Delivery Management", "Demand Planning", "Demand Side Platform (DSP)", "Demo",
                "Dental", "Dental Charting", "Dental Imaging", "Dermatology", "Dermatology EMR",
                "Desk Booking", "Diagram", "Direct Deposit Payroll", "Direct Mail Automation",
                "Display Advertising", "Distribution", "Distribution Accounting", "Dock Scheduling",
                "Docketing", "Donation Management", "Driving School", "Dropshipping",
                "Dry Cleaning", "e-Prescribing", "EAM", "Earthwork Estimating", "eCommerce",
                "EHS Management", "eLearning Authoring Tools", "Electrical Contractor",
                "Electrical Design", "Electrical Estimating", "Electronic Data Capture",
                "Electronic Discovery", "Electronic Lab Notebook", "Electronic Medical Records",
                "eMAR", "Emissions Management", "Employee Advocacy", "Employee Communication Tools",
                "Employee Engagement", "Employee Recognition", "Employee Scheduling", "EMS",
                "Energy Management", "Engineering Accounting", "Engineering CAD", "Entity Management",
                "Environmental", "Equipment Maintenance", "Equipment Rental", "Equity Management",
                "ERM", "ESG", "Event Booking", "Event Check In", "Event Management",
                "Event Marketing", "Event Rental", "Exam", "Expense Report", "Facility Management",
                "Family Law", "Family Practice Electronic Medical Records", "Farm Management",
                "Fashion Design", "Festival Management", "Field Sales", "Field Service Management",
                "Financial Close", "Financial CRM", "Financial Fraud Detection",
                "Financial Management", "Financial Reporting", "Financial Risk Management",
                "Financial Services", "Fire Department", "Fitness", "Fixed Asset Management",
                "Fleet Maintenance", "Fleet Management", "Floor Plan", "Florist", "Flowchart",
                "Food Costing", "Food Delivery", "Food Manufacturing", "Food Service Distribution",
                "Food Service Management", "Food Traceability", "Food Truck POS Systems",
                "Forestry", "Franchise Management", "Freight", "Fuel Management", "Fund Accounting",
                "Fundraising", "Funeral Home", "Garage Door", "Garden Center", "General Ledger",
                "Golf Course", "Governance, Risk and Compliance (GRC)", "Government", "GPS Tracking",
                "Gradebook", "Grant Management", "Graphic Design", "Gym Management", "Gymnastics",
                "Handyman", "Healthcare CRM", "Healthcare LMS", "Heatmap", "Hedge Fund",
                "Higher Education", "HOA", "Home Builder", "Home Care", "Home Health Care",
                "Home Inspection", "Horse", "Hospice", "Hospital Management", "Hospitality LMS",
                "Hospitality Property Management", "Hostel Management", "Hotel Channel Management",
                "HR Analytics", "Human Resources", "Human Services", "HVAC", "HVAC Estimating",
                "Hybrid Events", "Idea Management", "Influencer Marketing", "Innovation Management",
                "Inside Sales", "Insight Engines", "Inspection", "Insurance", "Insurance CRM",
                "Insurance Policy", "Insurance Rating", "Integrated Risk Management",
                "Intellectual Property Management", "Internal Communications", "Intranet",
                "Inventory Control", "Inventory Management", "Investigation Management",
                "Investment Management", "iPad POS", "Issue Tracking", "Jail Management",
                "Janitorial", "Jewelry Store Management", "Job Board", "Job Costing",
                "Job Evaluation", "Job Shop", "K-12", "Kanban Tools", "Kennel",
                "Keyword Research Tools", "KPI", "KYC", "Label Printing",
                "Laboratory Information Management System", "Laboratory Information Systems (LIS)",
                "Land Management", "Landing Page", "Landscape", "Law Enforcement",
                "Law Practice Management", "Lawn Care", "Lead Capture", "Lead Generation",
                "Lead Management", "Lead Nurturing", "Learning Experience Platform",
                "Learning Management System", "Lease Accounting", "Lease Management",
                "Leave Management System", "Legal Accounting", "Legal Billing", "Legal Calendar",
                "Legal Case Management", "Legal Document Management", "Legal Research",
                "Library Automation", "License Management", "Link Management Tools",
                "Liquor Store POS", "Local SEO Tools", "Localization", "Location Intelligence",
                "Locksmith", "Logbook", "Logistics", "Long Term Care", "Lost and Found",
                "Mac CRM", "Maid Service", "Mailroom Management", "Maintenance Management",
                "Manufacturing", "Manufacturing Execution", "Manufacturing Inventory Management",
                "Marine", "Market Research", "Marketing Analytics", "Marketing Attribution",
                "Marketing Automation", "Marketing Planning", "Marketplace", "Martial Arts",
                "Massage Therapy", "Medical Accounting", "Medical Billing", "Medical Imaging",
                "Medical Inventory", "Medical Lab", "Medical Practice Management",
                "Medical Scheduling", "Medical Spa", "Medical Transcription", "Meeting",
                "Meeting Room Booking System", "Membership Management", "Mental Health",
                "Mental Health EHR", "Mentoring", "Metal Fabrication", "Mileage Tracking",
                "Mind Mapping", "Mining", "MLM", "Mobile Credit Card Processing",
                "Mobile Home Park Management", "Mortgage", "Motel", "Moving", "MRM", "MRP",
                "Multi-Channel eCommerce", "Multi-Country Payroll", "Municipal", "Museum",
                "Music School", "Neurology EMR", "Nonprofit", "Nonprofit Accounting",
                "Nonprofit CRM", "Nonprofit Project Management", "NPS", "Nurse Scheduling",
                "Nursing Home", "Nutrition Analysis", "Nutritionist", "OBGYN EMR",
                "Occupational Health", "Occupational Therapy", "OEE", "Oil and Gas", "OKR",
                "Onboarding", "Online CRM", "Online Ordering", "Online Proofing",
                "Ophthalmology EMR", "Optometry", "Order Entry", "Order Fulfillment",
                "Order Management", "Org Chart", "Orthopedic EMR", "P&C Insurance", "Packaging",
                "PACS", "Pain Management EMR", "Parcel Audit", "Parking Management",
                "Parks and Recreation", "Partner Management", "Patient Case Management",
                "Patient Engagement", "Patient Management", "Patient Portal", "Patient Scheduling",
                "Pawn Shop", "Payment Processing", "Payroll", "PCI Compliance", "Pediatric",
                "PEO", "Performance Management System", "Permit", "Personal Trainer",
                "Pest Control", "Pet Grooming", "Pet Sitting", "Pharmacy", "Photo Editing",
                "Photography Studio", "Physical Therapy", "Pilates Studio", "PIM",
                "Plastic Surgery", "Plumbing", "Plumbing Estimating", "Podcast Hosting",
                "Podiatry", "Podiatry EMR", "Point of Sale", "Policy Management",
                "Political Campaign", "Pool Service", "PPC", "Pre-employment Testing",
                "Pricing Optimization", "Primary Care EHR", "Print Estimating", "Print Management",
                "Procure to Pay", "Procurement", "Production Scheduling", "Professional Services Automation",
                "Project Accounting", "Project Management", "Project Planning", "Project Portfolio Management",
                "Project Tracking", "Proofreading", "Property Management", "Property Management Accounting",
                "Proposal Management", "Psychiatry Electronic Medical Records", "Public Relations",
                "Public Transportation", "Public Works", "Publishing and Subscriptions",
                "Punch List", "Purchasing", "Qualitative Data Analysis", "Quality Management",
                "Quoting", "Radiology", "Real Estate Accounting", "Real Estate Agency",
                "Real Estate CMA", "Real Estate CRM", "Real Estate Property Management",
                "Real Estate Transaction Management", "Recruiting", "Recruiting Agency",
                "Recruitment Marketing Platforms", "Recurring Billing", "Recycling",
                "Reference Check", "Referral", "Registration", "Relocation", "Remodeling Estimating",
                "Remote Patient Monitoring", "Rental", "Reputation Management", "Reservations",
                "Residential Construction Estimating", "Resource Management", "Restaurant Management",
                "Restaurant POS", "Retail Execution", "Retail Management Systems",
                "Retail POS System", "Retargeting", "Returns Management (RMS)",
                "Revenue Cycle Management", "Revenue Management", "Revenue Recognition",
                "Review Management", "RFP", "Risk Management", "Roofing", "Route Planning",
                "Safety Management", "Sales Coaching", "Sales Content Management",
                "Sales Enablement", "Sales Engagement Platform", "Sales Force Automation",
                "Sales Forecasting", "Sales Intelligence", "Sales Performance Management",
                "Sales Tax", "Sales Tracking", "Salon", "Scheduling", "Scholarship Management",
                "School Accounting", "School Bus Routing", "School Facilities Management",
                "School Management", "Screenwriting", "Scrum", "Security System Installer",
                "Self Storage", "Service Dispatch", "Shipping", "Shopping Cart", "Small Business CRM",
                "Small Business eCommerce", "Small Business Loyalty Programs", "Social Work Case Management",
                "Solar", "Sourcing", "Spa", "Space Management", "SPC", "Spend Management",
                "Sports League", "Spreadsheet", "Staffing Agency", "Stock Portfolio Management",
                "Store Locator", "Strategic Planning", "Student Engagement Platform",
                "Student Information System", "Subcontractor", "Subscription Management",
                "Substance Abuse EMR", "Succession Planning", "Supply Chain Management",
                "Sustainability", "Swim School", "Takeoff", "Talent Management", "Task Management",
                "Tattoo Studio", "Tax Practice Management", "Tax Preparation", "Team Communication",
                "Team Management", "Telemarketing", "Telemedicine", "Therapy", "Therapy Notes",
                "Ticketing", "Timeshare", "Tool Management", "Tour Operator", "Towing",
                "Trade Promotion Management", "Training", "Transactional Email",
                "Transportation Dispatch", "Transportation Management", "Travel Agency",
                "Travel Management", "Treasury", "Trucking", "Trucking Accounting", "Trust Accounting",
                "Tutoring", "Urgent Care EMR", "Urology EMR", "Utility Billing",
                "Utility Management Systems", "Vacation Rental", "Vaccine Management",
                "Vendor Management", "Venue Management", "Veterinary", "Volunteer Management",
                "Voting", "Waitlist", "Waiver", "Warehouse Management", "Warranty Management",
                "Waste Management", "Whistleblowing", "Winery", "Wireless Expense Management",
                "Work Order", "Workforce Management", "Worship", "Yard Management", "Yoga Studio"
            ]
        }
    
    def _build_keyword_mappings(self) -> Dict[str, Set[str]]:
        """Build keyword mappings for intelligent classification"""
        keyword_mappings = {}
        
        # Build keywords from LinkedIn industries
        for industry, subcategories in self.linkedin_industries.items():
            keywords = set()
            
            # Add industry name keywords
            keywords.update(industry.lower().split())
            
            # Add subcategory keywords
            for subcategory in subcategories:
                # Extract meaningful keywords
                words = subcategory.lower().replace('&', 'and').split()
                keywords.update([word.strip('.,()') for word in words if len(word) > 2])
            
            keyword_mappings[industry] = keywords
        
        return keyword_mappings
    
    def classify_job_title(self, job_title: str) -> Dict[str, any]:
        """Classify a job title using LinkedIn industry taxonomy"""
        if not job_title:
            return {"primary_industry": "Unknown", "confidence": 0.0, "matches": []}
        
        title_lower = job_title.lower()
        title_words = set(title_lower.replace('&', 'and').split())
        
        # Score each industry
        industry_scores = {}
        
        for industry, keywords in self.industry_keywords.items():
            # Calculate keyword overlap
            common_keywords = title_words.intersection(keywords)
            
            if common_keywords:
                # Score based on keyword relevance and frequency
                score = len(common_keywords) / len(title_words)
                
                # Boost score for exact industry matches
                if industry.lower() in title_lower:
                    score += 0.5
                
                # Boost score for specific subcategory matches
                for subcategory in self.linkedin_industries[industry]:
                    if subcategory.lower() in title_lower:
                        score += 0.3
                        break
                
                industry_scores[industry] = min(score, 1.0)
        
        # Sort by score
        sorted_matches = sorted(industry_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Determine primary industry
        primary_industry = sorted_matches[0][0] if sorted_matches else "Other"
        confidence = sorted_matches[0][1] if sorted_matches else 0.0
        
        return {
            "primary_industry": primary_industry,
            "confidence": confidence,
            "matches": sorted_matches[:3],  # Top 3 matches
            "subcategories": self.linkedin_industries.get(primary_industry, [])
        }
    
    def get_industry_insights(self, industry: str) -> Dict[str, any]:
        """Get detailed insights about a specific industry"""
        if industry not in self.linkedin_industries:
            return {"error": f"Industry '{industry}' not found"}
        
        subcategories = self.linkedin_industries[industry]
        
        # Calculate growth indicators based on technology adoption
        tech_indicators = self._calculate_tech_adoption(subcategories)
        
        return {
            "industry": industry,
            "subcategories": subcategories,
            "subcategory_count": len(subcategories),
            "technology_adoption": tech_indicators,
            "related_software": self._get_related_software(industry),
            "career_paths": self._suggest_career_paths(industry)
        }
    
    def _calculate_tech_adoption(self, subcategories: List[str]) -> str:
        """Calculate technology adoption level for industry"""
        tech_keywords = {'digital', 'technology', 'software', 'automation', 'ai', 'data', 'cloud'}
        
        tech_count = sum(1 for sub in subcategories 
                        if any(keyword in sub.lower() for keyword in tech_keywords))
        
        adoption_rate = tech_count / len(subcategories) if subcategories else 0
        
        if adoption_rate > 0.3:
            return "High Technology Adoption"
        elif adoption_rate > 0.1:
            return "Moderate Technology Adoption"
        else:
            return "Traditional Industry"
    
    def _get_related_software(self, industry: str) -> List[str]:
        """Get software categories related to the industry"""
        industry_software_mapping = {
            "Software & IT Services": self.business_software_categories["Technology & Development"],
            "Finance": ["Banking Systems", "Financial Services", "Investment Management", "Insurance"],
            "Health Care": ["Electronic Medical Records", "Medical Practice Management", "Hospital Management"],
            "Education": ["Learning Management System", "Student Information System", "eLearning Authoring Tools"],
            "Manufacturing": ["Manufacturing Execution", "Quality Management", "Supply Chain Management"],
            "Construction": ["Construction Management", "Project Management", "CAD", "Estimating"],
            "Retail": ["Point of Sale", "Inventory Management", "eCommerce", "Customer Management"],
            "Real Estate": ["Real Estate CRM", "Property Management", "Real Estate Transaction Management"]
        }
        
        return industry_software_mapping.get(industry, ["CRM", "Project Management", "Accounting"])[:10]
    
    def _suggest_career_paths(self, industry: str) -> List[str]:
        """Suggest career progression paths for the industry"""
        career_paths = {
            "Software & IT Services": [
                "Developer → Senior Developer → Lead Developer → Engineering Manager → CTO",
                "Analyst → Senior Analyst → Consultant → Principal Consultant → Practice Lead",
                "Support → Senior Support → Team Lead → Support Manager → Operations Director"
            ],
            "Finance": [
                "Analyst → Senior Analyst → Associate → VP → Managing Director",
                "Accountant → Senior Accountant → Accounting Manager → Controller → CFO",
                "Advisor → Senior Advisor → Portfolio Manager → Investment Director"
            ],
            "Health Care": [
                "Technician → Senior Technician → Supervisor → Manager → Director",
                "Specialist → Senior Specialist → Department Head → Medical Director",
                "Coordinator → Manager → Director → VP of Operations"
            ],
            "Education": [
                "Teacher → Senior Teacher → Department Head → Vice Principal → Principal",
                "Instructor → Senior Instructor → Program Manager → Academic Director",
                "Coordinator → Manager → Director → VP of Education"
            ]
        }
        
        return career_paths.get(industry, [
            "Specialist → Senior Specialist → Manager → Director → VP",
            "Coordinator → Supervisor → Manager → Director → Executive"
        ])
    
    def export_enhanced_classification(self) -> Dict:
        """Export the complete enhanced classification system"""
        return {
            "linkedin_industries": self.linkedin_industries,
            "business_software_categories": self.business_software_categories,
            "total_industries": len(self.linkedin_industries),
            "total_subcategories": sum(len(subs) for subs in self.linkedin_industries.values()),
            "total_software_categories": sum(len(cats) for cats in self.business_software_categories.values()),
            "generated_at": datetime.now().isoformat(),
            "version": "2.0_linkedin_enhanced"
        }

def main():
    """Test the enhanced LinkedIn industry classifier"""
    classifier = LinkedInIndustryClassifier()
    
    # Test classifications
    test_titles = [
        "Software Engineer",
        "Marketing Manager", 
        "Registered Nurse",
        "Financial Analyst",
        "Construction Project Manager",
        "Digital Marketing Specialist",
        "Data Scientist",
        "HR Generalist"
    ]
    
    logger.info("🚀 Enhanced LinkedIn Industry Classification Test")
    logger.info("=" * 60)
    
    for title in test_titles:
        result = classifier.classify_job_title(title)
        logger.info(f"\n📋 **{title}**")
        logger.info(f"   Primary Industry: {result['primary_industry']}")
        logger.info(f"   Confidence: {result['confidence']:.2f}")
        if result['matches']:
            logger.info(f"   Top Matches: {[f'{ind} ({score:.2f})' for ind, score in result['matches'][:2]]}")
    
    # Export enhanced system
    export_data = classifier.export_enhanced_classification()
    logger.info(f"\n📊 **Enhanced Classification System Stats:**")
    logger.info(f"   LinkedIn Industries: {export_data['total_industries']}")
    logger.info(f"   Industry Subcategories: {export_data['total_subcategories']}")
    logger.info(f"   Software Categories: {export_data['total_software_categories']}")

if __name__ == "__main__":
    main()
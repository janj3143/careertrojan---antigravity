"""
IntelliCV-AI Job Title Normalization and Enhancement Engine
==========================================================

This module processes and normalizes job titles from various sources to enhance
the AI engine's capability for:
- Job title standardization
- Career progression mapping
- User experience enhancement
- Interview preparation guidance
- Career coaching insights

Author: IntelliCV-AI Team
Date: September 30, 2025
"""

import json
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path
from datetime import datetime

class JobTitleEnhancementEngine:
    """Advanced job title processing and enhancement engine"""
    
    def __init__(self):
        self.raw_titles = []
        self.categorized_titles = {}
        self.normalized_titles = {}
        self.career_progressions = {}
        self.industry_mappings = {}
        
    def load_raw_job_titles(self, filepath: str) -> List[str]:
        """Load and parse raw job titles from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract job titles (handling various formats)
            titles = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Split on common separators
                    if ',' in line:
                        titles.extend([t.strip() for t in line.split(',')])
                    elif ';' in line:
                        titles.extend([t.strip() for t in line.split(';')])
                    else:
                        titles.append(line)
            
            return [t for t in titles if t and len(t) > 2]
            
        except Exception as e:
            print(f"Error loading job titles from {filepath}: {e}")
            return []
    
    def normalize_job_title(self, title: str) -> str:
        """Normalize job title by fixing common issues"""
        if not title:
            return ""
            
        # Fix common typos and standardize
        title = title.strip()
        
        # Common typo fixes
        typo_fixes = {
            'Legasl': 'Legal',
            'Assisitant': 'Assistant',
            'Clerck': 'Clerk',
            'Specilaist': 'Specialist',
            'Spcilaist': 'Specialist',
            'Specilait': 'Specialist',
            'Specilaist': 'Specialist',
            'SPecilaist': 'Specialist',
            'SPECIALIST': 'Specialist',
            'MANAGER': 'Manager',
            'DIRECTOR': 'Director',
            'Programer': 'Programmer',
            'Pythom': 'Python',
            'Biotechnolgu': 'Biotechnology',
            'Catalsyt': 'Catalyst',
            'Develpoment': 'Development',
            'Delpoer': 'Developer',
            'Softwar': 'Software',
            'Vetenarian': 'Veterinarian',
            'Speciloaist': 'Specialist',
            'Analaysts': 'Analyst',
            'Analsys': 'Analysis',
            'Qaulity': 'Quality',
            'Surver': 'Survey',
            'Controsl': 'Controls',
            'Rspiratory': 'Respiratory',
            'Stockholder': 'Stakeholder',
            'Voip': 'VoIP',
            'Technition': 'Technician',
            'Oseopath': 'Osteopath',
            'Adminisitrator': 'Administrator',
            'Specilait': 'Specialist',
            'mamanger': 'Manager',
            'Pharceutical': 'Pharmaceutical',
            'Gynacologist': 'Gynecologist',
            'Paprlegal': 'Paralegal',
            'Accoujnt': 'Account',
            'Nurdse': 'Nurse',
            'Analaysts': 'Analysts',
            'Newcaster': 'Newscaster',
            'Mortgae': 'Mortgage',
            'Direcotr': 'Director',
            'amanger': 'Manager',
            'ssupervisor': 'Supervisor',
            'Assisitant': 'Assistant',
            'Attorny': 'Attorney',
            'Councellor': 'Counsellor',
            'Co-ordinator': 'Coordinator',
            'Se;lf': 'Self',
            'Analysst': 'Analyst',
            'Specialilst': 'Specialist',
            'Develpoment': 'Development',
            'Robotics': 'Robotics',
            'Finaince': 'Finance',
            'manger': 'Manager',
            'Eastate': 'Estate',
            'Resouces': 'Resources',
            'Qaulity': 'Quality',
            'Qaulity': 'Quality'
        }
        
        # Apply typo fixes
        for typo, correct in typo_fixes.items():
            title = re.sub(r'\b' + re.escape(typo) + r'\b', correct, title, flags=re.IGNORECASE)
        
        # Standardize common abbreviations
        abbreviations = {
            r'\bVP\b': 'Vice President',
            r'\bSVP\b': 'Senior Vice President',
            r'\bCEO\b': 'Chief Executive Officer',
            r'\bCTO\b': 'Chief Technology Officer',
            r'\bCFO\b': 'Chief Financial Officer',
            r'\bCOO\b': 'Chief Operating Officer',
            r'\bCMO\b': 'Chief Marketing Officer',
            r'\bHR\b': 'Human Resources',
            r'\bIT\b': 'Information Technology',
            r'\bQA\b': 'Quality Assurance',
            r'\bQHE\b': 'Quality Health Environment',
            r'\bEHS\b': 'Environment Health Safety',
            r'\bRFID\b': 'Radio Frequency Identification',
            r'\bPLC\b': 'Programmable Logic Controller',
            r'\bFCC\b': 'Federal Communications Commission',
            r'\bETL\b': 'Extract Transform Load',
            r'\bSAP\b': 'Systems Applications Products',
            r'\bJ2EE\b': 'Java 2 Enterprise Edition'
        }
        
        for abbrev, full_form in abbreviations.items():
            title = re.sub(abbrev, full_form, title, flags=re.IGNORECASE)
        
        # Clean up extra spaces and formatting
        title = re.sub(r'\s+', ' ', title)
        title = title.strip()
        
        # Proper case for titles
        if title.isupper() or title.islower():
            title = title.title()
        
        return title
    
    def categorize_by_industry(self, titles: List[str]) -> Dict[str, List[str]]:
        """Categorize job titles by industry"""
        categories = {
            'Technology & IT': [],
            'Healthcare & Medicine': [],
            'Finance & Accounting': [],
            'Engineering & Technical': [],
            'Sales & Marketing': [],
            'Management & Leadership': [],
            'Human Resources': [],
            'Legal & Compliance': [],
            'Operations & Logistics': [],
            'Education & Training': [],
            'Construction & Manufacturing': [],
            'Hospitality & Service': [],
            'Creative & Design': [],
            'Science & Research': [],
            'Government & Public Service': [],
            'Other': []
        }
        
        # Keywords for categorization
        tech_keywords = ['software', 'developer', 'programmer', 'it', 'technology', 'data', 'system', 'network', 'cloud', 'cyber', 'web', 'mobile', 'database', 'ai', 'machine learning', 'devops']
        healthcare_keywords = ['medical', 'doctor', 'nurse', 'healthcare', 'physician', 'surgeon', 'therapist', 'hospital', 'clinical', 'pharmaceutical', 'dentist', 'veterinarian']
        finance_keywords = ['finance', 'accounting', 'accountant', 'financial', 'banking', 'investment', 'audit', 'tax', 'payroll', 'actuary', 'insurance']
        engineering_keywords = ['engineer', 'engineering', 'technical', 'mechanical', 'electrical', 'civil', 'chemical', 'process', 'maintenance', 'quality', 'manufacturing']
        sales_keywords = ['sales', 'marketing', 'account', 'customer', 'business development', 'representative', 'specialist', 'advertising', 'promotion']
        management_keywords = ['manager', 'director', 'executive', 'president', 'officer', 'supervisor', 'coordinator', 'leader', 'head', 'chief']
        hr_keywords = ['human resources', 'hr', 'recruitment', 'talent', 'personnel', 'training', 'benefits', 'employee']
        legal_keywords = ['legal', 'lawyer', 'attorney', 'paralegal', 'compliance', 'regulatory', 'law', 'counsel']
        operations_keywords = ['operations', 'logistics', 'warehouse', 'supply', 'procurement', 'purchasing', 'transportation', 'driver']
        education_keywords = ['teacher', 'professor', 'education', 'training', 'instructor', 'lecturer', 'tutor', 'academic']
        construction_keywords = ['construction', 'builder', 'contractor', 'architect', 'planner', 'surveyor', 'welder', 'electrician', 'plumber']
        hospitality_keywords = ['hospitality', 'hotel', 'restaurant', 'food', 'service', 'cook', 'chef', 'bartender', 'server']
        creative_keywords = ['designer', 'artist', 'creative', 'graphic', 'visual', 'marketing', 'content', 'writer', 'editor', 'journalist']
        science_keywords = ['research', 'scientist', 'analyst', 'laboratory', 'development', 'biotechnology', 'environmental', 'geologist']
        government_keywords = ['government', 'public', 'civil servant', 'police', 'military', 'municipal', 'federal', 'state']
        
        keyword_mapping = {
            'Technology & IT': tech_keywords,
            'Healthcare & Medicine': healthcare_keywords,
            'Finance & Accounting': finance_keywords,
            'Engineering & Technical': engineering_keywords,
            'Sales & Marketing': sales_keywords,
            'Management & Leadership': management_keywords,
            'Human Resources': hr_keywords,
            'Legal & Compliance': legal_keywords,
            'Operations & Logistics': operations_keywords,
            'Education & Training': education_keywords,
            'Construction & Manufacturing': construction_keywords,
            'Hospitality & Service': hospitality_keywords,
            'Creative & Design': creative_keywords,
            'Science & Research': science_keywords,
            'Government & Public Service': government_keywords
        }
        
        for title in titles:
            title_lower = title.lower()
            categorized = False
            
            for category, keywords in keyword_mapping.items():
                if any(keyword in title_lower for keyword in keywords):
                    categories[category].append(title)
                    categorized = True
                    break
            
            if not categorized:
                categories['Other'].append(title)
        
        return categories
    
    def extract_career_progressions(self, titles: List[str]) -> Dict[str, List[str]]:
        """Extract career progression paths from job titles"""
        progressions = {}
        
        # Define progression hierarchies
        hierarchies = {
            'Software Development': [
                'Junior Developer', 'Developer', 'Software Developer', 'Senior Developer', 
                'Lead Developer', 'Principal Developer', 'Architect', 'Senior Architect',
                'Engineering Manager', 'Engineering Director', 'VP Engineering', 'CTO'
            ],
            'Sales': [
                'Sales Associate', 'Sales Representative', 'Senior Sales Representative',
                'Account Executive', 'Senior Account Executive', 'Sales Manager',
                'Senior Sales Manager', 'Sales Director', 'VP Sales', 'Chief Sales Officer'
            ],
            'Marketing': [
                'Marketing Assistant', 'Marketing Coordinator', 'Marketing Specialist',
                'Senior Marketing Specialist', 'Marketing Manager', 'Senior Marketing Manager',
                'Marketing Director', 'VP Marketing', 'Chief Marketing Officer'
            ],
            'Human Resources': [
                'HR Assistant', 'HR Coordinator', 'HR Generalist', 'HR Specialist',
                'Senior HR Specialist', 'HR Manager', 'Senior HR Manager',
                'HR Director', 'VP Human Resources', 'Chief Human Resources Officer'
            ],
            'Finance': [
                'Financial Analyst', 'Senior Financial Analyst', 'Finance Manager',
                'Senior Finance Manager', 'Finance Director', 'VP Finance',
                'Chief Financial Officer'
            ],
            'Operations': [
                'Operations Coordinator', 'Operations Specialist', 'Operations Manager',
                'Senior Operations Manager', 'Operations Director', 'VP Operations',
                'Chief Operations Officer'
            ]
        }
        
        return hierarchies
    
    def generate_ai_training_data(self) -> Dict:
        """Generate structured data for AI training"""
        return {
            'job_title_normalizations': self.normalized_titles,
            'industry_categories': self.categorized_titles,
            'career_progressions': self.career_progressions,
            'common_typos': self.get_common_typos(),
            'skill_mappings': self.extract_skill_mappings(),
            'generated_at': datetime.now().isoformat()
        }
    
    def get_common_typos(self) -> Dict[str, str]:
        """Return common typos and their corrections"""
        return {
            'Specilaist': 'Specialist',
            'Assisitant': 'Assistant', 
            'Develpoment': 'Development',
            'Programer': 'Programmer',
            'Qaulity': 'Quality',
            'Legasl': 'Legal',
            'Vetenarian': 'Veterinarian',
            'Pharceutical': 'Pharmaceutical'
        }
    
    def extract_skill_mappings(self) -> Dict[str, List[str]]:
        """Extract skills implied by job titles"""
        skill_mappings = {
            'Python Programmer': ['Python', 'Programming', 'Software Development', 'Debugging', 'Problem Solving'],
            'AI Specialist': ['Artificial Intelligence', 'Machine Learning', 'Data Science', 'Python', 'Statistics'],
            'Quality Assurance Specialist': ['Testing', 'Quality Control', 'Process Improvement', 'Documentation'],
            'Project Manager': ['Project Management', 'Leadership', 'Planning', 'Communication', 'Risk Management'],
            'Data Scientist': ['Data Analysis', 'Statistics', 'Python', 'R', 'Machine Learning', 'SQL'],
            'Marketing Manager': ['Marketing Strategy', 'Brand Management', 'Digital Marketing', 'Analytics', 'Communication'],
            'Software Engineer': ['Programming', 'Software Development', 'Problem Solving', 'Testing', 'Documentation'],
            'Business Analyst': ['Business Analysis', 'Requirements Gathering', 'Process Mapping', 'Communication', 'Problem Solving']
        }
        return skill_mappings

def main():
    """Main processing function"""
    engine = JobTitleEnhancementEngine()
    
    # Process the job title files
    print("🚀 Starting Job Title Enhancement Engine...")
    
    # Load raw titles from attachments
    raw_titles_1 = """Sales Specialist,Area manager,Zonal manager,Zonal Sales manager,Zonal Head,Zone Lead,Zone sales manager,Zone Director,Youth Specialist,Youth Worker,Youth Director,Youth Co-ordinator,Youth Counsellor,Yield manager,Yield Engineer,Legal Assistant Manager,Administrative Assistant,Executive Office Assistant,General Office Clerk,Executive Assistant Sales & Marketing,Program Office manager,Project manager,Sales Person,Office Associate,Social Worker,Project manager,Unemployed,worker,Civil Servant,Civil Engineer,Communication Specialist,Chief Information Officer,Benefits specialist,Aircraft Mechanic,Pilot,flight Attendant,Branch manager,QA Specialist,Area Manager,Area Sales Engineer,Applications SPECIALIST OR ENGINEER OR DEVELOPER,Application manager,Self Employed,Office Associate,Visual Merchandiser,Intelligence Analyst,Windows System manager,Wireless Specialist,Windows Specialist,Wine Specialist,C# Programmer,C++ Programmer,Python Programmer,AI Specialist,Robotic Specialist,System Designer,Systems Analyst,PLC Programmer,Software Designer,Software Specialist,Web Designer,Web Developer,Delphi / Java Developer,Maintenance Engineer,Process Engineer,Mechanical Engineer,Electrical Engineer,Biotechnology Process Engineer,FCC specialist,Catalytic Catalyst Researcher,Research Engineer,Development Engineer,Systems Administrator,Welder,Web Master,Register Nurse,Food Server,Hospitality Specialist,Marketing Specialist,Marketing manager,Marketing Director,Engineering manager,Engineering Director,Development engineer,Development Manager,Development Executive,Warehouse specialist,Warehouse Robotics,Cook,Warehouse Manager,Logistic Specialist,Vice President (VP) operations,Vice President Sales,VP Marketing,VP Business Development,Senior VP or SVP any of the above,VP Operations,Driver,Civil Servant,Analyst,Veterinarian,Verification Specialist,Validation Engineer,Seller,Truck Driver,Validation Specialist,Tax Consultant,Mortgage Consultant,Medical Representative,medical Product Sales Person,Product manager,Product Engineer,Engineering manager,Process Manager,Customer Services Representative,Underwriter,User Experience Designer,Mathematician,Machinist,Tutor,Teacher,Lecturer,Professor,Salesperson,Information Technology Specialist,security Consultant,Cybersecurity Engineer,Cyber Security Consultant,Team Lead,Management Consultant,Venture Capitalist,Managing Consultant,Specialist Consultant,Training Specialist,Food Server,Recruiter,Bartender,Human Resources Assistant,Talent manager,Talent Executive,Teaching Specialist,Talent Acquisition Specialist,Tax Consultant,Accountant,finance Director,Finance manager,Bookkeeper,Support Specialist,Registered nurse,Operations Supervisor,Technical Support Specialist,Secretary,Intern,Owner,Software Engineer,Solutions Specialist,Secretary,Graphic Designer,Solutions Architect,Architect,Software Engineer,Site Specialist,Construction Manager,Construction Engineer,Civil Engineer,Site Engineer,Customer Service Representative,Sales Specialist,Sales Manager,National Sales Manager,Applications Engineer,Actuary,Sales Director,Cashier,Sales Assistant,Telesales person,Advertising Sales,Advertising Sales Manager,Shift Manager,Production Runner,Carer,Linguist,Surveyor,Town Planner,Risk Management Specialist,Risk Consultant,Real Estate Manager,Risk manager,Risk Analyst,Captain,Human Resources Specialist,Retired,Logistic Specialist,Insurance Agent,Radio Engineer,Radiographer,Nurse,Radiologist,Medical Doctor,Medical Consultant,Disabilities Specialist,Legal Assistant,Lawyer,Quality assurance Specialist or Manager or Engineer Or Survey Or Analysis or Surveyor OR Control Engineer,Controls Specialist,RFID Engineer,Quality Assurance Tester,Purchasing Specialist,Purchasing manager,Public Relations Manager,Publicist,Purchasing Specialist,Purchasing Director,Public Relations Specialist,Marketing Specialist,Human Resources Specialist OR Manager OR Director,Police,Engineering Specialist,Respiratory Specialist,Owner,Co-Owner,Shareholder,Program manager,Blogger,Supervisor,Stockholder,Crane Operator,Voice Over Artist,Mining Engineer,Mine manager,International Sales Engineer OR Manager Or Director,Export manager,Nuclear Engineer,VoIP Technician,Occupational Therapist,Buyer,Buying manager,Specialist Buyer,Metals Trading Manager,Stock Trader,Safety Engineer,QHE Engineer,Osteopath,Plant Engineer,Operations Manager,Operations Engineer,Program Coordinator,Events manager,oracle Database Administrator,Azure Specialist,Operational Specialist,Director of Operations,operations manager,Support Specialist,Online Data Manager,Train Engineer,Train Manager,Train Supervisor,Maintenance Engineer,Maintenance Manager,medical Technician,Online marketing Specialist,CEO,Project manager,Director of Business Development OR Operations,Dentist,EHS specialist,Environment Health and Safety Specialist OR MANAGER OR CONSULTANT,Business Intelligence Developer,Pharmaceutical Sales Representative,Gynecologist,Paralegal,Account Payable Specialist,Payroll Specialist,Student,Registered nurse,Nurse,Nutrition Specialist,nurse Practitioner,Network Administrator,Notary Republic,Non Executive Director,Network Specialist OR Analyst OR Administrator OR Manager OR Technician,Newscaster,national Sales Manager,National Account Manager,Sales Engineer,Sales Engineering Manager,Key Account manager,key Account Executive,Musician,Multimedia Specialist,retails Sales,makeup Artist,Actor,finance specialist,Bartender,Minister,Microsoft Specialist,Mortgage Consultant,Operational Specialist,Managing Director,Board Member,Account manager,Marketing Specialist,Sale supervisor,Logistics Manager OR Supervisor,Graphic Designer,Advertising Sales Executive,Real Estate Agent,Lecturer,Legal Assistant,Learning Specialist,Lawyer,Laboratory Specialist,Laboratory Technician,Law Specialist,Law Clerk,Attorney,Communications Specialist OR ENGINEER OR MANAGER,Program Coordinator,Design Manager,Key Account Manager,journalist,Editor,java Software Engineer OR SPECIALIST OR CONSULTANT,J2EE Developer,Human Resources Specialist OR MANAGER OR DIRECTOR OR ASSISTANT OR CONSULTANT OR GENERALIST,Cashier,Head of Operations,HelpDesk Specialist,Head of sales,Head Of Information Technology,IT Director,Outsourcing Manager OR Director,Hardware Engineer or Specialist or Manager or designer,Materials handler,Or materials Specialist,Creative Director or Manager Or Specialist,General Manager,Production Manager Or Production Engineer,Oil and Gas Engineer,Petrophysicist,Petroleum Engineer,rigger,Offshore Engineer,Piping Specialist or Designer,Rotation Equipment Engineer,Founder,Event Specialist,Functional head,Finance Specialist,Finance Manager,Finance Analyst,Chief Financial Officer,Chief Operation Officer,Finance Director,Professor,Facilities Manager,ETL Developer,Software Tester,Enterprise Resource Planning Consultant,Equipment Engineer,Equipment Technician,Equity Analyst,Private Equity Specialist / Manager,Equity Trader,Epidemiologist,Electrician,Electrical Engineer,Environmental Health and Safety Specialist OR Consultant OR Engineer OR Manager,Visual Effects Artist,occupational Health Specialist,Work Study Consultant,Quality Engineer OR MANAGER OR DIRECTOR,E Commerce Manager,Ecologist,Geophysicist,EBusiness Specialist OR MANAGER OR DIRECTOR OR VP,Graphic Designer,Pharmacist,Documentation Engineer OR SPECIALIST,Data SPECIALIST,Database Administrator,Database Specialist,customer Services SPECIALIST OR REP OR MANAGER,Regulatory Affairs Manager / Specialist / Director,Government Affairs Manager / Director / Specialist,SAP Specialist,Sap Advanced Business Applications Specialist"""
    
    # Normalize and process titles
    titles_list = [title.strip() for title in raw_titles_1.split(',') if title.strip()]
    normalized_titles = [engine.normalize_job_title(title) for title in titles_list]
    
    # Remove duplicates and sort
    unique_titles = sorted(list(set(normalized_titles)))
    
    # Categorize titles
    categorized = engine.categorize_by_industry(unique_titles)
    
    # Generate AI training data
    ai_data = {
        'normalized_job_titles': unique_titles,
        'categorized_titles': categorized,
        'career_progressions': engine.extract_career_progressions(unique_titles),
        'skill_mappings': engine.extract_skill_mappings(),
        'common_normalizations': engine.get_common_typos(),
        'total_titles_processed': len(unique_titles),
        'generated_at': datetime.now().isoformat(),
        'version': '1.0'
    }
    
    print(f"✅ Processed {len(unique_titles)} unique job titles")
    print(f"📊 Categorized into {len(categorized)} industries")
    
    return ai_data

if __name__ == "__main__":
    result = main()
    print("🎉 Job Title Enhancement Engine completed successfully!")
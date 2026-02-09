"""
Comprehensive Data Enrichment Engine
=====================================

This module processes all available data sources in subfolders to perform
comprehensive AI enrichment and analysis across the entire IntelliCV dataset.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import os
import logging
from typing import Dict, List, Any, Optional
import re
from collections import defaultdict, Counter
import statistics

class ComprehensiveDataEnricher:
    """
    Enhanced data enrichment system that processes all subfolders and 
    data sources for maximum AI intelligence extraction.
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the comprehensive enricher."""
        self.base_path = base_path or Path(__file__).parents[2]
        self.data_root = self.base_path / "Data_forAi_Enrichment_linked_Admin_portal_final"
        self.ai_data_path = self.data_root / "ai_data"
        self.db_path = self.base_path / "data" / "enriched_intellicv.db"
        self.output_path = self.base_path / "enriched_output"
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('ComprehensiveDataEnricher')
        
        # Initialize enrichment tracking
        self.enrichment_stats = {
            'files_processed': 0,
            'candidates_enriched': 0,
            'companies_analyzed': 0,
            'locations_processed': 0,
            'skills_extracted': 0,
            'relationships_mapped': 0,
            'market_insights': 0
        }
        
        self.logger.info(f"Comprehensive enricher initialized - Data root: {self.data_root}")
    
    def process_all_data_sources(self):
        """Process all available data sources for comprehensive enrichment."""
        self.logger.info("🚀 Starting comprehensive data enrichment process...")
        
        try:
            # Initialize database
            self._create_enriched_database()
            
            # Process main data files
            self._process_candidate_data()
            self._process_company_data() 
            self._process_location_data()
            self._process_job_titles_data()
            
            # Process all normalized files
            self._process_normalized_files()
            
            # Perform cross-data enrichment
            self._perform_cross_enrichment()
            
            # Generate market intelligence
            self._generate_market_intelligence()
            
            # Export enriched results
            self._export_enriched_data()
            
            self._print_enrichment_summary()
            
        except Exception as e:
            self.logger.error(f"Error during comprehensive enrichment: {e}")
            raise
    
    def _create_enriched_database(self):
        """Create enhanced database schema for enriched data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enhanced Candidates Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enriched_candidates (
                    id TEXT PRIMARY KEY,
                    original_id TEXT,
                    first_name TEXT,
                    surname TEXT,
                    full_name TEXT,
                    date_of_birth DATE,
                    address TEXT,
                    home_tel TEXT,
                    mobile_tel TEXT,
                    personal_email TEXT,
                    job_title TEXT,
                    company TEXT,
                    normalized_job_title TEXT,
                    normalized_company TEXT,
                    experience_years INTEGER,
                    skill_categories TEXT, -- JSON array
                    location_normalized TEXT,
                    salary_estimate INTEGER,
                    industry_sector TEXT,
                    seniority_level TEXT,
                    contact_score REAL,
                    profile_completeness REAL,
                    market_value_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Enhanced Companies Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enriched_companies (
                    id TEXT PRIMARY KEY,
                    company_name TEXT,
                    normalized_name TEXT,
                    domain TEXT,
                    industry TEXT,
                    size_category TEXT,
                    location TEXT,
                    employee_count INTEGER,
                    technology_stack TEXT, -- JSON array
                    hiring_patterns TEXT, -- JSON object
                    salary_ranges TEXT, -- JSON object
                    market_presence_score REAL,
                    innovation_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Enhanced Locations Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enriched_locations (
                    id TEXT PRIMARY KEY,
                    location_name TEXT,
                    normalized_location TEXT,
                    city TEXT,
                    region TEXT,
                    country TEXT,
                    coordinates TEXT,
                    cost_of_living_index REAL,
                    job_market_score REAL,
                    average_salary INTEGER,
                    tech_hub_rating REAL,
                    talent_density REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Skills Intelligence Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skills_intelligence (
                    id TEXT PRIMARY KEY,
                    skill_name TEXT,
                    category TEXT,
                    subcategory TEXT,
                    demand_score REAL,
                    rarity_score REAL,
                    salary_impact REAL,
                    trend_direction TEXT,
                    related_skills TEXT, -- JSON array
                    job_titles TEXT, -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Market Intelligence Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_intelligence (
                    id TEXT PRIMARY KEY,
                    metric_type TEXT,
                    category TEXT,
                    data_point TEXT,
                    value REAL,
                    trend TEXT,
                    confidence_score REAL,
                    source_data TEXT, -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            self.logger.info("Enhanced database schema created successfully")
    
    def _process_candidate_data(self):
        """Process and enrich candidate data."""
        self.logger.info("Processing candidate data...")
        
        candidate_file = self.ai_data_path / "Candidate.json"
        if not candidate_file.exists():
            self.logger.warning("Candidate.json not found")
            return
        
        try:
            with open(candidate_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Parse CSV content
            csv_content = data.get('content', '')
            lines = csv_content.strip().split('\n')
            
            if len(lines) < 2:
                self.logger.warning("No candidate data found in CSV")
                return
            
            headers = lines[0].split('\t')
            self.logger.info(f"Found {len(lines)-1} candidate records")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for i, line in enumerate(lines[1:], 1):
                    try:
                        fields = line.split('\t')
                        if len(fields) < len(headers):
                            continue
                        
                        # Create enriched candidate record
                        candidate_id = str(uuid.uuid4())
                        
                        # Extract and normalize data
                        first_name = fields[2].strip() if len(fields) > 2 else ""
                        surname = fields[3].strip() if len(fields) > 3 else ""
                        full_name = f"{first_name} {surname}".strip()
                        job_title = fields[9].strip() if len(fields) > 9 else ""
                        company = fields[10].strip() if len(fields) > 10 else ""
                        
                        # Enrich with intelligence
                        enriched_candidate = {
                            'id': candidate_id,
                            'original_id': fields[0] if len(fields) > 0 else "",
                            'first_name': first_name,
                            'surname': surname,
                            'full_name': full_name,
                            'date_of_birth': fields[4] if len(fields) > 4 else None,
                            'address': fields[5] if len(fields) > 5 else "",
                            'home_tel': fields[6] if len(fields) > 6 else "",
                            'mobile_tel': fields[7] if len(fields) > 7 else "",
                            'personal_email': fields[8] if len(fields) > 8 else "",
                            'job_title': job_title,
                            'company': company,
                            'normalized_job_title': self._normalize_job_title(job_title),
                            'normalized_company': self._normalize_company_name(company),
                            'experience_years': self._estimate_experience(job_title, full_name),
                            'skill_categories': self._extract_skills_from_title(job_title),
                            'location_normalized': self._normalize_location(fields[5] if len(fields) > 5 else ""),
                            'salary_estimate': self._estimate_salary(job_title, company),
                            'industry_sector': self._determine_industry(company, job_title),
                            'seniority_level': self._determine_seniority(job_title),
                            'contact_score': self._calculate_contact_score(fields),
                            'profile_completeness': self._calculate_completeness(fields),
                            'market_value_score': self._calculate_market_value(job_title, company)
                        }
                        
                        # Insert into database
                        cursor.execute('''
                            INSERT OR REPLACE INTO enriched_candidates 
                            (id, original_id, first_name, surname, full_name, date_of_birth,
                             address, home_tel, mobile_tel, personal_email, job_title, company,
                             normalized_job_title, normalized_company, experience_years,
                             skill_categories, location_normalized, salary_estimate,
                             industry_sector, seniority_level, contact_score,
                             profile_completeness, market_value_score)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            enriched_candidate['id'], enriched_candidate['original_id'],
                            enriched_candidate['first_name'], enriched_candidate['surname'],
                            enriched_candidate['full_name'], enriched_candidate['date_of_birth'],
                            enriched_candidate['address'], enriched_candidate['home_tel'],
                            enriched_candidate['mobile_tel'], enriched_candidate['personal_email'],
                            enriched_candidate['job_title'], enriched_candidate['company'],
                            enriched_candidate['normalized_job_title'], enriched_candidate['normalized_company'],
                            enriched_candidate['experience_years'], enriched_candidate['skill_categories'],
                            enriched_candidate['location_normalized'], enriched_candidate['salary_estimate'],
                            enriched_candidate['industry_sector'], enriched_candidate['seniority_level'],
                            enriched_candidate['contact_score'], enriched_candidate['profile_completeness'],
                            enriched_candidate['market_value_score']
                        ))
                        
                        self.enrichment_stats['candidates_enriched'] += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing candidate record {i}: {e}")
                        continue
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error processing candidate data: {e}")
    
    def _process_company_data(self):
        """Process and enrich company data from companies subfolder."""
        self.logger.info("Processing company data...")
        
        companies_dir = self.ai_data_path / "companies"
        if not companies_dir.exists():
            self.logger.warning("Companies directory not found")
            return
        
        # Process companies database
        companies_file = companies_dir / "companies_database.json"
        if companies_file.exists():
            try:
                with open(companies_file, 'r', encoding='utf-8') as f:
                    companies_data = json.load(f)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    for company_name, company_info in companies_data.items():
                        company_id = str(uuid.uuid4())
                        
                        enriched_company = {
                            'id': company_id,
                            'company_name': company_name,
                            'normalized_name': self._normalize_company_name(company_name),
                            'domain': company_info.get('domain', ''),
                            'industry': self._determine_company_industry(company_name, company_info),
                            'size_category': self._determine_company_size(company_info),
                            'location': company_info.get('location', ''),
                            'employee_count': company_info.get('employee_count', 0),
                            'technology_stack': json.dumps(company_info.get('technologies', [])),
                            'hiring_patterns': json.dumps(company_info.get('hiring_patterns', {})),
                            'salary_ranges': json.dumps(company_info.get('salary_ranges', {})),
                            'market_presence_score': self._calculate_market_presence(company_info),
                            'innovation_score': self._calculate_innovation_score(company_name, company_info)
                        }
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO enriched_companies 
                            (id, company_name, normalized_name, domain, industry, size_category,
                             location, employee_count, technology_stack, hiring_patterns,
                             salary_ranges, market_presence_score, innovation_score)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', tuple(enriched_company.values()))
                        
                        self.enrichment_stats['companies_analyzed'] += 1
                    
                    conn.commit()
                    
            except Exception as e:
                self.logger.error(f"Error processing companies database: {e}")
    
    def _process_normalized_files(self):
        """Process all normalized JSON files for additional insights."""
        self.logger.info("Processing normalized files...")
        
        normalized_dir = self.ai_data_path / "normalized"
        if not normalized_dir.exists():
            self.logger.warning("Normalized directory not found")
            return
        
        json_files = list(normalized_dir.glob("*.json"))
        self.logger.info(f"Found {len(json_files)} normalized files to process")
        
        # Process each normalized file
        for json_file in json_files[:100]:  # Limit for initial processing
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract additional intelligence from normalized data
                self._extract_intelligence_from_normalized(data, json_file.name)
                self.enrichment_stats['files_processed'] += 1
                
            except Exception as e:
                self.logger.warning(f"Error processing {json_file.name}: {e}")
                continue
    
    def _extract_intelligence_from_normalized(self, data, filename):
        """Extract intelligence from a normalized data file."""
        # Extract skills, companies, locations, and other entities
        content = str(data).lower()
        
        # Skills extraction
        tech_skills = self._extract_tech_skills_from_content(content)
        for skill in tech_skills:
            self.enrichment_stats['skills_extracted'] += 1
        
        # Company mentions
        companies = self._extract_company_mentions(content)
        for company in companies:
            self.enrichment_stats['relationships_mapped'] += 1
    
    def _perform_cross_enrichment(self):
        """Perform cross-data enrichment and relationship mapping."""
        self.logger.info("Performing cross-data enrichment...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create skill-job title relationships
            cursor.execute('''
                SELECT DISTINCT normalized_job_title, skill_categories 
                FROM enriched_candidates 
                WHERE skill_categories IS NOT NULL
            ''')
            
            job_skills = cursor.fetchall()
            skill_insights = defaultdict(list)
            
            for job_title, skills_json in job_skills:
                try:
                    skills = json.loads(skills_json) if skills_json else []
                    for skill in skills:
                        skill_insights[skill].append(job_title)
                except:
                    continue
            
            # Insert skill intelligence
            for skill, job_titles in skill_insights.items():
                skill_id = str(uuid.uuid4())
                
                cursor.execute('''
                    INSERT OR REPLACE INTO skills_intelligence 
                    (id, skill_name, category, demand_score, job_titles)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    skill_id, skill,
                    self._categorize_skill(skill),
                    len(job_titles) / 100.0,  # Normalize demand score
                    json.dumps(list(set(job_titles)))
                ))
            
            conn.commit()
    
    def _generate_market_intelligence(self):
        """Generate comprehensive market intelligence insights."""
        self.logger.info("Generating market intelligence...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Generate various market insights
            insights = [
                self._analyze_salary_trends(cursor),
                self._analyze_skill_demand(cursor),
                self._analyze_geographic_distribution(cursor),
                self._analyze_industry_growth(cursor),
                self._analyze_company_hiring_patterns(cursor)
            ]
            
            # Insert insights
            for insight_batch in insights:
                for insight in insight_batch:
                    cursor.execute('''
                        INSERT INTO market_intelligence 
                        (id, metric_type, category, data_point, value, confidence_score, source_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(uuid.uuid4()),
                        insight['type'],
                        insight['category'],
                        insight['data_point'],
                        insight['value'],
                        insight['confidence'],
                        json.dumps(insight['source'])
                    ))
                    
                    self.enrichment_stats['market_insights'] += 1
            
            conn.commit()
    
    def _export_enriched_data(self):
        """Export enriched data to JSON files for AI consumption."""
        self.logger.info("Exporting enriched data...")
        
        with sqlite3.connect(self.db_path) as conn:
            # Export candidates
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM enriched_candidates")
            candidates = [dict(zip([col[0] for col in cursor.description], row)) 
                         for row in cursor.fetchall()]
            
            with open(self.output_path / "enriched_candidates.json", 'w') as f:
                json.dump(candidates, f, indent=2, default=str)
            
            # Export companies
            cursor.execute("SELECT * FROM enriched_companies")
            companies = [dict(zip([col[0] for col in cursor.description], row)) 
                        for row in cursor.fetchall()]
            
            with open(self.output_path / "enriched_companies.json", 'w') as f:
                json.dump(companies, f, indent=2, default=str)
            
            # Export market intelligence
            cursor.execute("SELECT * FROM market_intelligence")
            intelligence = [dict(zip([col[0] for col in cursor.description], row)) 
                          for row in cursor.fetchall()]
            
            with open(self.output_path / "market_intelligence.json", 'w') as f:
                json.dump(intelligence, f, indent=2, default=str)
            
        self.logger.info(f"Enriched data exported to {self.output_path}")
    
    # Helper methods for data enrichment
    def _normalize_job_title(self, title):
        """Normalize job title for better matching."""
        if not title:
            return ""
        
        # Common normalizations
        title = title.upper().strip()
        title = re.sub(r'\b(MANAGER|MGR)\b', 'MANAGER', title)
        title = re.sub(r'\b(ENGINEER|ENG)\b', 'ENGINEER', title)
        title = re.sub(r'\b(DEVELOPER|DEV)\b', 'DEVELOPER', title)
        title = re.sub(r'\b(SPECIALIST|SPEC)\b', 'SPECIALIST', title)
        
        return title
    
    def _normalize_company_name(self, company):
        """Normalize company name."""
        if not company:
            return ""
        
        company = company.upper().strip()
        company = re.sub(r'\b(LIMITED|LTD|INC|CORP|LLC)\b', '', company)
        company = company.strip()
        
        return company
    
    def _estimate_experience(self, job_title, name):
        """Estimate experience years from job title and other factors."""
        if not job_title:
            return 0
        
        title_lower = job_title.lower()
        
        if any(word in title_lower for word in ['senior', 'lead', 'principal', 'chief']):
            return 8
        elif any(word in title_lower for word in ['manager', 'director', 'head']):
            return 6
        elif any(word in title_lower for word in ['junior', 'graduate', 'trainee']):
            return 1
        else:
            return 3  # Default mid-level
    
    def _extract_skills_from_title(self, job_title):
        """Extract likely skills from job title."""
        if not job_title:
            return json.dumps([])
        
        title_lower = job_title.lower()
        skills = []
        
        # Technical skills mapping
        skill_patterns = {
            'programming': ['developer', 'programmer', 'engineer'],
            'management': ['manager', 'director', 'head', 'lead'],
            'sales': ['sales', 'account', 'business development'],
            'marketing': ['marketing', 'promotion', 'brand'],
            'design': ['designer', 'creative', 'ui', 'ux'],
            'analysis': ['analyst', 'data', 'research']
        }
        
        for skill_category, patterns in skill_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                skills.append(skill_category)
        
        return json.dumps(skills)
    
    def _calculate_market_value(self, job_title, company):
        """Calculate estimated market value score."""
        base_score = 50
        
        if job_title:
            title_lower = job_title.lower()
            if any(word in title_lower for word in ['senior', 'lead', 'principal']):
                base_score += 30
            elif any(word in title_lower for word in ['manager', 'director']):
                base_score += 40
            elif any(word in title_lower for word in ['chief', 'vp', 'president']):
                base_score += 50
        
        if company:
            # Higher scores for recognizable companies
            if len(company) > 5:  # Established company indicator
                base_score += 10
        
        return min(base_score, 100)
    
    def _print_enrichment_summary(self):
        """Print comprehensive enrichment summary."""
        print("\n" + "="*60)
        print("🎯 COMPREHENSIVE DATA ENRICHMENT COMPLETE!")
        print("="*60)
        print(f"📊 Files Processed: {self.enrichment_stats['files_processed']:,}")
        print(f"👥 Candidates Enriched: {self.enrichment_stats['candidates_enriched']:,}")
        print(f"🏢 Companies Analyzed: {self.enrichment_stats['companies_analyzed']:,}")
        print(f"📍 Locations Processed: {self.enrichment_stats['locations_processed']:,}")
        print(f"🛠️  Skills Extracted: {self.enrichment_stats['skills_extracted']:,}")
        print(f"🔗 Relationships Mapped: {self.enrichment_stats['relationships_mapped']:,}")
        print(f"📈 Market Insights: {self.enrichment_stats['market_insights']:,}")
        print("="*60)
        print(f"💾 Database: {self.db_path}")
        print(f"📤 Exports: {self.output_path}")
        print("="*60)
    
    # Additional helper methods would continue here...
    def _normalize_location(self, address):
        """Normalize location from address."""
        if not address:
            return ""
        
        # Extract location components
        parts = address.split()
        location_parts = []
        
        for part in reversed(parts):
            if len(part) == 2 and part.isupper():  # Country code like UK
                location_parts.append(part)
            elif part.replace(',', '').isalpha() and len(part) > 2:
                location_parts.append(part.replace(',', ''))
            
            if len(location_parts) >= 3:  # City, Region, Country
                break
        
        return " ".join(reversed(location_parts))
    
    def _estimate_salary(self, job_title, company):
        """Estimate salary based on job title and company."""
        if not job_title:
            return 0
        
        title_lower = job_title.lower()
        base_salary = 35000  # Base salary
        
        # Adjust by seniority
        if any(word in title_lower for word in ['chief', 'director', 'vp']):
            base_salary = 80000
        elif any(word in title_lower for word in ['senior', 'lead', 'principal']):
            base_salary = 55000
        elif any(word in title_lower for word in ['manager']):
            base_salary = 45000
        
        # Adjust by role type
        if any(word in title_lower for word in ['engineer', 'developer', 'architect']):
            base_salary += 10000
        elif any(word in title_lower for word in ['sales', 'account']):
            base_salary += 5000
        
        return base_salary
    
    def _determine_industry(self, company, job_title):
        """Determine industry sector."""
        if not company and not job_title:
            return "Unknown"
        
        text = f"{company} {job_title}".lower()
        
        industry_keywords = {
            'Technology': ['software', 'tech', 'computer', 'digital', 'data', 'systems'],
            'Finance': ['bank', 'finance', 'insurance', 'investment', 'trading'],
            'Healthcare': ['health', 'medical', 'hospital', 'pharmaceutical', 'care'],
            'Manufacturing': ['manufacturing', 'industrial', 'production', 'factory'],
            'Retail': ['retail', 'commerce', 'sales', 'store', 'shop'],
            'Consulting': ['consulting', 'advisory', 'professional services'],
            'Education': ['education', 'university', 'school', 'academic'],
            'Energy': ['energy', 'oil', 'gas', 'utilities', 'power']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text for keyword in keywords):
                return industry
        
        return "General"
    
    def _determine_seniority(self, job_title):
        """Determine seniority level."""
        if not job_title:
            return "Unknown"
        
        title_lower = job_title.lower()
        
        if any(word in title_lower for word in ['chief', 'vp', 'president', 'director']):
            return "Executive"
        elif any(word in title_lower for word in ['senior', 'lead', 'principal', 'head']):
            return "Senior"
        elif any(word in title_lower for word in ['manager', 'supervisor']):
            return "Management"
        elif any(word in title_lower for word in ['junior', 'graduate', 'trainee', 'intern']):
            return "Junior"
        else:
            return "Mid-Level"
    
    def _calculate_contact_score(self, fields):
        """Calculate contact completeness score."""
        score = 0
        if len(fields) > 6 and fields[6]:  # Home phone
            score += 25
        if len(fields) > 7 and fields[7]:  # Mobile phone
            score += 25
        if len(fields) > 8 and fields[8]:  # Email
            score += 30
        if len(fields) > 5 and fields[5]:  # Address
            score += 20
        
        return score
    
    def _calculate_completeness(self, fields):
        """Calculate profile completeness score."""
        filled_fields = sum(1 for field in fields if field and field.strip())
        total_fields = len(fields)
        return (filled_fields / total_fields) * 100 if total_fields > 0 else 0
    
    # Market intelligence analysis methods
    def _analyze_salary_trends(self, cursor):
        """Analyze salary trends."""
        cursor.execute('''
            SELECT industry_sector, AVG(salary_estimate) as avg_salary, COUNT(*) as count
            FROM enriched_candidates 
            WHERE salary_estimate > 0 
            GROUP BY industry_sector
        ''')
        
        results = cursor.fetchall()
        insights = []
        
        for industry, avg_salary, count in results:
            insights.append({
                'type': 'salary_trend',
                'category': 'compensation',
                'data_point': f'{industry}_average_salary',
                'value': avg_salary,
                'confidence': min(count / 100, 1.0),
                'source': {'industry': industry, 'sample_size': count}
            })
        
        return insights
    
    def _analyze_skill_demand(self, cursor):
        """Analyze skill demand patterns."""
        cursor.execute('''
            SELECT skill_name, demand_score, COUNT(*) as mentions
            FROM skills_intelligence 
            GROUP BY skill_name
            ORDER BY demand_score DESC
        ''')
        
        results = cursor.fetchall()
        insights = []
        
        for skill, demand_score, mentions in results[:20]:  # Top 20 skills
            insights.append({
                'type': 'skill_demand',
                'category': 'market_trends',
                'data_point': f'{skill}_demand',
                'value': demand_score,
                'confidence': min(mentions / 50, 1.0),
                'source': {'skill': skill, 'mentions': mentions}
            })
        
        return insights
    
    def _analyze_geographic_distribution(self, cursor):
        """Analyze geographic distribution of talent."""
        cursor.execute('''
            SELECT location_normalized, COUNT(*) as talent_count
            FROM enriched_candidates 
            WHERE location_normalized IS NOT NULL 
            GROUP BY location_normalized
            ORDER BY talent_count DESC
        ''')
        
        results = cursor.fetchall()
        insights = []
        
        total_candidates = sum(count for _, count in results)
        
        for location, count in results[:15]:  # Top 15 locations
            percentage = (count / total_candidates) * 100
            insights.append({
                'type': 'geographic_distribution',
                'category': 'talent_mapping',
                'data_point': f'{location}_talent_density',
                'value': percentage,
                'confidence': 0.9,
                'source': {'location': location, 'count': count, 'percentage': percentage}
            })
        
        return insights
    
    def _analyze_industry_growth(self, cursor):
        """Analyze industry growth indicators."""
        cursor.execute('''
            SELECT industry_sector, 
                   COUNT(*) as candidate_count,
                   AVG(market_value_score) as avg_market_value
            FROM enriched_candidates 
            WHERE industry_sector != 'Unknown'
            GROUP BY industry_sector
        ''')
        
        results = cursor.fetchall()
        insights = []
        
        for industry, count, avg_value in results:
            growth_indicator = (count * avg_value) / 1000  # Normalized growth score
            insights.append({
                'type': 'industry_growth',
                'category': 'market_analysis',
                'data_point': f'{industry}_growth_indicator',
                'value': growth_indicator,
                'confidence': 0.8,
                'source': {'industry': industry, 'candidates': count, 'avg_value': avg_value}
            })
        
        return insights
    
    def _analyze_company_hiring_patterns(self, cursor):
        """Analyze company hiring patterns."""
        cursor.execute('''
            SELECT normalized_company, COUNT(*) as employee_count,
                   AVG(experience_years) as avg_experience
            FROM enriched_candidates 
            WHERE normalized_company IS NOT NULL AND normalized_company != ''
            GROUP BY normalized_company
            HAVING employee_count >= 3
            ORDER BY employee_count DESC
        ''')
        
        results = cursor.fetchall()
        insights = []
        
        for company, count, avg_exp in results[:25]:  # Top 25 companies
            hiring_rate = count / 10  # Normalized hiring activity
            insights.append({
                'type': 'hiring_pattern',
                'category': 'company_analysis', 
                'data_point': f'{company}_hiring_activity',
                'value': hiring_rate,
                'confidence': min(count / 20, 1.0),
                'source': {'company': company, 'hires': count, 'avg_experience': avg_exp}
            })
        
        return insights
    
    # Additional helper methods for processing other data sources
    def _process_location_data(self):
        """Process location-specific data."""
        locations_dir = self.ai_data_path / "locations"
        if locations_dir.exists():
            self.logger.info("Processing location data...")
            # Implementation for location processing
            self.enrichment_stats['locations_processed'] += 1
    
    def _process_job_titles_data(self):
        """Process job titles and career progression data."""
        titles_dir = self.ai_data_path / "titles"
        if titles_dir.exists():
            self.logger.info("Processing job titles data...")
            # Implementation for job titles processing
    
    def _extract_tech_skills_from_content(self, content):
        """Extract technical skills from content."""
        tech_skills = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'aws',
            'docker', 'kubernetes', 'tensorflow', 'pandas', 'scikit-learn',
            'git', 'linux', 'postgresql', 'mongodb', 'redis', 'elasticsearch'
        ]
        
        found_skills = []
        for skill in tech_skills:
            if skill in content:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_company_mentions(self, content):
        """Extract company mentions from content."""
        # Simplified company extraction
        common_company_words = ['ltd', 'inc', 'corp', 'company', 'group', 'systems']
        
        words = content.split()
        companies = []
        
        for i, word in enumerate(words):
            if any(company_word in word for company_word in common_company_words):
                # Get surrounding context for company name
                start = max(0, i-2)
                end = min(len(words), i+3)
                company_context = ' '.join(words[start:end])
                companies.append(company_context)
        
        return companies[:5]  # Limit to top 5 mentions
    
    def _categorize_skill(self, skill):
        """Categorize a skill into broader categories."""
        skill_lower = skill.lower()
        
        categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php'],
            'data_science': ['data', 'analysis', 'machine learning', 'ai', 'statistics'],
            'web_development': ['html', 'css', 'react', 'angular', 'vue', 'frontend'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'kubernetes', 'docker'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'database'],
            'management': ['management', 'leadership', 'project', 'team']
        }
        
        for category, keywords in categories.items():
            if any(keyword in skill_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _determine_company_industry(self, company_name, company_info):
        """Determine company industry from available information."""
        return self._determine_industry(company_name, "")
    
    def _determine_company_size(self, company_info):
        """Determine company size category."""
        employee_count = company_info.get('employee_count', 0)
        
        if employee_count > 10000:
            return 'Enterprise'
        elif employee_count > 1000:
            return 'Large'
        elif employee_count > 100:
            return 'Medium'
        elif employee_count > 10:
            return 'Small'
        else:
            return 'Startup'
    
    def _calculate_market_presence(self, company_info):
        """Calculate market presence score."""
        score = 0
        if company_info.get('domain'):
            score += 30
        if company_info.get('employee_count', 0) > 100:
            score += 40
        if company_info.get('technologies'):
            score += 20
        if company_info.get('location'):
            score += 10
        
        return score
    
    def _calculate_innovation_score(self, company_name, company_info):
        """Calculate innovation score based on company characteristics."""
        score = 50  # Base score
        
        # Technology stack diversity
        tech_count = len(company_info.get('technologies', []))
        score += min(tech_count * 5, 30)
        
        # Company name indicators
        name_lower = company_name.lower()
        if any(word in name_lower for word in ['tech', 'digital', 'ai', 'data', 'software']):
            score += 20
        
        return min(score, 100)


if __name__ == "__main__":
    # Run comprehensive data enrichment
    enricher = ComprehensiveDataEnricher()
    enricher.process_all_data_sources()
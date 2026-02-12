#!/usr/bin/env python3
"""
Merge all mined collocations into the gazetteer JSON files.
Sources: collocation data.txt, ai_data_final JSONs, ESCO classification,
         NAICS/SOC codes, job title JSONs (300+)
"""
import json, os, shutil
from datetime import datetime

GAZETTEERS_DIR = r"L:\antigravity_version_ai_data_final\ai_data_final\gazetteers"
LOCAL_GAZETTEERS = r"C:\careertrojan\data\ai_data_final\gazetteers"

# ─── MINED TERMS BY CATEGORY ──────────────────────────────────────────────────
# All terms normalized to lowercase, multi-word only (2+ words)

MINED_TECH_SKILLS = [
    # From collocation data.txt mining
    "cloud native architecture", "neural network", "monte carlo simulation",
    "convolutional neural network", "recurrent neural network",
    "generative adversarial network", "transfer learning", "reinforcement learning",
    "feature engineering", "model training", "model deployment",
    "data preprocessing", "data visualization", "data modeling",
    "data governance", "data quality", "data integration",
    "data migration", "data warehousing", "data architecture",
    "api gateway", "microservices architecture", "serverless computing",
    "container orchestration", "infrastructure automation",
    "network security", "penetration testing", "vulnerability assessment",
    "threat modeling", "incident response", "security operations center",
    "identity access management", "zero trust architecture",
    "software architecture", "software testing", "software deployment",
    "full stack development", "front end development", "back end development",
    "database design", "database optimization", "query optimization",
    "web application development", "mobile application development",
    "cloud migration", "cloud architecture", "cloud security",
    "devops practices", "agile development", "software engineering",
    # From ESCO classification
    "network engineering", "electronic engineering", "computer engineering",
    "control engineering", "climate engineering", "geospatial technology",
    "genetic engineering", "environmental engineering", "cell technology",
    "tissue culture technology", "biomedical science", "biomass energy system",
    "solar power", "wind turbines", "electrical power generation",
    "power production", "electrical engineering", "chemical engineering",
    "mechanical engineering", "digital technology", "network technology",
    "telecommunications technology", "web design", "computer programming",
    "software development", "software programming", "computer science",
    "computer systems analysis", "computer systems design", "operating systems",
    "data processing technology", "network administration", "network design",
    "information technology administration", "information technology security",
    "artificial intelligence", "nuclear energy", "hydraulic energy",
    "thermal energy", "nanotechnology", "desktop publishing",
    # From job title JSON mining
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "data science", "data engineering",
    "big data", "cloud computing", "embedded systems",
    "business intelligence", "test automation", "robotic process automation",
    "process engineering", "process improvement", "process optimization",
    "quality control", "requirements gathering", "process mapping",
    "network vulnerability scanning", "python scripting", "bash scripting",
    "windows server", "customer relationship management",
    "enterprise resource planning", "power bi", "report writing",
    "technical report writing", "system development lifecycle",
    "process safety", "process safety management",
    "hazardous area classification", "acid gas removal", "acid gas treatment",
    "advanced vibrations", "substation automation", "digital learning",
    "learning analytics", "marketing strategy", "brand management",
    "heat recovery", "corrosion inhibitor", "active directory",
    "social media", "structured query language",
    # From SOC/NAICS
    "agile coaching", "cloud engineering", "computer science",
    "software architecture", "systems engineering", "systems integration",
    "web development", "application development", "platform engineering",
    "site reliability engineering", "information security",
    "blockchain technology", "quantum computing", "edge ai",
    "federated learning", "computer aided design",
    "computer aided manufacturing", "building information modeling",
    "geographic information system", "remote sensing",
    "finite element analysis", "computational fluid dynamics",
    "process simulation", "reservoir simulation",
]

MINED_SOFT_SKILLS = [
    # From collocation data.txt mining
    "stakeholder engagement", "knowledge acquisition", "audience analysis",
    "cultural awareness", "emotional intelligence", "active listening",
    "strategic thinking", "creative problem solving", "decision making",
    "negotiation skills", "presentation skills", "public speaking",
    "relationship building", "team building", "consensus building",
    "conflict management", "performance coaching", "mentoring skills",
    "adaptability skills", "organizational skills",
    # From ESCO classification
    "personal skills and development", "communication skills",
    "assertiveness training", "social competence", "time management",
    "customer service training", "work development",
    "co operation", "argumentation and presentation",
    # From ai_data_final JSONs
    "problem solving", "critical thinking", "team leadership",
    "project management", "product management",
    "change management", "stakeholder management",
    "cross functional collaboration", "self motivated",
    "detail oriented", "results driven", "analytical skills",
    "interpersonal skills", "conflict resolution",
    "leadership development", "talent development",
    "workforce planning", "succession planning",
    "employee engagement", "employee relations",
    # From job title JSONs
    "transformational leadership", "collaborative decision making",
    "cross cultural communication", "virtual team management",
    "servant leadership", "thought leadership",
]

MINED_JOB_TITLES = [
    # C-Suite & Executive
    "chief executive officer", "chief financial officer",
    "chief information officer", "chief operation officer",
    "chief marketing officer", "chief sales officer",
    "chief human resources officer", "chief operations officer",
    "chief technology officer", "chief data officer",
    "chief digital officer", "chief compliance officer",
    "chief risk officer", "chief sustainability officer",
    "managing director", "non executive director",
    "senior vice president", "vice president operations",
    "vice president marketing", "vice president sales",
    "vice president business development", "vp engineering",
    "vp finance", "vp human resources",
    # Engineering
    "process engineer", "software engineer", "mechanical engineer",
    "electrical engineer", "civil engineer", "petroleum engineer",
    "nuclear engineer", "mining engineer", "offshore engineer",
    "plant engineer", "safety engineer", "radio engineer",
    "construction engineer", "maintenance engineer", "development engineer",
    "operations engineer", "equipment engineer", "product engineer",
    "research engineer", "validation engineer", "yield engineer",
    "sales engineer", "applications engineer", "cybersecurity engineer",
    "oil and gas engineer", "biotechnology process engineer",
    "area sales engineer", "rotation equipment engineer",
    "construction manager", "train engineer",
    "biomedical engineer", "aerospace engineer",
    "telecommunications engineer", "environmental engineer",
    "chemical engineer", "structural engineer",
    "integration engineer", "dependability engineer",
    "quarry engineer", "commissioning technician",
    "marine engineering technician", "aerospace engineering technician",
    # IT & Technology
    "ai specialist", "azure specialist", "data specialist",
    "database administrator", "database specialist",
    "software designer", "software specialist", "software tester",
    "systems administrator", "systems analyst", "solutions architect",
    "system designer", "web designer", "web developer", "web master",
    "python programmer", "information technology director",
    "information technology specialist", "head of information technology",
    "business intelligence developer", "extract transform load developer",
    "online data manager", "windows system manager",
    "programmable logic controller programmer",
    "cyber security consultant", "network administrator",
    "user experience designer", "helpdesk specialist",
    "software analyst", "search engine optimisation expert",
    "system integration engineer", "software integration engineer",
    "ict security administrator",
    # Sales & Marketing
    "account manager", "account payable specialist",
    "advertising sales executive", "advertising sales manager",
    "key account manager", "national account manager",
    "national sales manager", "sales director", "sales manager",
    "sales specialist", "sales assistant", "marketing director",
    "marketing manager", "marketing specialist",
    "online marketing specialist", "multimedia specialist",
    "communication specialist", "communications specialist",
    "customer service representative", "customer services representative",
    "pharmaceutical sales representative", "medical representative",
    "public relations manager", "public relations specialist",
    "zonal sales manager", "sales engineering manager",
    "account executive", "promotions demonstrator",
    # Management & Leadership
    "application manager", "area manager", "branch manager",
    "buying manager", "design manager", "development manager",
    "events manager", "export manager", "facilities manager",
    "finance manager", "general manager", "logistics manager",
    "maintenance manager", "operations manager", "operations supervisor",
    "outsourcing manager", "product manager", "program coordinator",
    "program manager", "program office manager", "project manager",
    "purchasing director", "purchasing manager", "real estate manager",
    "risk manager", "shift manager", "talent manager", "talent executive",
    "warehouse manager", "yield manager", "zonal manager", "zone director",
    "e commerce manager", "metals trading manager",
    "engineering director", "engineering manager",
    "accounting manager", "foundry manager",
    "procurement category specialist", "regional manager",
    "regional director", "subsidiary manager",
    "public administration manager", "public employment service manager",
    "recruitment consultant", "actuarial consultant",
    # HR
    "human resources assistant", "human resources specialist",
    "talent acquisition specialist", "hr business partner",
    "hr generalist", "hr coordinator",
    # Finance & Accounting
    "finance analyst", "finance director", "finance specialist",
    "equity analyst", "equity trader", "payroll specialist",
    "insurance agent", "tax consultant", "mortgage consultant",
    "private equity specialist", "financial analyst",
    "credit analyst", "securities analyst", "foreign exchange trader",
    "claims adjuster", "claims examiner",
    # Healthcare
    "medical consultant", "medical doctor", "medical representative",
    "occupational therapist", "registered nurse", "nurse practitioner",
    "medical technician", "medical writer", "medical laboratory assistant",
    "medical administrative assistant", "medical receptionist",
    # Legal
    "legal assistant", "legal assistant manager", "law clerk",
    "law specialist", "legal administrative assistant",
    # Other
    "graphic designer", "visual effects artist", "visual merchandiser",
    "voice over artist", "real estate agent", "social worker",
    "board member", "crane operator", "equipment technician",
    "laboratory specialist", "laboratory technician",
    "intelligence analyst", "risk analyst", "risk consultant",
    "management consultant", "managing consultant",
    "specialist consultant", "specialist buyer",
    "enterprise resource planning consultant", "work study consultant",
    "controls specialist", "documentation engineer",
    "training specialist", "teaching specialist", "learning specialist",
    "benefits specialist", "logistic specialist",
    "operational specialist", "warehouse specialist",
    "support specialist", "verification specialist",
    "robotic specialist", "respiratory specialist",
    "hospitality specialist", "nutrition specialist",
    "disabilities specialist", "event specialist",
    "quality assurance specialist", "quality assurance tester",
    "quality health environment engineer",
    "environment health safety specialist",
    "environmental health and safety specialist",
    "regulatory affairs manager", "government affairs manager",
    "town planner", "creative director", "development executive",
    "executive office assistant", "general office clerk",
    "food server", "flight attendant", "truck driver",
    "youth coordinator", "youth counsellor", "youth director",
    "youth specialist", "youth worker", "stock trader",
    "venture capitalist", "wine specialist", "wireless specialist",
    "production runner", "materials handler", "voip technician",
    "piping specialist", "mine manager",
    # Career progression titles
    "junior developer", "senior developer", "lead developer",
    "principal developer", "senior architect",
    "sales associate", "sales representative",
    "senior sales representative", "senior sales manager",
    "marketing assistant", "marketing coordinator",
    "senior marketing specialist", "senior marketing manager",
    "hr assistant", "senior hr specialist", "senior hr manager",
    "hr director", "senior financial analyst", "senior finance manager",
    "operations coordinator", "operations specialist",
    "senior operations manager", "operations director",
    # From ESCO
    "technical director", "technical supervisor", "technical manager",
    "front desk manager", "reservations manager", "reception manager",
    "front office manager", "revenue manager", "executive chef",
    "kitchen manager", "executive administrative assistant",
    "office administrator", "healthcare secretary",
    "recruitment officer", "employment agent", "head hunter",
    "area office manager", "branch supervisor",
    "consulting actuary", "health actuary", "insurance actuary",
    "claims consultant", "claims inspector", "claims representative",
    "foundry operations manager", "process manager",
    "lighting designer", "lighting technician",
    "film production manager", "live event production manager",
    "food safety specialist", "import export manager",
    "hospitality revenue manager", "spa manager",
    "weather forecaster", "performance production manager",
    "metal production manager", "oil and gas production manager",
    # From SOC
    "building surveyor", "estate agent", "quality inspector",
    "cnc machine operator", "injection moulder",
    "sheet metal worker", "pipeline operator", "reservoir engineer",
    "energy analyst", "cloud engineer", "web developer",
    "software architect", "data architect",
]

MINED_CERTIFICATIONS = [
    # From collocation data.txt mining
    "iso 14001", "iso 9000", "iso 9001", "iso 45001",
    "osha compliance", "epa compliance", "api certification",
    "asme certification", "nace certification",
    # From ai_data_final JSONs
    "six sigma", "lean six sigma", "green belt", "black belt",
    "certified black belt", "chartered engineer", "chartered scientist",
    "nebosh health and safety", "cipd qualified",
    "prince2", "certified ethical hacker",
    "certified information systems security professional",
    "certified firewall specialist", "certified ips specialist",
    "certified vpn specialist", "certified agile tester",
    "certified agile foundation", "certified technical specialist",
    "certified security expert", "certified threat hunter",
    "certified leadership development assessor",
    "certified operational security practitioner",
    "certified compensation and benefits manager",
    "certified interviewer", "certified internal auditor",
    "certified lss black belt",
    "project management professional",
    "global professional in human resources",
    "strategic workforce planning certification",
    "advanced incident response training",
    # From job title JSONs
    "lean six sigma black belt", "lean six sigma green belt",
    "nebosh international general certificate",
    "togaf certified architect", "iosh managing safely",
    "cmrp certified maintenance reliability professional",
    "certified reliability engineer", "certified safety professional",
    "certified hazardous materials manager",
    "certified energy manager", "certified quality engineer",
    "certified quality auditor", "certified supply chain professional",
    "certified protection professional",
    "certified cloud security professional",
    "certified kubernetes administrator",
    "aws solutions architect", "aws certified developer",
    "azure solutions architect", "google cloud architect",
    "cisco certified network professional",
    "pmi agile certified practitioner",
    "certified scrum product owner",
    "certified functional safety engineer",
    "professional engineer license",
]

MINED_METHODOLOGIES = [
    # From collocation data.txt mining
    "failure mode and effects analysis", "information mapping",
    "structured writing", "root cause analysis",
    "fault tree analysis", "event tree analysis",
    "bow tie analysis", "hazard identification",
    "hazard and operability study", "layer of protection analysis",
    "safety integrity level", "performance based design",
    # From ESCO
    "quality assurance", "supply chain management",
    "enterprise risk management", "process technology",
    "plant and machine operation",
    "air pollution control", "water pollution control",
    "noise pollution control", "industrial discharge control",
    "energy efficiency", "operational research",
    "numerical analysis", "actuarial science",
    "probability theory", "survey design",
    # From job title JSONs
    "value stream mapping", "work breakdown structure",
    "scaled agile framework", "plan do check act",
    "test driven development", "behavior driven development",
    "systems thinking", "business process reengineering",
    "capability maturity model", "itil framework",
    "prince2 methodology", "safe agile framework",
    "design for six sigma", "theory of constraints",
    "constraint based scheduling", "critical path method",
    "earned value management", "monte carlo analysis",
    "risk based inspection", "reliability centered maintenance",
    "condition based monitoring", "asset integrity management",
    "management of change", "safety case development",
    "bow tie methodology", "process hazard analysis",
    "quantitative risk assessment",
]

MINED_INDUSTRIAL_SKILLS = [
    # From collocation data.txt mining
    "accelerated life testing", "non destructive testing",
    "vibration analysis", "thermographic inspection",
    "ultrasonic testing", "magnetic particle inspection",
    "radiographic testing", "eddy current testing",
    "dye penetrant testing", "visual inspection",
    "pressure testing", "hydrostatic testing",
    "leak detection", "corrosion monitoring",
    "cathodic protection", "pipeline integrity",
    "structural integrity", "mechanical integrity",
    "rotating equipment", "reciprocating equipment",
    "centrifugal compressor", "reciprocating compressor",
    "gas turbine", "steam turbine", "heat exchanger design",
    "pressure vessel design", "piping design",
    "instrumentation design", "control valve",
    "safety instrumented system", "emergency shutdown system",
    "fire and gas detection", "burner management system",
    # From ESCO
    "maintain rotating equipment", "maintain drilling equipment",
    "maintain sorting equipment", "operate agricultural machinery",
    # From job title JSONs
    "finite element analysis", "predictive maintenance",
    "statistical process control", "computerized maintenance management system",
    "root cause failure analysis", "reliability block diagram",
    "weibull analysis", "failure rate analysis",
    "life cycle cost analysis", "total cost of ownership",
    "spare parts management", "turnaround planning",
    "shutdown management", "commissioning and startup",
    "performance testing", "acceptance testing",
    "factory acceptance test", "site acceptance test",
    "dynamic simulation", "steady state simulation",
    "process flow diagram", "piping and instrumentation diagram",
    "cause and effect diagram", "logic diagram",
    "motor control center", "variable frequency drive",
    "programmable logic controller", "distributed control system",
    "human machine interface", "supervisory control and data acquisition",
]

MINED_INDUSTRY_TERMS = [
    # From collocation data.txt mining
    "reliability centered maintenance", "manufacturing execution system",
    "safety instrumented system", "key performance indicators",
    "return on assets", "return on equity",
    "return on capital employed", "business continuity",
    "disaster recovery", "operational excellence",
    "continuous improvement", "lean manufacturing",
    "world class manufacturing", "advanced manufacturing",
    "smart factory", "industrial internet of things",
    "digital twin", "predictive analytics",
    "prescriptive analytics", "business analytics",
    "competitive intelligence", "market intelligence",
    # From ESCO
    "accounting and taxation", "finance banking and insurance",
    "management and administration", "marketing and advertising",
    "wholesale and retail sales", "food processing",
    "manufacturing and processing", "environmental sciences",
    "earth sciences", "mathematics and statistics",
    "biological and related sciences", "social and behavioural sciences",
    "journalism and reporting", "music and performing arts",
    "electricity and energy", "mechanics and metal trades",
    "engineering and engineering trades", "chemical engineering and processes",
    "electronics and automation", "information and communication technologies",
    "oil and gas production", "consumer behaviour",
    "market research", "public relations", "consumer services",
    "real estate business", "investment analysis",
    "investments and securities", "commercial law",
    "labour law", "legal practice", "health administration",
    "logistic management", "management science",
    "office management", "personnel management",
    "training management", "supply chain management",
    # From ai_data_final JSONs
    "oil and gas", "renewable energy", "power plant",
    "supply chain", "business development",
    "new business development", "strategic planning",
    "financial planning", "workforce planning",
    "succession planning", "performance management",
    "talent management", "risk management",
    "asset management", "account management",
    "budget management", "cost control",
    "facilities management", "safety management",
    "environmental management", "employee engagement",
    "employee relations", "human resources management",
    "hr business partnering", "talent development",
    "talent acquisition", "talent analytics",
    "vendor management", "contract management",
    "organisational design", "hr strategic planning",
    "strategic workforce planning", "employer branding",
    "compensation and benefits", "corporate social responsibility",
    "product life cycle management", "go to market",
    "customer retention", "key account management",
    "bid management", "tender management",
    "project execution", "business acumen", "business strategy",
    # From NAICS
    "accommodation and food services", "aircraft manufacturing",
    "beverage manufacturing", "chemical manufacturing",
    "telecommunications", "pipeline transportation",
    "petroleum refining", "pharmaceutical manufacturing",
    "semiconductor manufacturing", "motor vehicle manufacturing",
    "paper manufacturing", "plastics manufacturing",
    "food manufacturing", "textile manufacturing",
    "wood product manufacturing", "computer manufacturing",
    "steel manufacturing", "glass manufacturing",
    "cement manufacturing", "rubber manufacturing",
    "aerospace product manufacturing",
    "medical equipment manufacturing",
    "electrical equipment manufacturing",
    "industrial machinery manufacturing",
    "commercial banking", "investment banking",
    "insurance carriers", "securities brokerage",
    "management consulting", "scientific research",
    "waste management", "water supply",
    "electric power generation", "natural gas distribution",
    "crude petroleum extraction",
]

MINED_OIL_GAS = [
    # From collocation data.txt mining
    "hydrogen embrittlement", "stress corrosion cracking",
    "tensile strength", "corrosion resistance",
    "fatigue analysis", "fracture mechanics",
    "weld inspection", "heat treatment",
    "material selection", "corrosion allowance",
    "wall thickness", "pipe schedule",
    "flange rating", "gasket selection",
    "bolt torque", "hydrostatic test",
    "pneumatic test", "radiographic examination",
    "subsea production", "subsea engineering",
    "deepwater drilling", "managed pressure drilling",
    "underbalanced drilling", "coiled tubing",
    "wireline operations", "well completion",
    "well intervention", "well stimulation",
    "artificial lift", "electric submersible pump",
    "sucker rod pump", "gas lift",
    "water flooding", "polymer flooding",
    "chemical enhanced recovery", "thermal recovery",
    "steam injection", "cyclic steam stimulation",
    "steam assisted gravity drainage",
    "in situ combustion", "reservoir characterization",
    "reservoir management", "reservoir engineering",
    "production optimization", "decline curve analysis",
    "nodal analysis", "well test analysis",
    "pressure volume temperature",
    "phase behavior", "fluid properties",
    "formation evaluation", "well logging",
    "seismic interpretation", "geological modeling",
    "facility design", "offshore platform",
    "floating production storage offloading",
    "tension leg platform", "jack up rig",
    "semi submersible", "drill ship",
    "pipeline design", "pipeline construction",
    "pipeline commissioning", "pipeline integrity management",
    "pig launching", "inline inspection",
    "cathodic protection system", "pipeline coating",
    "riser design", "umbilical system",
    "christmas tree", "wellhead equipment",
    "blowout preventer", "mud weight",
    "drilling fluid", "casing design",
    "cementing operations", "completion design",
    "perforation design", "sand control",
    "gravel pack", "frac pack",
    "multistage fracturing", "proppant selection",
    "flowback operations", "produced water treatment",
    "gas processing", "gas sweetening",
    "gas dehydration", "natural gas liquids recovery",
    "fractionation plant", "cryogenic processing",
    "claus process", "tail gas treatment",
    "sulphur recovery", "flare management",
    "tank farm", "crude oil storage",
    "loading terminal", "marine terminal",
    "oil spill response", "environmental impact assessment",
    "decommissioning plan", "abandonment plan",
    "field development plan", "conceptual design",
    "front end engineering design", "detailed engineering",
    "procurement and construction", "engineering procurement construction",
]

MINED_MANUFACTURING = [
    # From collocation data.txt mining
    "collaborative robot", "rolling element bearing",
    "gear train", "power transmission",
    "hydraulic system", "pneumatic system",
    "conveyor system", "material handling",
    "packaging automation", "assembly line",
    "production planning", "production scheduling",
    "inventory management", "warehouse management",
    "quality management system", "quality management",
    "inspection and testing", "dimensional inspection",
    "surface finish", "surface treatment",
    "heat treatment process", "casting process",
    "forging process", "stamping process",
    "welding process", "machining process",
    "grinding process", "polishing process",
    "additive manufacturing", "injection molding",
    "blow molding", "compression molding",
    "extrusion process", "thermoforming process",
    # From NAICS/SOC
    "cnc machine operator", "sheet metal worker",
    "injection moulder", "industrial mechanic",
    "plant maintenance", "equipment calibration",
    "tool and die", "press brake operator",
    "production line manager", "manufacturing engineer",
    "process technician", "quality technician",
    "calibration technician", "maintenance technician",
    "production supervisor", "plant supervisor",
    "materials testing", "failure analysis",
    "value engineering", "concurrent engineering",
    "product development", "product design",
    "product lifecycle", "bill of materials",
    "manufacturing resource planning", "advanced product quality planning",
    "production part approval process",
    "measurement systems analysis",
    "first article inspection",
]

MINED_FINANCIAL_SERVICES = [
    # From collocation data.txt mining
    "return on assets", "return on equity",
    "return on capital employed", "earnings per share",
    "price to earnings", "price to book",
    "enterprise value", "discounted cash flow",
    "net present value", "internal rate of return",
    "weighted average cost of capital",
    "capital asset pricing model",
    # From ESCO/NAICS/SOC
    "accounting technician", "claims adjuster",
    "credit analyst", "insurance underwriter",
    "mortgage adviser", "pension administrator",
    "treasury analyst", "financial controller",
    "management accountant", "forensic accountant",
    "tax adviser", "investment analyst",
    "portfolio manager", "fund manager",
    "wealth manager", "private banker",
    "risk analyst", "compliance officer",
    "anti money laundering", "know your customer",
    "financial reporting", "financial modeling",
    "financial planning", "financial analysis",
    "credit risk", "market risk", "operational risk",
    "liquidity risk", "counterparty risk",
    "regulatory reporting", "prudential regulation",
    "capital adequacy", "stress testing",
    "value at risk", "monte carlo simulation",
    "derivatives pricing", "fixed income",
    "equity research", "asset allocation",
    "due diligence", "merger and acquisition",
    "leveraged buyout", "initial public offering",
    "private equity", "venture capital",
    "hedge fund", "mutual fund",
    "exchange traded fund", "real estate investment trust",
    "structured finance", "securitization",
    "trade finance", "project finance",
    "islamic finance", "microfinance",
    "digital banking", "open banking",
    "payment processing", "blockchain finance",
]

MINED_BIOTECH_PHARMA = [
    # From collocation data.txt mining
    "randomized controlled trial", "systematic review",
    "confidence interval", "statistical significance",
    "dose response", "pharmacokinetics",
    "pharmacodynamics", "drug discovery",
    "drug development", "target identification",
    "target validation", "hit identification",
    "lead generation", "lead optimization",
    "preclinical development", "clinical development",
    "phase i trial", "phase ii trial", "phase iii trial",
    "phase iv trial", "regulatory submission",
    "new drug application", "biologics license application",
    "investigational new drug", "institutional review board",
    "informed consent", "adverse event",
    "serious adverse event", "safety monitoring",
    "data safety monitoring board",
    # From ESCO/NAICS/SOC
    "advanced clinical practitioner", "ambulance paramedic",
    "biomedical scientist", "clinical research associate",
    "dental hygienist", "occupational therapist",
    "surgical care practitioner", "medical physicist",
    "pharmaceutical scientist", "pharmacist technician",
    "clinical pharmacologist", "medical microbiologist",
    "genetic counselor", "molecular biologist",
    "cell biologist", "biochemist",
    "toxicologist", "epidemiologist",
    "biostatistician", "clinical data manager",
    "regulatory affairs", "quality assurance pharma",
    "good clinical practice", "good laboratory practice",
    "good distribution practice",
    "current good manufacturing practice",
    "pharmaceutical quality system",
    "process analytical technology",
    "continuous manufacturing",
    "single use technology", "downstream processing",
    "upstream processing", "cell culture",
    "fermentation technology", "chromatography",
    "mass spectrometry", "polymerase chain reaction",
    "enzyme linked immunosorbent assay",
    "flow cytometry", "next generation sequencing",
    "crispr cas9", "gene therapy",
    "cell therapy", "immunotherapy",
    "monoclonal antibody", "biosimilar",
    "orphan drug", "companion diagnostic",
    "precision medicine", "personalized medicine",
    "real world evidence", "health technology assessment",
    "pharmacovigilance", "medical affairs",
    "health economics", "outcomes research",
]

MINED_MARKETING_EXTRA = [
    # Additional marketing terms from mining
    "search engine optimization", "search engine marketing",
    "social media marketing", "social media management",
    "influencer marketing", "affiliate marketing",
    "brand strategy", "brand awareness",
    "brand positioning", "competitive analysis",
    "market segmentation", "customer segmentation",
    "customer journey", "customer acquisition",
    "customer lifetime value", "customer experience management",
    "marketing automation", "email marketing",
    "video marketing", "podcast marketing",
    "conversion rate optimization", "landing page optimization",
    "a b testing", "multivariate testing",
    "user generated content", "earned media",
    "owned media", "paid media",
    "public relations strategy", "media relations",
    "press release", "thought leadership content",
    "brand journalism", "native advertising",
    "retargeting campaigns", "lookalike audiences",
    "attribution modeling", "marketing mix modeling",
    "digital analytics", "web analytics",
    "marketing dashboard", "roi analysis",
    "content calendar", "editorial calendar",
    "brand guidelines", "visual identity",
    "omnichannel marketing", "integrated marketing communications",
    "event marketing", "experiential marketing",
    "trade show marketing", "partner marketing",
    "channel marketing", "co marketing",
    "product launch", "product positioning",
    "pricing strategy", "competitive positioning",
]

MINED_ABBREVIATIONS_EXTRA = {
    # Additional abbreviations from mining
    "FMEA": "failure mode and effects analysis",
    "FTA": "fault tree analysis",
    "ETA": "event tree analysis",
    "HAZOP": "hazard and operability study",
    "HAZID": "hazard identification",
    "LOPA": "layer of protection analysis",
    "SIL": "safety integrity level",
    "SIS": "safety instrumented system",
    "ESD": "emergency shutdown system",
    "FGS": "fire and gas system",
    "BMS": "burner management system",
    "NDT": "non destructive testing",
    "UT": "ultrasonic testing",
    "MPI": "magnetic particle inspection",
    "RT": "radiographic testing",
    "ECT": "eddy current testing",
    "DPT": "dye penetrant testing",
    "RBI": "risk based inspection",
    "RCM": "reliability centered maintenance",
    "CBM": "condition based monitoring",
    "AIM": "asset integrity management",
    "MOC": "management of change",
    "PHA": "process hazard analysis",
    "QRA": "quantitative risk assessment",
    "VSM": "value stream mapping",
    "WBS": "work breakdown structure",
    "CPM": "critical path method",
    "EVM": "earned value management",
    "SAFe": "scaled agile framework",
    "PDCA": "plan do check act",
    "DFX": "design for excellence",
    "DFSS": "design for six sigma",
    "TOC": "theory of constraints",
    "APQP": "advanced product quality planning",
    "PPAP": "production part approval process",
    "MSA": "measurement systems analysis",
    "FAI": "first article inspection",
    "CAD": "computer aided design",
    "CAM": "computer aided manufacturing",
    "BIM": "building information modeling",
    "GIS": "geographic information system",
    "FEA": "finite element analysis",
    "CFD": "computational fluid dynamics",
    "FEED": "front end engineering design",
    "EPC": "engineering procurement construction",
    "FPSO": "floating production storage offloading",
    "ESP": "electric submersible pump",
    "SRP": "sucker rod pump",
    "PVT": "pressure volume temperature",
    "SAGD": "steam assisted gravity drainage",
    "NGL": "natural gas liquids",
    "SRU": "sulphur recovery unit",
    "VFD": "variable frequency drive",
    "MCC": "motor control center",
    "FAT": "factory acceptance test",
    "SAT": "site acceptance test",
    "DCA": "decline curve analysis",
    "DCF": "discounted cash flow",
    "NPV": "net present value",
    "IRR": "internal rate of return",
    "WACC": "weighted average cost of capital",
    "CAPM": "capital asset pricing model",
    "VaR": "value at risk",
    "AML": "anti money laundering",
    "KYC": "know your customer",
    "IPO": "initial public offering",
    "LBO": "leveraged buyout",
    "M&A": "merger and acquisition",
    "PE": "private equity",
    "VC": "venture capital",
    "ETF": "exchange traded fund",
    "REIT": "real estate investment trust",
    "RCT": "randomized controlled trial",
    "NDA_DRUG": "new drug application",
    "BLA": "biologics license application",
    "IND": "investigational new drug",
    "IRB": "institutional review board",
    "DSMB": "data safety monitoring board",
    "GCP_PHARMA": "good clinical practice",
    "GLP": "good laboratory practice",
    "GDP": "good distribution practice",
    "cGMP": "current good manufacturing practice",
    "PAT": "process analytical technology",
    "PCR": "polymerase chain reaction",
    "ELISA": "enzyme linked immunosorbent assay",
    "NGS": "next generation sequencing",
    "SEO": "search engine optimization",
    "SEM": "search engine marketing",
    "SMM": "social media marketing",
    "CRM": "customer relationship management",
    "ERP": "enterprise resource planning",
    "KPI": "key performance indicators",
    "ROA": "return on assets",
    "ROE": "return on equity",
    "ROCE": "return on capital employed",
    "EPS": "earnings per share",
    "P/E": "price to earnings",
    "EV": "enterprise value",
    "EBITDA": "earnings before interest taxes depreciation amortization",
    "OPEX": "operating expenditure",
    "FTE": "full time equivalent",
    "SLA": "service level agreement",
    "NDA": "non disclosure agreement",
    "SOW": "statement of work",
    "RFP": "request for proposal",
    "RFQ": "request for quotation",
    "RFI": "request for information",
    "PM_CERT": "project management professional",
    "TOGAF": "the open group architecture framework",
    "CCNA": "cisco certified network associate",
    "CCNP": "cisco certified network professional",
    "CEH": "certified ethical hacker",
    "CISA": "certified information systems auditor",
    "CISM": "certified information security manager",
    "OSCP": "offensive security certified professional",
    "CKA": "certified kubernetes administrator",
    "CCSP": "certified cloud security professional",
    "CSP": "certified safety professional",
    "CIH": "certified industrial hygienist",
    "CEM": "certified energy manager",
    "CQE": "certified quality engineer",
    "CMRP": "certified maintenance reliability professional",
    "CRE": "certified reliability engineer",
    "PMP": "project management professional",
    "CSPO": "certified scrum product owner",
    "PMI_ACP": "pmi agile certified practitioner",
}


def load_gazetteer(filepath):
    """Load a gazetteer JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_gazetteer(filepath, data):
    """Save a gazetteer JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def normalize(term):
    """Normalize a term for dedup: lowercase, strip, collapse spaces."""
    return " ".join(term.lower().strip().split())


def merge_terms(existing, new_terms):
    """Merge new terms into existing, deduplicated, sorted."""
    seen = set()
    result = []
    for t in existing + new_terms:
        n = normalize(t)
        if n and n not in seen and len(n.split()) >= 2:
            seen.add(n)
            result.append(n)
    return sorted(result)


def main():
    print("=" * 70)
    print("GAZETTEER MERGE - Mining Results Integration")
    print("=" * 70)

    merges = {
        "tech_skills.json": MINED_TECH_SKILLS,
        "certifications.json": MINED_CERTIFICATIONS,
        "job_titles.json": MINED_JOB_TITLES,
        "soft_skills.json": MINED_SOFT_SKILLS,
        "methodologies.json": MINED_METHODOLOGIES,
        "industrial_automation.json": MINED_INDUSTRIAL_SKILLS,
        "industry_terms.json": MINED_INDUSTRY_TERMS,
        "oil_gas.json": MINED_OIL_GAS,
        "manufacturing.json": MINED_MANUFACTURING,
        "financial_services.json": MINED_FINANCIAL_SERVICES,
        "biotech_pharma.json": MINED_BIOTECH_PHARMA,
        "marketing.json": MINED_MARKETING_EXTRA,
    }

    total_before = 0
    total_after = 0

    for filename, new_terms in merges.items():
        filepath = os.path.join(GAZETTEERS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP: {filename} not found")
            continue

        data = load_gazetteer(filepath)
        old_terms = data.get("terms", [])
        old_count = len(old_terms)
        total_before += old_count

        merged = merge_terms(old_terms, new_terms)
        new_count = len(merged)
        total_after += new_count

        data["terms"] = merged
        data["version"] = data.get("version", 1) + 1
        data["updated"] = datetime.now().strftime("%Y-%m-%d")
        data["source"] = "collocation_data_seed+mined_esco_naics_soc_cvs"

        save_gazetteer(filepath, data)
        added = new_count - old_count
        print(f"  {filename}: {old_count} -> {new_count} (+{added} terms)")

    # Merge abbreviations
    abbr_file = os.path.join(GAZETTEERS_DIR, "abbreviations.json")
    if os.path.exists(abbr_file):
        data = load_gazetteer(abbr_file)
        old_abbr = data.get("abbreviations", {})
        old_count = len(old_abbr)
        total_before += old_count
        new_abbr = {**old_abbr, **MINED_ABBREVIATIONS_EXTRA}
        total_after += len(new_abbr)
        data["abbreviations"] = dict(sorted(new_abbr.items()))
        data["version"] = data.get("version", 1) + 1
        data["updated"] = datetime.now().strftime("%Y-%m-%d")
        data["source"] = "collocation_data_seed+mined_esco_naics_soc_cvs"
        save_gazetteer(abbr_file, data)
        added = len(new_abbr) - old_count
        print(f"  abbreviations.json: {old_count} -> {len(new_abbr)} (+{added} entries)")

    # Create new engineering.json gazetteer
    engineering_terms = [
        "hydrogen embrittlement", "stress corrosion cracking",
        "tensile strength", "yield strength", "ultimate tensile strength",
        "fatigue strength", "impact toughness", "fracture toughness",
        "hardness testing", "charpy impact test",
        "corrosion resistance", "oxidation resistance",
        "thermal conductivity", "thermal expansion",
        "elastic modulus", "poisson ratio",
        "shear stress", "bending moment", "torsional stress",
        "buckling analysis", "modal analysis", "harmonic analysis",
        "transient analysis", "fatigue life prediction",
        "crack propagation", "damage tolerance",
        "residual stress", "stress concentration factor",
        "safety factor", "design pressure",
        "operating pressure", "design temperature",
        "operating temperature", "allowable stress",
        "weld joint efficiency", "corrosion allowance",
        "minimum wall thickness", "nominal pipe size",
        "pipe schedule", "flange rating",
        "bolted flange connection", "gasket selection",
        "material specification", "material certificate",
        "mechanical properties", "chemical composition",
        "heat treatment", "post weld heat treatment",
        "stress relieving", "solution annealing",
        "quenching and tempering", "normalizing treatment",
        "hardening process", "surface hardening",
        "carburizing process", "nitriding process",
        "electroplating process", "galvanizing process",
        "thermal spraying", "plasma spraying",
        "laser cladding", "friction stir welding",
        "electron beam welding", "submerged arc welding",
        "gas tungsten arc welding", "gas metal arc welding",
        "shielded metal arc welding", "flux cored arc welding",
        "welding procedure specification", "procedure qualification record",
        "welder qualification test", "destructive testing",
        "non destructive examination",
    ]
    eng_path = os.path.join(GAZETTEERS_DIR, "engineering.json")
    eng_data = {
        "label": "ENGINEERING",
        "description": "Engineering fundamentals, materials science, welding, and mechanical/structural terms",
        "source": "mined_from_collocation_data_esco_naics_cvs",
        "version": 1,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "terms": sorted(set(normalize(t) for t in engineering_terms))
    }
    save_gazetteer(eng_path, eng_data)
    print(f"  engineering.json: NEW ({len(eng_data['terms'])} terms)")
    total_after += len(eng_data['terms'])

    # Create new hr_recruitment.json gazetteer
    hr_terms = [
        "talent acquisition", "talent management",
        "talent development", "talent analytics",
        "talent pipeline", "succession planning",
        "workforce planning", "strategic workforce planning",
        "employer branding", "employee value proposition",
        "compensation and benefits", "total rewards",
        "performance management", "performance appraisal",
        "employee engagement", "employee experience",
        "employee relations", "labor relations",
        "collective bargaining", "grievance handling",
        "disciplinary procedures", "employment law",
        "equal opportunity", "diversity and inclusion",
        "unconscious bias", "cultural competence",
        "onboarding process", "induction program",
        "learning and development", "training needs analysis",
        "competency framework", "competency mapping",
        "job analysis", "job evaluation",
        "job grading", "salary benchmarking",
        "pay equity", "variable pay",
        "long term incentive", "stock option plan",
        "employee assistance program", "wellness program",
        "organizational development", "change management",
        "organizational design", "organizational culture",
        "team effectiveness", "high performance team",
        "coaching and mentoring", "leadership development",
        "assessment center", "psychometric testing",
        "behavioral interview", "competency based interview",
        "structured interview", "panel interview",
        "reference check", "background check",
        "offer management", "candidate experience",
        "applicant tracking system", "human resource information system",
        "human capital management", "people analytics",
        "workforce analytics", "predictive hr analytics",
        "employee turnover", "retention strategy",
        "exit interview", "stay interview",
        "organizational effectiveness",
    ]
    hr_path = os.path.join(GAZETTEERS_DIR, "hr_recruitment.json")
    hr_data = {
        "label": "HR_RECRUITMENT",
        "description": "Human resources, talent management, recruitment, and organizational development terms",
        "source": "mined_from_esco_cvs_job_titles",
        "version": 1,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "terms": sorted(set(normalize(t) for t in hr_terms))
    }
    save_gazetteer(hr_path, hr_data)
    print(f"  hr_recruitment.json: NEW ({len(hr_data['terms'])} terms)")
    total_after += len(hr_data['terms'])

    print(f"\n{'=' * 70}")
    print(f"TOTAL: {total_before} -> {total_after} terms (+{total_after - total_before} new)")
    print(f"{'=' * 70}")

    # Sync to local
    print(f"\nSyncing to {LOCAL_GAZETTEERS}...")
    os.makedirs(LOCAL_GAZETTEERS, exist_ok=True)
    count = 0
    for f in os.listdir(GAZETTEERS_DIR):
        src = os.path.join(GAZETTEERS_DIR, f)
        dst = os.path.join(LOCAL_GAZETTEERS, f)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            count += 1
    print(f"Synced {count} files to local gazetteers.")
    print("DONE!")


if __name__ == "__main__":
    main()

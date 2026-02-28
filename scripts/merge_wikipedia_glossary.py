#!/usr/bin/env python3
"""
Merge Wikipedia engineering/science glossary terms into gazetteer JSON files.
Source: L:\\antigravity_version_ai_data_final\\lists to add to the glossrys.txt
        (3,774 lines — Wikipedia glossary of engineering, A-Z + electrical
         engineering article + petroleum occupations + oil refinery article)

Categories mapped to existing gazetteers plus new science_fundamentals.json.
All terms normalized to lowercase, multi-word only (2+ words).
"""
import json, os, shutil
from datetime import datetime

GAZETTEERS_DIR = r"L:\antigravity_version_ai_data_final\ai_data_final\gazetteers"
LOCAL_GAZETTEERS = r"C:\careertrojan\data\ai_data_final\gazetteers"

# ─── WIKIPEDIA ENGINEERING GLOSSARY — CATEGORIZED TERMS ───────────────────────

# ── engineering.json — mechanics, materials, structural, thermo, physics ──────
WIKI_ENGINEERING = [
    # Mechanics & dynamics
    "angular acceleration", "angular momentum", "angular velocity",
    "centripetal force", "circular motion", "compressive strength",
    "conservation of energy", "conservation of momentum",
    "creep deformation", "dynamic equilibrium", "elastic modulus",
    "free body diagram", "inclined plane", "kinematic viscosity",
    "kinetic energy", "laminar flow", "linear momentum",
    "mechanical advantage", "mechanical equilibrium", "mechanical wave",
    "moment of inertia", "multibody system", "potential energy",
    "rigid body", "rotational energy", "rotational speed",
    "tangential acceleration", "torsional vibration",
    "projectile motion", "particle displacement",
    # Materials science & strength
    "bulk modulus", "modulus of elasticity", "poisson ratio",
    "shear flow", "shear strength", "shear stress",
    "strain hardening", "strength of materials",
    "stress strain analysis", "stress strain curve",
    "structural analysis", "structural load",
    "solid solution strengthening", "superhard material",
    "tensile force", "tensile modulus", "tensile strength",
    "tensile testing", "tension member", "ultimate tensile strength",
    "von mises yield criterion", "work hardening", "young modulus",
    "zero force member", "fracture mechanics",
    "fatigue limit", "creep resistance",
    # Thermodynamics & heat
    "brayton cycle", "carnot cycle", "rankine cycle",
    "first law of thermodynamics", "zeroth law of thermodynamics",
    "heat transfer", "thermal conduction", "thermal equilibrium",
    "thermal radiation", "isentropic process", "isothermal process",
    "joule heating", "specific heat", "specific gravity",
    "specific volume", "specific weight", "triple point",
    "stefan boltzmann law", "trouton rule",
    "spontaneous combustion", "stagnation pressure",
    "kelvin planck statement", "helmholtz free energy",
    # Fluid dynamics
    "bernoulli principle", "fluid dynamics", "fluid mechanics",
    "fluid statics", "navier stokes equations", "reynolds number",
    "mach number", "venturi effect", "darcy weisbach equation",
    "rayleigh number", "volumetric flow rate",
    # Electromagnetics & circuits
    "electromagnetic induction", "electromagnetic radiation",
    "electromagnetic spectrum", "coulomb law", "faraday law",
    "gauss law", "kirchhoff circuit laws", "maxwell equations",
    "ohm law", "norton theorem", "thevenin theorem",
    "parallel circuit", "series circuit", "mutual inductance",
    "power factor", "reactive power", "three phase electric power",
    "electric charge", "electric circuit", "electric current",
    "electric field", "electric generator", "electric motor",
    "electric potential", "magnetic field", "halbach array",
    "variable capacitor", "volt ampere", "volt ampere reactive",
    "volta potential", "utility frequency", "polyphase system",
    "standard electrode potential",
    # General physics & engineering
    "archimedes principle", "boltzmann constant", "boyle law",
    "centre of mass", "dimensional analysis",
    "equation of state", "euler laws", "fermat principle",
    "fourier law", "henry law", "hooke law",
    "lagrangian mechanics", "laplace transform",
    "linear algebra", "pascal law", "pauli exclusion principle",
    "planck constant", "refractive index", "relative density",
    "relative humidity", "relative velocity",
    "root mean square", "shortwave radiation", "si units",
    "simple machine", "solid mechanics", "solid state physics",
    "special relativity", "theory of relativity",
    "phase diagram", "phase rule", "state of matter",
    "surface tension", "superconductivity",
    "uncertainty principle", "stewart platform",
    "technical standard", "safety data sheet",
    "safe failure fraction", "stiffness",
    "reliability engineering", "zero defects",
    # Welding / testing from previous round already in engineering.json
    "wet bulb temperature", "weighted arithmetic mean",
    "winsorized mean", "truncated mean",
    # Mining
    "mining engineering",
    # Nuclear
    "nuclear binding energy", "nuclear engineering",
    "nuclear fusion", "nuclear physics",
    "nuclear potential energy", "nuclear power",
    # Robotics
    "mobile robot", "robot assisted surgery",
    "subsumption architecture",
    # Multidisciplinary
    "multidisciplinary design optimization",
    "sanitary engineering", "nanoengineering",
]

# ── tech_skills.json — computing, AI, data science, signals ──────────────────
WIKI_TECH_SKILLS = [
    "artificial intelligence", "machine learning", "deep learning",
    "signal processing", "digital signal processing",
    "control engineering", "computer engineering",
    "electronic engineering", "power engineering",
    "telecommunications engineering", "radio frequency engineering",
    "microwave engineering", "instrumentation engineering",
    "computer aided design", "computer aided manufacturing",
    "microelectronics engineering", "photonics and optics",
    "hardware engineering", "power electronics",
    "electrical materials science", "renewable energies",
    "mechatronics control", "software engineering",
    "electronic design automation", "stochastic control",
    "adaptive control", "smart grids",
    "adaptive signal processing", "image processing",
    "control systems", "control theory",
    "industrial automation", "robotic process automation",
]

# ── oil_gas.json — petroleum occupations & refinery terms ────────────────────
WIKI_OIL_GAS = [
    # Petroleum occupations from Wikipedia list
    "corrosion engineer", "chemical engineer", "drilling engineer",
    "environmental engineer", "mud engineer", "mud logging technician",
    "oil platform crew", "oil terminal operator",
    "offshore geotechnical engineer", "offshore installation manager",
    "petroleum engineer", "petroleum geologist",
    "petroleum production engineering", "petroleum technician",
    "pipeline operator", "plant operator", "process engineer",
    "production engineer", "reservoir engineer",
    "seismic data analyst", "subsurface engineer",
    "well logging technician",
    # Oil refinery processes & terms
    "oil refinery", "petroleum refinery", "crude oil distillation",
    "vacuum distillation", "catalytic reforming",
    "fluid catalytic cracking", "catalytic cracking",
    "thermal cracking", "distillate hydrotreater",
    "naphtha hydrotreater", "alkylation unit",
    "dimerization unit", "isomerization unit",
    "steam reforming", "amine gas treater",
    "sour water stripper", "solvent refining",
    "solvent dewaxing", "coking unit",
    "delayed coker", "fluid coker",
    "atmospheric distillation", "fractional distillation",
    "petroleum products", "petroleum coke",
    "liquefied petroleum gas", "petrochemical feedstock",
    "fuel oil", "heating oil", "petroleum naphtha",
    "diesel fuel", "jet fuel", "gasoline blending",
    "octane rating", "hydrodesulfurization",
    "hydrogen sulfide removal", "claus process",
    "refinery corrosion", "process turnaround",
    "crude oil processing", "refinery capacity",
]

# ── biotech_pharma.json — biology, chemistry, pharma ────────────────────────
WIKI_BIOTECH_PHARMA = [
    "amino acid", "adenosine triphosphate", "active transport",
    "activated sludge", "biomedical engineering", "biomimetic design",
    "cell biology", "cell membrane", "chemical bond",
    "chemical compound", "chemical kinetics", "chemical reaction",
    "chemical equilibrium", "covalent bond", "ionic bond",
    "electrode potential", "molar concentration", "molar mass",
    "molecular physics", "organic chemistry", "physical chemistry",
    "saturated compound", "unsaturated compound",
    "solubility equilibrium", "stoichiometric ratio",
    "acid base reaction", "molar attenuation coefficient",
    "van der waals equation", "van der waals force",
    "van t hoff equation", "van t hoff factor",
    "valence electron", "valence shell", "valence bond theory",
    "particle physics", "quantum electrodynamics",
    "quantum field theory",
]

# ── manufacturing.json — manufacturing processes ────────────────────────────
WIKI_MANUFACTURING = [
    "manufacturing engineering", "agricultural engineering",
    "aerospace engineering", "mechanical engineering",
    "civil engineering", "electrical engineering",
    "biomedical engineering", "mining engineering",
    "petroleum engineering", "industrial engineering",
    "molding process", "casting process",
    "particle accelerator",
]

# ── industry_terms.json — cross-industry technical terms ────────────────────
WIKI_INDUSTRY_TERMS = [
    "safety data sheet", "technical standard",
    "safe failure fraction", "quality assurance",
    "zero defects", "reliability engineering",
    "structural analysis", "structural load",
    "stress strain curve", "phase diagram",
    "steam table", "probability distribution",
    "probability theory", "point estimation",
    "root mean square", "dimensional analysis",
    "differential equation", "trigonometric functions",
]

# ── job_titles.json — engineering & petroleum job titles ─────────────────────
WIKI_JOB_TITLES = [
    "corrosion engineer", "chemical engineer", "drilling engineer",
    "environmental engineer", "mud engineer",
    "offshore geotechnical engineer", "offshore installation manager",
    "petroleum engineer", "petroleum geologist",
    "petroleum technician", "process engineer",
    "production engineer", "reservoir engineer",
    "seismic data analyst", "subsurface engineer",
    "mining engineer", "nuclear engineer",
    "sanitary engineer", "nanoengineering specialist",
    "control systems engineer", "power systems engineer",
    "telecommunications engineer", "signal processing engineer",
    "instrumentation engineer", "microelectronics engineer",
    "biomedical engineer", "reliability engineer",
    "structural engineer", "materials engineer",
    "aerospace engineer", "civil engineer",
    "mechanical engineer", "electrical engineer",
    "manufacturing engineer", "industrial engineer",
    "computer engineer", "software engineer",
]

# ── methodologies.json — analysis methods & frameworks ──────────────────────
WIKI_METHODOLOGIES = [
    "finite element analysis", "computational fluid dynamics",
    "stress strain analysis", "structural analysis",
    "modal analysis", "harmonic analysis",
    "fatigue life prediction", "dimensional analysis",
    "multidisciplinary design optimization",
    "statistical analysis", "point estimation",
    "probability theory", "probability distribution",
    "trigonometric functions", "linear algebra",
    "differential equation", "laplace transform",
    "fourier analysis", "stoichiometric analysis",
    "tensile testing", "charpy impact test",
]

# ── certifications.json — standards & professional bodies ───────────────────
WIKI_CERTIFICATIONS = [
    "professional engineer", "chartered engineer",
    "incorporated engineer", "european engineer",
    "certified professional engineer",
]

# ── NEW: science_fundamentals.json — pure physics/chem/math glossary ────────
WIKI_SCIENCE_FUNDAMENTALS = [
    # Physics fundamentals
    "absolute electrode potential", "angular acceleration",
    "angular momentum", "angular velocity",
    "alpha particle", "alternating current", "direct current",
    "brownian motion", "centre of mass", "centripetal force",
    "chain reaction", "circular motion", "conservation of energy",
    "conservation of momentum", "coulomb law", "critical point",
    "de broglie wavelength", "doppler effect", "drag coefficient",
    "elastic collision", "electric charge", "electric current",
    "electric field", "electric potential",
    "electromagnetic induction", "electromagnetic radiation",
    "electromagnetic spectrum", "electromotive force",
    "electron volt", "faraday law", "free body diagram",
    "gauss law", "gravitational energy", "gravitational field",
    "gravitational wave", "half life", "heat transfer",
    "helmholtz free energy", "hooke law",
    "inclined plane", "internal energy", "ionization energy",
    "joule heating", "kinematic viscosity", "kinetic energy",
    "laminar flow", "linear momentum", "lorentz force",
    "mach number", "magnetic field", "mass spectrometry",
    "maxwell equations", "mechanical advantage",
    "mechanical equilibrium", "mechanical wave",
    "moment of inertia", "natural frequency",
    "navier stokes equations", "newton laws of motion",
    "nuclear binding energy", "nuclear fusion",
    "ohm law", "pascal law", "pauli exclusion principle",
    "phase transition", "planck constant", "potential energy",
    "projectile motion", "quantum mechanics",
    "quantum electrodynamics", "quantum field theory",
    "refractive index", "relative density",
    "relative velocity", "reynolds number",
    "root mean square", "rotational energy",
    "rotational speed", "shortwave radiation",
    "simple machine", "special relativity",
    "speed of light", "spontaneous combustion",
    "stagnation pressure", "state of matter",
    "stefan boltzmann law", "superconductivity",
    "surface tension", "thermal conduction",
    "thermal equilibrium", "thermal radiation",
    "theory of relativity", "uncertainty principle",
    "van der waals force", "venturi effect",
    "wave particle duality",
    # Chemistry fundamentals
    "absolute electrode potential", "acid base equilibrium",
    "amino acid", "atomic mass", "atomic number",
    "avogadro number", "chemical bond", "chemical compound",
    "chemical equilibrium", "chemical kinetics",
    "chemical reaction", "covalent bond",
    "electrode potential", "electron configuration",
    "gibbs free energy", "henry law",
    "ionic bond", "molar concentration", "molar mass",
    "molecular physics", "organic chemistry",
    "oxidation reduction", "physical chemistry",
    "solubility equilibrium", "van der waals equation",
    "van t hoff equation", "van t hoff factor",
    "valence electron", "valence shell",
    # Mathematics fundamentals
    "applied mathematics", "differential equation",
    "fourier analysis", "laplace transform",
    "linear algebra", "mathematical optimization",
    "mathematical physics", "miller indices",
    "probability distribution", "probability theory",
    "scalar multiplication", "trigonometric functions",
    "vector space", "unit vector",
    # Thermodynamics
    "boltzmann constant", "boyle law",
    "brayton cycle", "carnot cycle", "rankine cycle",
    "first law of thermodynamics", "zeroth law of thermodynamics",
    "helmholtz free energy", "isentropic process",
    "isothermal process", "kelvin planck statement",
    "specific heat", "specific gravity",
    "specific volume", "specific weight",
    "stefan boltzmann law", "triple point",
    "trouton rule", "phase diagram", "phase rule",
    # Engineering science
    "archimedes principle", "bernoulli principle",
    "darcy weisbach equation", "euler laws",
    "fermat principle", "fluid dynamics",
    "fluid mechanics", "fluid statics",
    "fourier law", "fracture mechanics",
    "kirchhoff circuit laws", "lagrangian mechanics",
    "norton theorem", "rayleigh number",
    "thevenin theorem", "von mises yield criterion",
]

# ── abbreviations — new abbreviations from Wikipedia articles ───────────────
WIKI_ABBREVIATIONS = {
    "SDS": "safety data sheet",
    "MSDS": "material safety data sheet",
    "PSDS": "product safety data sheet",
    "SFF": "safe failure fraction",
    "PLC": "programmable logic controller",
    "MEMS": "microelectromechanical systems",
    "MOSFET": "metal oxide semiconductor field effect transistor",
    "AGC": "apollo guidance computer",
    "MOS": "metal oxide semiconductor",
    "IC": "integrated circuit",
    "QED": "quantum electrodynamics",
    "QFT": "quantum field theory",
    "UTS": "ultimate tensile strength",
    "CDU": "crude oil distillation unit",
    "FCC": "fluid catalytic cracker",
    "LPG": "liquefied petroleum gas",
    "BTX": "benzene toluene xylene",
    "DSP": "digital signal processor",
    "OSHA": "occupational safety and health administration",
    "NIOSH": "national institute for occupational safety and health",
    "ACGIH": "american conference of governmental industrial hygienists",
    "PPE": "personal protective equipment",
    "IEC": "international electrotechnical commission",
    "IEEE": "institute of electrical and electronics engineers",
    "IET": "institution of engineering and technology",
    "NSPE": "national society of professional engineers",
    "AMR": "autonomous mobile robot",
    "MDO": "multidisciplinary design optimization",
    "RMS": "root mean square",
    "AC": "alternating current",
    "DC": "direct current",
    "SI": "systeme international d unites",
    "RF": "radio frequency",
    "VLSI": "very large scale integration",
}


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def load_gazetteer(filepath):
    """Load a gazetteer JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_gazetteer(filepath, data):
    """Save a gazetteer JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def normalize(term):
    """Normalize a term for dedup: lowercase, strip, collapse spaces, remove possessives."""
    t = term.lower().strip()
    t = t.replace("'s", "s").replace("'", "").replace("–", " ").replace("-", " ")
    return " ".join(t.split())


def merge_terms(existing, new_terms):
    """Merge new terms into existing, deduplicated, sorted. Multi-word only."""
    seen = set()
    result = []
    for t in existing + new_terms:
        n = normalize(t)
        if n and n not in seen and len(n.split()) >= 2:
            seen.add(n)
            result.append(n)
    return sorted(result)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("GAZETTEER MERGE — Wikipedia Engineering/Science Glossary")
    print(f"Source: lists to add to the glossrys.txt (3,774 lines)")
    print(f"Target: {GAZETTEERS_DIR}")
    print("=" * 70)

    # ── Merge into existing gazetteers ──────────────────────────────────────
    merges = {
        "engineering.json":     WIKI_ENGINEERING,
        "tech_skills.json":     WIKI_TECH_SKILLS,
        "oil_gas.json":         WIKI_OIL_GAS,
        "biotech_pharma.json":  WIKI_BIOTECH_PHARMA,
        "manufacturing.json":   WIKI_MANUFACTURING,
        "industry_terms.json":  WIKI_INDUSTRY_TERMS,
        "job_titles.json":      WIKI_JOB_TITLES,
        "methodologies.json":   WIKI_METHODOLOGIES,
        "certifications.json":  WIKI_CERTIFICATIONS,
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
        data["source"] = data.get("source", "") + "+wikipedia_engineering_glossary"

        save_gazetteer(filepath, data)
        added = new_count - old_count
        print(f"  {filename}: {old_count} -> {new_count} (+{added} terms)")

    # ── Merge abbreviations ─────────────────────────────────────────────────
    abbr_file = os.path.join(GAZETTEERS_DIR, "abbreviations.json")
    if os.path.exists(abbr_file):
        data = load_gazetteer(abbr_file)
        old_abbr = data.get("abbreviations", {})
        old_count = len(old_abbr)
        total_before += old_count
        new_abbr = {**old_abbr, **WIKI_ABBREVIATIONS}
        total_after += len(new_abbr)
        data["abbreviations"] = dict(sorted(new_abbr.items()))
        data["version"] = data.get("version", 1) + 1
        data["updated"] = datetime.now().strftime("%Y-%m-%d")
        data["source"] = data.get("source", "") + "+wikipedia_engineering_glossary"
        save_gazetteer(abbr_file, data)
        added = len(new_abbr) - old_count
        print(f"  abbreviations.json: {old_count} -> {len(new_abbr)} (+{added} entries)")

    # ── Create NEW science_fundamentals.json gazetteer ──────────────────────
    sci_path = os.path.join(GAZETTEERS_DIR, "science_fundamentals.json")
    existing_terms = []
    if os.path.exists(sci_path):
        existing_data = load_gazetteer(sci_path)
        existing_terms = existing_data.get("terms", [])
    all_sci = merge_terms(existing_terms, WIKI_SCIENCE_FUNDAMENTALS)
    sci_data = {
        "label": "SCIENCE_FUNDAMENTALS",
        "description": "Physics, chemistry, mathematics, and thermodynamics fundamentals from Wikipedia engineering glossary",
        "source": "wikipedia_engineering_glossary",
        "version": 1,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "terms": all_sci
    }
    save_gazetteer(sci_path, sci_data)
    print(f"  science_fundamentals.json: NEW ({len(all_sci)} terms)")
    total_after += len(all_sci)

    print(f"\n{'=' * 70}")
    print(f"TOTAL: {total_before} -> {total_after} terms (+{total_after - total_before} new)")
    print(f"{'=' * 70}")

    # ── Sync to local gazetteers ────────────────────────────────────────────
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

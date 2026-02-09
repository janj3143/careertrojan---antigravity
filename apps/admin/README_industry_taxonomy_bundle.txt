IntelliCV-AI Industry Taxonomy Bundle
====================================

This bundle contains:

  • services/industry_taxonomy_service.py
      - Central service for SOC 2020, ESCO and NAICS 2022 lookups.
      - NO demo or fake data; everything is file-backed.

  • 18_Job_Title_AI_Integration.py
  • 19_Job_Title_Overlap_Cloud.py
  • 17_Mentor_Management.py
      - These are your current versions, copied from the system so you can
        patch them alongside the new service.

How to integrate
----------------

1. Place `industry_taxonomy_service.py` under your shared services module,
   for example:

       IntelliCV/
         shared_backend/
           services/
             industry_taxonomy_service.py   <-- this file

   or

       IntelliCV/
         services/
           industry_taxonomy_service.py

   Adjust imports accordingly (examples below assume `services` package).

2. Configure dataset paths via environment variables (Docker, dev, admin):

       INTELLICV_DATA_ROOT=/path/to/large_datasets

       INTELLICV_SOC2020_STRUCTURE=.../extendedsoc2020structureanddescriptionsexcel03122025.xlsx
       INTELLICV_SOC2020_INDEX=.../soc2020volume2thecodingindexexcel03122025.xlsx

       INTELLICV_ESCO_CLASSIFICATION=.../esco_classification_en.csv

       INTELLICV_NAICS_STRUCTURE=.../2022_NAICS_Structure.xlsx
       INTELLICV_NAICS_DESCRIPTIONS=.../2022_NAICS_Descriptions.xlsx

3. Wire into **Job Title AI Integration** (admin page 18):

     - At the top of `18_Job_Title_AI_Integration.py` add:

           from services.industry_taxonomy_service import (
               get_global_industry_taxonomy_service,
           )

     - When you show industry statistics or mappings, resolve industries
       using the service instead of any hard-coded, limited lists, e.g.:

           svc = get_global_industry_taxonomy_service()
           match = svc.infer_industry_for_job_title(some_job_title)
           if match:
               # use match.industries[0].name / .code in your UI

4. Wire into **Job Title Overlap Cloud** (admin page 19):

     - Import the same service:

           from services.industry_taxonomy_service import (
               get_global_industry_taxonomy_service,
           )

     - When computing overlap clusters, call:

           svc = get_global_industry_taxonomy_service()
           codes_by_tax = svc.infer_codes_for_job_title(job_title)

       and attach the resulting SOC / ESCO / NAICS codes into your
       overlap nodes so the admin can drill from clusters → industries.

5. Wire into **Mentor Management** (admin page 17):

     - Use the service to tag each mentorship offer and mentor profile
       with one or more industry codes:

           svc = get_global_industry_taxonomy_service()
           match = svc.infer_industry_for_job_title(mentor_primary_title)

           if match:
               offer["industry_codes"] = [ind.as_dict() for ind in match.industries]

     - These tags can then power filters in the Mentorship Marketplace
       (user portal) and keep everything aligned with SOC / ESCO / NAICS.

Notes
-----

• The service is deliberately conservative: if any dataset is missing,
  the corresponding loader simply returns and lookups fall back to other
  taxonomies. No placeholder values are generated.

• You can freely extend `IndustryTaxonomyService` with richer scoring,
  sector grouping (e.g. Technology, Healthcare, Finance, etc.) or an
  explicit mapping table derived from your existing `ai_data_final`
  job-title database.

• Because this bundle ships the original 17/18/19 pages unchanged,
  nothing will break if you drop the files in and then progressively
  integrate the new service.

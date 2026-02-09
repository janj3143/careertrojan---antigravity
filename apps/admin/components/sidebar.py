import streamlit as st

PAGES = [('00_admin_home.py', '00 • Admin Home'), ('01_data_roots_and_health.py', '01 • Data Roots and Health'), ('02_datasets_browser.py', '02 • Datasets Browser'), ('03_resume_json_viewer.py', '03 • Resume JSON Viewer'), ('04_parser_runs.py', '04 • Parser Runs'), ('05_enrichment_runs.py', '05 • Enrichment Runs'), ('06_keyword_ontology.py', '06 • Keyword Ontology'), ('07_phrase_manager.py', '07 • Phrase Manager'), ('08_email_capture.py', '08 • Email Capture'), ('09_email_analytics.py', '09 • Email Analytics'), ('10_job_index.py', '10 • Job Index'), ('11_role_taxonomy.py', '11 • Role Taxonomy'), ('12_scoring_analytics.py', '12 • Scoring Analytics'), ('13_bias_and_fairness.py', '13 • Bias and Fairness'), ('14_model_registry.py', '14 • Model Registry'), ('15_prompt_registry.py', '15 • Prompt Registry'), ('16_evaluation_harness.py', '16 • Evaluation Harness'), ('17_queue_monitor.py', '17 • Queue Monitor'), ('18_blob_storage.py', '18 • Blob Storage'), ('19_user_audit.py', '19 • User Audit'), ('20_admin_audit.py', '20 • Admin Audit'), ('21_notifications.py', '21 • Notifications'), ('22_system_config.py', '22 • System Config'), ('23_logs_viewer.py', '23 • Logs Viewer'), ('24_diagnostics.py', '24 • Diagnostics'), ('25_exports.py', '25 • Exports'), ('26_backup_and_restore.py', '26 • Backup and Restore'), ('27_route_map.py', '27 • Route Map'), ('28_api_explorer.py', '28 • API Explorer'), ('29_about.py', '29 • About')]

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## Admin Tools (00–29)")
        for fname, label in PAGES:
            st.page_link(f"pages/{fname}", label=label, icon="➡️")

# Routing Trace Report

Generated: 2026-03-10T11:24:12Z

## FastAPI Composition
- Router mounting occurs in services/backend_api/main.py
- Mounted routes observed: 320

## Critical Route Families
- /api/ops/v1/*
- /api/intelligence/v1/*
- /api/lenses/v1/*
- /api/payment/v1/*
- /api/mentor/v1/*

## Trace Focus for Next Pass
- upload -> parsing -> feature generation -> inference -> explanation -> visual payload

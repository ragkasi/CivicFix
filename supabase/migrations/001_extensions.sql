-- Enable required PostgreSQL extensions for CivicFix.
-- Run this migration first on any new Supabase project.

create extension if not exists postgis;
create extension if not exists vector;
create extension if not exists pgcrypto;
create extension if not exists "uuid-ossp";

-- Seed initial city departments.
-- Run after 002_schema.sql.
-- Safe to run multiple times — uses ON CONFLICT (slug) DO NOTHING.

insert into departments (slug, name, description, category_coverage, contact_email) values
  (
    'public_works',
    'Public Works',
    'Handles road infrastructure, sidewalks, and drainage systems.',
    array['pothole','road_hazard','sidewalk_damage','flooding','snow_or_ice'],
    'publicworks@city.gov'
  ),
  (
    'transportation',
    'Transportation',
    'Manages traffic signals, road signs, and street safety.',
    array['damaged_sign','streetlight'],
    'transportation@city.gov'
  ),
  (
    'sanitation',
    'Sanitation',
    'Manages trash collection, overflow cleanup, and graffiti removal.',
    array['trash_overflow','graffiti'],
    'sanitation@city.gov'
  ),
  (
    'parks_and_recreation',
    'Parks and Recreation',
    'Maintains public parks, trails, and urban trees.',
    array['other'],
    'parks@city.gov'
  ),
  (
    'water_and_drainage',
    'Water and Drainage',
    'Manages water mains, storm drains, and flood response.',
    array['flooding'],
    'water@city.gov'
  ),
  (
    'code_enforcement',
    'Code Enforcement',
    'Handles zoning violations, blight, and public nuisance issues.',
    array['graffiti','other'],
    'codeenforcement@city.gov'
  ),
  (
    'general_services',
    'General Services',
    'Handles miscellaneous city operations not covered by other departments.',
    array['other'],
    'generalservices@city.gov'
  )
on conflict (slug) do nothing;

-- Seed initial city departments.
-- Run after 002_schema.sql.

insert into departments (name, description, category_coverage, contact_email) values
  (
    'Public Works',
    'Handles road infrastructure, sidewalks, and drainage systems.',
    array['pothole','road_hazard','sidewalk_damage','flooding','snow_or_ice'],
    'publicworks@city.gov'
  ),
  (
    'Transportation',
    'Manages traffic signals, road signs, and street safety.',
    array['damaged_sign','streetlight'],
    'transportation@city.gov'
  ),
  (
    'Sanitation',
    'Manages trash collection, overflow cleanup, and graffiti removal.',
    array['trash_overflow','graffiti'],
    'sanitation@city.gov'
  ),
  (
    'Parks and Recreation',
    'Maintains public parks, trails, and urban trees.',
    array['other'],
    'parks@city.gov'
  ),
  (
    'Water and Drainage',
    'Manages water mains, storm drains, and flood response.',
    array['flooding'],
    'water@city.gov'
  ),
  (
    'Code Enforcement',
    'Handles zoning violations, blight, and public nuisance issues.',
    array['graffiti','other'],
    'codeenforcement@city.gov'
  ),
  (
    'General Services',
    'Handles miscellaneous city operations not covered by other departments.',
    array['other'],
    'generalservices@city.gov'
  )
on conflict do nothing;

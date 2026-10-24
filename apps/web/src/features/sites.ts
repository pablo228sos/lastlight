export type SiteId = 'school' | 'clinic' | 'business' | 'residential'
export const sites: { id: SiteId; name: string; category: string; description: string }[] = [
  { id: 'school', name: 'School', category: 'PUBLIC EDUCATION / ARCHETYPE', description: 'A campus-scale energy system awaiting a verified outage simulation.' },
  { id: 'clinic', name: 'Clinic', category: 'COMMUNITY CARE / ARCHETYPE', description: 'A synthetic care facility for exploring critical-load continuity.' },
  { id: 'business', name: 'Small business', category: 'LOCAL COMMERCE / ARCHETYPE', description: 'A compact commercial site with research-stage assumptions.' },
  { id: 'residential', name: 'Residential', category: 'HOUSING / ARCHETYPE', description: 'A residential cluster prepared for scenario analysis.' },
]

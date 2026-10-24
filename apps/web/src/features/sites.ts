export type SiteId = 'school' | 'clinic' | 'business' | 'residential'
export const sites: { id: SiteId; name: string; category: string; description: string }[] = [
  { id: 'school', name: 'School', category: 'PUBLIC EDUCATION / ARCHETYPE', description: 'A campus-scale energy system awaiting a verified outage simulation.' },
  { id: 'clinic', name: 'Clinic', category: 'COMMUNITY CARE / VISUAL SITE STUDY', description: 'A single care facility and entrance court. No validated energy model is available for this site.' },
  { id: 'business', name: 'Small business', category: 'LOCAL COMMERCE / VISUAL SITE STUDY', description: 'A single street-facing commercial building. No validated energy model is available for this site.' },
  { id: 'residential', name: 'Residential cluster', category: 'THREE HOUSING BLOCKS / VISUAL SITE STUDY', description: 'Three blocks and their shared courtyard form one selected parcel. No validated energy model is available.' },
]

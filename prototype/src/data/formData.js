export const FORM_OBJECTIVES = [
  {
    short: 'Obj 1',
    full: '1. Promote Gender Equitable and Non-Violent Behaviours by Raising Awareness and Addressing Harmful Social Norms Perpetuating SRGBV',
    tactics: [
      'Carry Out Nationwide Media Campaigns',
      'Strengthen Peer Education Programs',
      'Conduct School-Based Awareness Campaigns',
    ],
  },
  {
    short: 'Obj 2',
    full: '2. Strengthen Institutional and Community Capacity to Prevent and Respond to SRGBV',
    tactics: [
      'Strengthen Capacity of School Personnel',
      'Establish Safe and Inclusive Learning Environments',
      'Implement Community-Based Monitoring and Engagement',
    ],
  },
  {
    short: 'Obj 3',
    full: '3. Ensure Sustained Commitment to SRGBV Prevention Through Policy Enforcement and Stakeholder Engagement',
    tactics: [
      'Enforce Policy',
      'Strengthen Reporting and Referral Systems',
      'Engage Stakeholders for Sustainability',
    ],
  },
];

export const FOCUS_AREAS = [
  '1. SRGBV Prevention & Response',
  '2. MHPSS',
  '3. School Governance',
  '4. Life Skills / SRH',
  '5. WASH',
  '6. Social Norms',
  '7. Social Protection',
  '8. Other',
];

// Data dict 5.4 — Activity Types
export const ACTIVITY_TYPES = [
  'Training / Capacity Building',
  'Safe Space / Club Establishment',
  'Awareness / Community Sensitisation',
  'Counselling / Psychosocial Support',
  'Cash / Material Transfer',
  'Referral / Case Management',
  'Governance / Policy Development',
  'Other (specify)',
];

// Data dict 5.5
export const IMPLEMENTATION_STATUSES = [
  'Not started', 'Ongoing', 'Completed', 'Delayed',
];

export const GOV_COUNTERPARTS = [
  'MBSSE', 'MoGCA', 'MSW', 'MoYA', 'TSC', 'Local Council', 'NASSIT', 'Other',
];

export const REFERRAL_PATHWAYS = [
  'Police Family Support Unit (FSU)',
  'One-Stop Centre',
  'Social Welfare Office',
  'Health Facility',
  'Community Child Welfare Committee',
  'Other',
];

export const BUDGET_STATUSES = [
  'On track', 'Under-spending', 'Over-spending',
];

export const DISTRICTS = [
  'Bo', 'Bombali', 'Bonthe', 'Falaba', 'Kailahun', 'Kambia', 'Karene',
  'Kenema', 'Koinadugu', 'Kono', 'Moyamba', 'Port Loko', 'Pujehun',
  'Tonkolili', 'Western Area Rural', 'Western Area Urban',
];

export const SECTIONS = [
  { id: 'A', label: 'Reporting metadata', page: 1, required: true },
  { id: 'B', label: 'Geographic coverage', page: 1, required: true },
  { id: 'C', label: 'Activity classification', page: 1, required: true },
  { id: 'D', label: 'Implementation details', page: 1, required: true },
  { id: 'E', label: 'Output indicators', page: 2, required: true },
  { id: 'F', label: 'Outcome snapshot', page: 2, required: false },
  { id: 'G', label: 'Financial tracking', page: 2, required: false },
  { id: 'H', label: 'Coordination', page: 2, required: false },
  { id: 'I', label: 'Challenges & risks', page: 3, required: false },
  { id: 'J', label: 'Safeguarding', page: 3, required: true, critical: true },
  { id: 'K', label: 'Evidence uploads', page: 3, required: false },
  { id: 'L', label: 'Next period plan', page: 3, required: false },
  { id: 'M', label: 'Data quality', page: 3, required: false, systemManaged: true },
];

// All 9 tactics (data dictionary 5.4)
export const TACTICS = [
  'Carry Out Nationwide Media Campaigns',
  'Strengthen Peer Education Programs',
  'Conduct School-Based Awareness Campaigns',
  'Strengthen Capacity of School Personnel',
  'Establish Safe and Inclusive Learning Environments',
  'Implement Community-Based Monitoring and Engagement',
  'Enforce Policy',
  'Strengthen Reporting and Referral Systems',
  'Engage Stakeholders for Sustainability',
];

export const INTERVENTION_LEVELS = [
  'School-based',
  'Community-based',
  'System-level',
];

// Chiefdoms by district (official names). Used to filter the Section B chiefdom
// picker to the partner's selected district(s).
export const CHIEFDOMS_BY_DISTRICT = {
  "Kailahun": ["Dea", "Jawie", "Kissi Kama", "Kissi Teng", "Kissi Tongi", "Kpeje Bongre", "Kpeje West", "Luawa", "Malema", "Mandu", "Njaluahun", "Penguia", "Upper Bambara", "Yawei"],
  "Kenema": ["Dama", "Dodo", "Gaura", "Gorama Mende", "Kandu Leppiama", "Koya", "Langrama", "Lower Bambara", "Malegohun", "Niawa", "Nomo", "Nongowa", "Simbaru", "Small Bo", "Tunkia", "Wandor", "Kenema Town"],
  "Kono": ["Fiama", "Gbane", "Gbane Kandor", "Gbense", "Gorama Kono", "Kamara", "Lei", "Mafindor", "Nimikoro", "Nimiyama", "Sandor", "Soa", "Tankoro", "Toli", "Koidu Town"],
  "Bombali": ["Biriwa", "Bombali Sebora", "Gbanti Kamaranka", "Gbendembu Ngowahun", "Magbaimba Ndorhahun", "Makari Gbanti", "Paki Masabong", "Safroko Limba", "Makeni Town"],
  "Koinadugu": ["Diang", "Kasunko", "Nieni", "Sengbe", "Wara Wara Bafodia", "Wara Wara Yagala"],
  "Tonkolili": ["Gbonkolenken", "Kafe Simiria", "Kalansogoia", "Kholifa Mabang", "Kholifa Rowala", "Kunike Barina", "Kunike", "Malal Mara", "Sambaya", "Tane", "Yoni"],
  "Falaba": ["Dembelia-Sinkunia", "Folosaba-Dembelia", "Mongo", "Neya", "Sulima"],
  "Bo": ["Badjia", "Bagbo", "Bagbwe (Bagbe)", "Boama", "Bumpe Ngao", "Gbo", "Jaiama Bongor", "Kakua", "Komboya", "Lugbu", "Niawa Lenga", "Selenga", "Tikonko", "Valunia", "Wonde", "Bo Town"],
  "Bonthe": ["Bendu Cha", "Bum", "Dema", "Imperri", "Jong", "Kpanda Kemo", "Kwamebai Krim", "Nongoba Bullom", "Sittia", "Sogbeni", "Yawbeko", "Bonthe Urban"],
  "Moyamba": ["Bagruwa", "Bumpeh", "Dasse", "Fakunya", "Kagboro", "Kaiyamba", "Kamajei", "Kongbora", "Kori", "Kowa", "Lower Banta", "Ribbi", "Timdale", "Upper Banta"],
  "Pujehun": ["Barri", "Galliness Perri", "Kpaka", "Panga Kabonde", "Makpele", "Malen", "Mano Sakrim", "Panga Krim", "Pejeh (Futa Pejeh)", "Soro Gbema", "Sowa", "Yakemu Kpukumu"],
  "Western Area Rural": ["Koya Rural", "Mountain Rural", "Waterloo Rural", "York Rural"],
  "Western Area Urban": ["Central I", "Central II", "East I", "East II", "East III", "West I", "West II", "West III", "Tasso Island"],
  "Kambia": ["Bramaia", "Gbinle Dixing", "Magbema", "Mambolo", "Masungbala", "Samu", "Tonko Limba"],
  "Karene": ["Buya Romende", "Dibia", "Sanda Magbolontor", "Libeisaygahun", "Sanda Loko", "Sanda Tendaren", "Sella Limba", "Tambakha"],
  "Port Loko": ["Bureh Kasseh Makonteh", "Kaffu Bullom", "Koya", "Lokomasama", "Maforki", "Marampa", "Masimera", "Tinkatupa Makonteh Safroko (TMS)"],
};

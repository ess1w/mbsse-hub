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

export const ACTIVITY_TYPES = [
  'Training / Capacity Building',
  'Community Outreach',
  'Awareness Campaign',
  'Safe Space Activities',
  'Policy / Advocacy',
  'Research / Assessment',
  'Coordination Meeting',
  'Other',
];

export const IMPLEMENTATION_STATUSES = [
  'Completed', 'Ongoing', 'Delayed', 'Cancelled',
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

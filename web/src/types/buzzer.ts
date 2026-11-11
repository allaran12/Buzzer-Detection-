export type RiskLevel = "high" | "medium" | "low";

export type RelationType = "original" | "reply" | "retweet" | "quote";

export interface TweetSample {
  id: string;
  date: string;
  text: string;
  relationType: RelationType;
  targetUsername?: string | null;
  targetPostId?: string | null;
  duplicateSimilarity?: number;
  burstEvent?: boolean;
}

export interface SuspiciousIndicator {
  name: string;
  score: number; // 0 - 100
  weight: number;
  description: string;
  status: "danger" | "warning" | "normal";
}

export interface BuzzerAccount {
  id: string;
  username: string;
  name: string;
  avatar: string;
  bio: string;
  created: string;
  accountAgeDays: number;
  followers: number;
  following: number;
  followerRatio: number; // following / followers
  statuses: number;
  statusesPerDay: number;

  // Analysis Metrics
  buzzerScore: number; // 0 - 100
  riskLevel: RiskLevel;
  campaignIssue: string; // e.g., "PrayForKalimantan", "Pilpres wowo2", "RoySuryo"
  nPostsInDataset: number;
  postRatePerHour: number;
  duplicateTextRatio: number; // 0.0 - 1.0
  burstRatio: number; // 0.0 - 1.0
  outDegree: number; // count of replies/quotes to other accounts
  isClusterLeader?: boolean;
  clusterId?: string;

  // Detail components
  indicators: SuspiciousIndicator[];
  tweets: TweetSample[];
}

export interface DashboardSummary {
  totalAccounts: number;
  totalPosts: number;
  highRiskCount: number;
  mediumRiskCount: number;
  lowRiskCount: number;
  avgBuzzerScore: number;
  clustersDetected: number;
  burstEventsCount: number;
  lastUpdated: string;
}

export interface FilterState {
  searchQuery: string;
  riskFilter: "all" | "high" | "medium" | "low";
  issueFilter: string;
  sortBy: "buzzerScore" | "nPostsInDataset" | "postRatePerHour" | "followerRatio" | "accountAgeDays";
  sortOrder: "asc" | "desc";
}


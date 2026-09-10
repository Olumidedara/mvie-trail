export type VideoAsset = {
  local?: string;
  browser_download_url?: string;
};

export type LibraryEntry = {
  id: string;
  created_at: string;
  genre: string;
  topic: string;
  title: string;
  description: string;
  tags: string[];
  hook: string;
  captions: string;
  videos: Record<string, VideoAsset>;
  release?: { html_url: string; tag_name: string } | null;
};

export type ReleaseAsset = {
  name: string;
  browser_download_url: string;
  size?: number;
};

export type Release = {
  tag_name: string;
  name: string;
  html_url: string;
  body?: string;
  created_at: string;
  assets: ReleaseAsset[];
};

export type WorkflowRun = {
  id: number;
  status: string;
  conclusion: string | null;
  created_at: string;
  event: string;
  head_branch: string;
  run_number: number;
  html_url: string;
};

export type Schedule = {
  enabled: boolean;
  time: string;
  days: string[];
  max_videos_per_run: number;
  timezone: string;
};

export const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
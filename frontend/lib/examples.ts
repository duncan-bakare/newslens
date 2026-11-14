// One-click example articles shown on the empty screen.
// Edit freely. Pick free (non-paywalled) articles, since the scraper rejects
// paywalled sites, and prefer evergreen URLs that will not disappear.
export interface Example {
  label: string;
  url: string;
}

export const EXAMPLES: Example[] = [
  {
    label: "Guardian editorial",
    url: "https://www.theguardian.com/commentisfree/2022/nov/09/the-guardian-view-on-the-us-midterm-results-the-red-wave-that-wasnt",
  },
  {
    label: "Fox News report",
    url: "https://www.foxnews.com/politics/pence-leaves-door-open-2028-white-house-run-issues-stark-warning-gop-after-midterm-disaster",
  },
];

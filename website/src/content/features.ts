export type Feature = {
  title: string;
  eyebrow: string;
  blurb: string;
  bullets: string[];
  highlight?: boolean;
};

export const features: Feature[] = [
  {
    title: "Local file and folder scanning",
    eyebrow: "ClamAV engine",
    blurb:
      "Use the host-installed ClamAV engine for on-demand file, folder, home, and system scans. ClamAV and its configured signature database stay under your distro's package and FreshClam services.",
    bullets: [
      "Standalone and optional daemon backends",
      "Profiles, exclusions, progress, and readable results",
      "No second bundled engine or private database copy",
    ],
  },
  {
    title: "Multiple signatures and local YARA",
    eyebrow: "Configured rules",
    blurb:
      "ClamAV can load compatible signature files from its configured database directory. Linux Defender shows the files it detects and can pass selected local YARA rules alongside that system database for standalone scans.",
    bullets: [
      "Show recognized host database files",
      "Run local YARA rules with clamscan",
      "Third-party feed installation and updates are still a separate task",
    ],
  },
  {
    title: "VirusTotal and urlscan",
    eyebrow: "Online · opt in",
    blurb:
      "Check file, folder, or URL reputation with a chosen service. The app asks before sending data and reports online reputation separately from the local ClamAV result.",
    bullets: [
      "VirusTotal file and URL analysis",
      "Bounded folder uploads and visible progress",
      "urlscan URL checks with visibility selection",
    ],
    highlight: true,
  },
  {
    title: "Quarantine and recovery",
    eyebrow: "Careful handling",
    blurb:
      "Keep flagged files in restricted local storage with integrity checks and a clear restore or delete path. Review a detection before taking action.",
    bullets: [
      "Hash-verified restore flow",
      "Searchable, paged quarantine list",
      "History and scan evidence for follow-up",
    ],
  },
  {
    title: "Security audit and updates",
    eyebrow: "Host status",
    blurb:
      "Review selected security posture checks and ClamAV service/database status in one place. The audit is advisory and does not change system settings.",
    bullets: [
      "Read-only firewall and host checks",
      "Show FreshClam service and timer state",
      "System-managed signature update schedule",
    ],
  },
  {
    title: "Desktop integration",
    eyebrow: "One Linux app",
    blurb:
      "Use scan actions from the app, supported file managers, and the optional system tray. Distribution and desktop behavior still needs validation on each target.",
    bullets: [
      "Tray scan and update actions",
      "File-manager actions for supported desktops",
      "Scheduling, logs, and scan statistics",
    ],
  },
];

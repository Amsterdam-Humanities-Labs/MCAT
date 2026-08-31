---
title: Getting Started
description: Install MCAT and learn what each content state means.
---

<script>
  import { base } from '$app/paths';
  import { StatusBadge } from '@mcat/shared-ui';
  import P from '$components/P.svelte';
</script>


# Documentation

## Installation

MCAT requires Chrome Chrome installed on the device. 

### macOS

MCAT is currently available for macOS only, on Apple Silicon Macs (M1 or later). Intel Macs are not supported.

**[Download the latest macOS build →](https://github.com/Amsterdam-Humanities-Labs/MCAT/releases/latest/download/MCAT-macOS-arm64.zip)**

1. Unzip the download and move MCAT.app into your Applications folder.
2. Open it. macOS will refuse and warn you the app is from an unidentified developer. This is expected: MCAT is research software distributed outside the App Store, so it isn't signed by Apple.
3. Open **System Settings → Privacy & Security** and scroll to the **Security** section at the bottom. You'll see a note that MCAT was blocked; click **Open Anyway** and enter your password.

### Linux and Windows

Linux and Windows support is coming. In the meantime, you can build from source by following the build section on [GitHub](https://github.com/Amsterdam-Humanities-Labs/MCAT#building--installing).

## First run

### Prepare your input data 

MCAT takes a CSV of URLs in and writes a CSV of results out. The only requirement is one column of URLs. Every other column passes through to the output CSV untouched. The smallest valid CSV file is:

```
url
https://www.youtube.com/watch?v=QI87UoRlfIY
https://www.youtube.com/watch?v=_eMrAZLorQs
```

To try a first run without assembling urls, download one of these samples:

- [youtube-sample-10.csv]({base}/examples/youtube-sample-10.csv)
- [instagram-sample-10.csv]({base}/examples/instagram-sample-10.csv)
- [facebook-sample-10.csv]({base}/examples/facebook-sample-10.csv)
- [x-sample-10.csv]({base}/examples/x-sample-10.csv)

### Create a project

A project is a folder. Its `project.json` holds the configuration; the input CSV and every run's results sit beside it, all as plain CSV. **Avoid editing any of the project's CSVs directly: each URL carries an index that MCAT allocates and tracks, and edits outside the app can corrupt the project.** To analyse or edit output CSV from a project it's recommended to copy the desired file and work on it elsewhere on your disk. In the app, click **New Project** and fill in five fields:

- **Project Name**: the folder name.
- **Project Location**: where to put it. Keep it outside the app folder, since updating MCAT deletes anything stored beside the app.
- **Platform**: YouTube, Instagram, Facebook, or X. One platform per project.
- **Source CSV**: your input file.
- **URL Column**: pick the column that holds the URLs.

### Setting up MCAT with consent and login cookies

Cookies are small pieces of data a site stores in your browser so it remembers you between page loads. They let MCAT see a platform as a logged-in user would, removing login walls and consent walls from the scraped data. MCAT stores two kinds of cookies:

**Consent cookies** record that you answered the platform's cookie or privacy banner. They belong to the browser, not to you, and carry no account information. Dismissing the banner once is what they preserve.

**Login cookies** are the session token the platform issues after you sign in. They are what proves to the platform that a request comes from your account, and they are the reason MCAT can see what a logged-in visitor sees.

<P variant="warning">Always create a new throwaway account for each platform, never use your personal one. MCAT never stores passwords, only cookies.</P>

Click **Set up browser**. A Chrome window opens. Dismiss the cookie banner and log in where needed. MCAT stores the resulting cookies inside the project and reuses them until they expire.

#### How are session cookies stored

MCAT stores cookies in `cookies/<platform>.json` of the project folder, one file per platform, readable only by your user account. Cookies never leave your machine. MCAT has no account, no server, and no telemetry, and the file is only ever read back to rebuild the same browser session. Anyone who gets this file is signed in as that account without needing your password or a 2FA code, and can read its private messages, post as it, and change its settings or lock you out, until the cookies expire.

To avoid leaking cookies, delete the `cookies` folder before sharing or publishing a project folder. **Reset browser** in the respective project does the same thing, and a good habit is to reset once you're done with a project.

### Run it

Before you start, leave **Save screenshots** on unless you have a reason not to: screenshots let you check MCAT's verdict by eye, and they are evidence of what the page looked like at that moment.

Click **Start**. Every URL resolves to one of seven [content states](#content-states): live, restricted, moderated, unavailable, login_required, unknown, or error. The progress bar fills by state as URLs resolve, and the activity log prints each check. **Pause** stops after the in-flight checks finish. **Resume** picks up where it left off. **Abandon** discards the run.

### Read the results

Each run appears in the timeline. Click one to expand it:

- **All Results**: every URL and the state it resolved to.
- **Changes**: what moved since the previous run. Empty on the first run.
- **Run Info**: when it ran, how long it took, which account was used.

**Run Folder** opens the run on disk:

```
my-project/
├── project.json
├── urls.csv
└── runs/
    └── 2026-01-14_1030/
        ├── results.csv
        ├── changes.csv   (second run onward)
        └── screenshots/
            ├── live/
            ├── unavailable/
            └── …
```

`results.csv` is your input CSV plus:

- **mcat_status**: the content state.
- **mcat_detail**: the specific reason, such as age-restricted or removed by uploader.
- **mcat_screenshot**: the path to the page screenshot.
- **mcat_timestamp**: when it was checked.
- **mcat_error**: why a check failed, if it did.
- **mcat_user**: which account was used, stored as the platform's internal numeric account ID.

### Check again over time

Set **Repeat every** to an interval in minutes, hours, or days. MCAT re-checks the same URLs on that schedule. The first completed run in a project is its **baseline**. It records the starting state and its Changes tab stays empty. Every run after that is compared against **the run immediately before it**, matching URLs between the two runs and reporting the ones whose state differs.

Abandoned runs are skipped, so the comparison always reaches back to the last run that finished. From the second run on, each run folder also gets a `changes.csv` alongside `results.csv`, listing every changed URL with its previous and new state.

### Adding new URLs to a project

A project's URLs are fixed when you create it. When you have new URLs to track, create a new project.

## Scraping hygiene

### Your IP's reputation

MCAT checks each URL from your own internet connection, so every check comes from your IP address. When one connection makes many automated visits in a short time, networks and platforms can lower the reputation of that address. A few companies, such as Cloudflare and Google, handle bot checks for a large part of the web, and each sees your address across every site it covers. Because ofthis, you may start seeing bot checks, such as captchas or a "verifying you're not a bot" message, on normal websites for a while,even ones you never scraped. This is not permanent. The reputation recovers over days or weeks once you stop scraping.

### Lowering your scraping footprint

Large runs and repeated runs affect the reputation most, and scheduled tracking affects it more than anything else, because it repeats on its own over several days. To keep the effect small, check only the URLs you need, and set long tracking intervals. If your own browsing starts showing bot checks, stop for a while and let the IP address recover.

### Using a VPN for long or tracked runs

For long runs or tracking it's recommended to use a VPN service. VPN hides your real IP address from platform's bot detection protecting your home network's reputation. Use the VPN's desktop app, so that all of MCAT's traffic goes through it. Some platforms are stricter with VPN addresses than with home ones, so check that your targets still load with the VPN.

## Content states

Every checked URL resolves to one content state. A few states only occur on certain platforms.

- <StatusBadge status="live" /> Loads and is publicly viewable. All platforms.
- <StatusBadge status="restricted" /> Present but access-gated, such as age-restricted, geo-blocked, or private. YouTube and X.
- <StatusBadge status="moderated" /> Taken down by platform enforcement, such as a suspended account or terminated channel. YouTube and X.
- <StatusBadge status="unavailable" /> Gone: deleted by the uploader, a 404, or expired. All platforms.
- <StatusBadge status="login_required" /> An auth wall blocked the check; the content itself may still be live. Instagram.
- <StatusBadge status="unknown" /> Loaded but nothing matched, left for a human to judge from the screenshot. All platforms.
- <StatusBadge status="error" /> The check itself failed: no load, a timeout, or a crash. All platforms.

### States by platform

Which states occur, and how reliably they are told apart, varies by platform.

### YouTube

Tells apart <StatusBadge status="live" />, <StatusBadge status="unavailable" />, <StatusBadge status="restricted" />, and <StatusBadge status="moderated" />. It reads the visible page text for removal, age, geo, private, and channel-termination markers, and confirms <StatusBadge status="live" /> from the rendered video title. Run it once through **Set up browser** to capture the consent cookie; without it, checks are redirected to a consent page.

### Instagram

Works without login, since Instagram shows post previews to anonymous visitors. It reads <StatusBadge status="unavailable" /> from the page title and error state, and confirms <StatusBadge status="live" /> from the post caption. When a login wall is the only signal it reports <StatusBadge status="login_required" />, so log in through **Set up browser** for fuller coverage.

### Facebook

The coarsest of the four: in practice it only separates <StatusBadge status="live" /> from <StatusBadge status="unavailable" />. Unavailable pages load fast with a clear error; live pages render slowly. Every anonymous page embeds a login form, so there is no reliable <StatusBadge status="login_required" /> signal and undecided pages fall back to <StatusBadge status="unknown" />.

### X

Renders a tweet card only when a post is genuinely live, so a card is conclusive <StatusBadge status="live" />, checked before any takedown phrase. Run it logged in through **Set up browser**: logged out, X throttles even live tweets to a generic page that misreads as <StatusBadge status="unavailable" />.

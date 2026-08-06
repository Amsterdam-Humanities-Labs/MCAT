---
title: Getting Started
description: Install MCAT and learn what each content state means.
---

<script>
  import { base } from '$app/paths';
  import { StatusBadge } from '@mcat/shared-ui';
</script>

# Documentation

## Installation

MCAT requires Google Chrome installed on the device.

### macOS

MCAT is currently available for macOS only, on Apple Silicon Macs (M1 or later). Intel Macs are not supported.

**[Download the latest macOS build →](https://github.com/Amsterdam-Humanities-Labs/MCAT/releases/latest/download/MCAT-macOS-arm64.zip)**

1. Unzip the download and move MCAT.app into your Applications folder.
2. Open it. macOS will refuse and warn you the app is from an unidentified developer — this is expected. MCAT is research software distributed outside the App Store, so it isn't signed by Apple.
3. Open **System Settings → Privacy & Security** and scroll to the **Security** section at the bottom. You'll see a note that MCAT was blocked; click **Open Anyway** and enter your password.

### Linux and Windows

Linux and Windows support is coming. In the meantime, you can build from source by following the build section on [GitHub](https://github.com/Amsterdam-Humanities-Labs/MCAT#building--installing).

## First run

MCAT takes a CSV of URLs in and writes a CSV of results out. 

### Prepare your CSV

The only requirements are a header row and one column of URLs. The column can be named anything. Every other column passes through to the output untouched, so keep your titles, IDs, and dates. The smallest valid CSV file is:

```
url
https://www.youtube.com/watch?v=QI87UoRlfIY
https://www.youtube.com/watch?v=_eMrAZLorQs
```

To try a first run without assembling a list yourself, download one of these samples.

- [youtube-sample-10.csv]({base}/examples/youtube-sample-10.csv)
- [instagram-sample-10.csv]({base}/examples/instagram-sample-10.csv)
- [facebook-sample-10.csv]({base}/examples/facebook-sample-10.csv)
- [x-sample-10.csv]({base}/examples/x-sample-10.csv)

### Create a project

A project is a folder containing the main project.json all necessary information for the project. It contains the input CSV and results from all runs also stored as CSV. **It is recommended to avoid editing or updating any of the projects CSVs directly, since this can lead to project corruption**. Copy the desired CSV and edit it elsewhere on your disk.

In the app, click **New Project** and fill in five fields:

- **Project Name**: the folder name.
- **Project Location**: where to put it. Keep it outside the app, updating MCAT later on deletes anything stored beside it.
- **Platform**: YouTube, Instagram, Facebook, or X. One platform per project.
- **Source CSV**: your input file.
- **URL Column**: pick the column that holds the URLs.

### Setting up MCAT with consent and login cookies 

Cookies allow MCAT to see a platform as a logged user would, they remove login walls and consent walls from the scraped data. It als

**When working with MCAT always use a platform throwaway account, never your personal one. MCAT never stores passwords, only cookies.**

MCAT stores two kinds of cookies:

**Consent cookies** record that you answered the platform's cookie or privacy banner. They belong to the browser, not to you, and carry no account information. Dismissing the banner once is what they preserve.

**Login cookies** are the session token the platform issues after you sign in. They are what proves to the platform that a request comes from your account, and they are the reason MCAT can see what a logged-in visitor sees.

Click **Set up browser**. A Chrome window opens. Dismiss the cookie banner and log in where needed. MCAT stores the resulting cookies inside the project and reuses them for the duration of the project or until cookie naturally expires.

#### How are session cookies tored 

MCAT stores cookies in `cookies/<platform>.json` of the project folder, one file per platform, readable only by your user account. Cookies never leave your machine. MCAT has no account, no server, and no telemetry, and the file is only ever read back to rebuild the same browser session. 

Storing this file is not much riskier than what your browser already does with your sessions, but MCAT's copy lives inside a project folder. Two habits worth keeping: delete the `cookies` folder before sharing or publishing a project, since nothing else in the project depends on it, and click **Logout** when you are done with a platform, which deletes the stored cookies for it.

### Run it

Leave **Save screenshots** on unless you have a reason not to. The screenshot lets you check MCAT's verdict by eye, and it's the only evidence of what the page looked like at that moment.

Click **Start**. The progress bar fills by state as URLs resolve, and the activity log prints each check. **Pause** stops after the in-flight checks finish. **Resume** picks up where it left off. **Abandon** discards the run.

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
        └── screenshots/
            ├── live/
            ├── unavailable/
            └── …
```

`results.csv` is your original columns plus:

| Column | What it holds |
|---|---|
| `mcat_status` | The content state |
| `mcat_detail` | The specific reason, e.g. age-restricted, removed by uploader |
| `mcat_screenshot` | Path to the screenshot for this check |
| `mcat_timestamp` | When it was checked |
| `mcat_error` | Why a check failed, when it did |
| `mcat_user` | Which account was used |

Rows are written as the run goes, so a crash still leaves you everything completed so far.

### Check again over time

One run is a snapshot. The point of MCAT is the second run and the ones after it.

Set **Repeat every** to an interval in minutes, hours, or days. MCAT re-checks the same URLs on that schedule, and each new run diffs itself against the one before, so the Changes tab shows exactly what got taken down, restricted, or restored in between. Tracking stops when you turn it off or close the project.

## Content states

Every checked URL resolves to one content state. A few states only occur on certain platforms.

- <StatusBadge status="live" /> Loads and is publicly viewable. All platforms.
- <StatusBadge status="restricted" /> Present but access-gated, such as age-restricted, geo-blocked, or private. YouTube and X.
- <StatusBadge status="moderated" /> Taken down by platform enforcement, such as a suspended account or terminated channel. YouTube and X.
- <StatusBadge status="unavailable" /> Gone: deleted by the uploader, a 404, or expired. All platforms.
- <StatusBadge status="login_required" /> An auth wall blocked the check; the content itself may still be live. Instagram.
- <StatusBadge status="unknown" /> Loaded but nothing matched, left for a human to judge from the screenshot. All platforms.
- <StatusBadge status="error" /> The check itself failed: no load, a timeout, or a crash. All platforms.

## States by platform

Which states occur, and how reliably they are told apart, varies by platform.

### YouTube

Tells apart <StatusBadge status="live" />, <StatusBadge status="unavailable" />, <StatusBadge status="restricted" />, and <StatusBadge status="moderated" />. It reads the visible page text for removal, age, geo, private, and channel-termination markers, and confirms <StatusBadge status="live" /> from the rendered video title. Run it once through Set up browser to capture the consent cookie, otherwise an un-set-up browser is redirected to a consent page.

### Instagram

Works without login, since Instagram shows post previews to anonymous visitors. It reads <StatusBadge status="unavailable" /> from the page title and error state, and confirms <StatusBadge status="live" /> from the post caption. When a login wall is the only signal it reports <StatusBadge status="login_required" />, so log in through Set up browser for fuller coverage.

### Facebook

The coarsest of the four: in practice it only separates <StatusBadge status="live" /> from <StatusBadge status="unavailable" />. Unavailable pages load fast with a clear error, live pages render slowly. Every anonymous page embeds a login form, so there is no reliable <StatusBadge status="login_required" /> signal and undecided pages fall back to <StatusBadge status="unknown" />.

### X

Renders a tweet card only when a post is genuinely live, so a card is conclusive <StatusBadge status="live" />, checked before any takedown phrase. Run it logged in through Set up browser: logged out, X throttles even live tweets to a generic page that misreads as <StatusBadge status="unavailable" />.

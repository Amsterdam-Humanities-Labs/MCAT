---
title: Getting Started
description: Install MCAT and learn what each content state means.
---

<script>
  import { StatusBadge } from '@mcat/shared-ui';
</script>

MCAT is a desktop app for tracking how content-moderation status changes over time. There is no installer: download a build and run it.

## Installation

### macOS

[Download the latest macOS build](https://github.com/Amsterdam-Humanities-Labs/MCAT/releases/latest/download/MCAT-macOS-arm64.zip), unzip it, and move `MCAT.app` to your Applications folder. The build is for Apple Silicon. On first launch, right click the app and choose Open, since it is not notarized yet.

### Linux

There is no prebuilt Linux download yet. For now, build it from source by following the Building and installing section of the [README](https://github.com/Amsterdam-Humanities-Labs/MCAT#building--installing).

### Windows

A Windows build is on the way.

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

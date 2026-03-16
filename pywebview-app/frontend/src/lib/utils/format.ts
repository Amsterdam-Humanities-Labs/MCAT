import { colors } from '$lib/theme';

export function statusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'live':
      return colors.status.live;
    case 'removed':
      return colors.status.removed;
    case 'restricted':
    case 'age-restricted':
    case 'geo-blocked':
    case 'private':
      return colors.status.restricted;
    case 'error':
      return colors.status.error;
    default:
      return colors.text.muted;
  }
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null || seconds <= 0) return '';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.round(seconds / 60);
  if (mins < 60) return `~${mins} min`;
  const hours = Math.floor(mins / 60);
  const remainMins = mins % 60;
  return remainMins > 0 ? `~${hours}h ${remainMins}m` : `~${hours}h`;
}

export function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  const month = d.toLocaleString('en-US', { month: 'short' });
  const day = d.getDate();
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${month} ${day}, ${hours}:${minutes}`;
}

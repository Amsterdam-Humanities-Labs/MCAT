export interface NavLink {
  label: string;
  href: string;
}

export const navLinks: NavLink[] = [
  { label: 'Home', href: '/' },
  { label: 'Download', href: '/download' },
  { label: 'Documentation', href: '/docs' },
  { label: 'Policies', href: '/policies' },
  { label: 'About', href: '/about' },
];

export interface NavLink {
  label: string;
  href: string;
}

export const navLinks: NavLink[] = [
  { label: 'Home', href: '/' },
  { label: 'Documentation', href: '/docs' },
  { label: 'Policies', href: '/policies' },
];

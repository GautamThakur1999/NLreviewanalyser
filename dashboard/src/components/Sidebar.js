"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

export default function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const links = [
    { href: '/', icon: 'dashboard', label: 'Overview' },
    { href: '/barriers', icon: 'analytics', label: 'Themes & Barriers' },
    { href: '/validation', icon: 'fact_check', label: 'Hypothesis Scorecard' },
    { href: '/insights', icon: 'explore', label: 'Research Questions' },
    { href: '/segments', icon: 'groups', label: 'Segments' },
    { href: '/playground', icon: 'experiment', label: 'Live Workflow Tester' },
  ];

  return (
    <>
      {/* Mobile Toggle Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-3 left-4 z-[60] p-2 bg-surface dark:bg-surface-dim rounded-md border border-outline-variant text-on-surface hover:bg-surface-container-low transition-colors shadow-sm"
      >
        <span className="material-symbols-outlined">{isOpen ? 'close' : 'menu'}</span>
      </button>

      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <nav className={`fixed left-0 top-0 h-full w-[260px] bg-surface dark:bg-surface border-r border-outline-variant flex flex-col h-screen py-container-margin z-50 transition-transform duration-300 ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
      <div className="px-6 mb-8">
        <h1 className="font-headline-md text-headline-md font-bold text-on-surface dark:text-on-surface tracking-tight">Category Discovery</h1>
        <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Quick-Commerce Insights</p>
      </div>
      <div className="flex-1 overflow-y-auto font-body-md text-body-md">
        {links.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 px-4 py-3 transition-all duration-200 ease-in-out ${
                isActive
                  ? 'text-on-surface dark:text-on-primary-fixed-variant font-bold border-l-4 border-primary-fixed bg-surface-container-low'
                  : 'text-on-surface-variant dark:text-on-surface-variant hover:bg-surface-container-high border-l-4 border-transparent'
              }`}
            >
              <span className={`material-symbols-outlined ${isActive ? 'text-primary' : ''}`}>
                {link.icon}
              </span>
              <span>{link.label}</span>
            </Link>
          );
        })}
      </div>
      <div className="px-6 mt-auto flex items-center gap-3 pt-6 border-t border-outline-variant">
        <div className="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center overflow-hidden">
          <img alt="User Profile" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDimTqeCz7dLp6Y1l9HP45Se-iCgssUI-ftx59cp2bQAdwZZnLddVbgVaGYpewPQC9G71npDuZtwm9WxKevNjiwb3MPxLBSBv26bZMVxCEsRh6QEicfsQYCDHQvmYhwldVV3FIi8w8SH5eKHzl_pEaJ7EWok2luDXMD4-JIKXuTEee7PknB9rnHBJL0-81-97EXzZUokPfYB2b8Q5G2LeyO_g1ZAOYjCi21FqJunjG9keoms0MgN4fUF8XlZ3EvPmTrjIkNsfmWq-o" />
        </div>
        <span className="font-body-sm text-body-sm font-medium">User Profile</span>
      </div>
      </nav>
    </>
  );
}

"use client";
import React, { useState, useRef, useEffect } from 'react';
import { useFilter } from '@/context/FilterContext';

function Dropdown({ label, filterKey, options }) {
  const { filters, setFilters } = useFilter();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const currentVal = filters[filterKey];

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`whitespace-nowrap text-on-surface-variant font-body-md text-body-md px-2 xl:px-3 py-2 hover:text-primary dark:hover:text-primary-fixed transition-colors cursor-pointer active:opacity-70 rounded-md flex items-center gap-1 ${isOpen ? 'bg-primary-container/10 text-primary' : ''}`}
      >
        <span className="opacity-70">{label}:</span> 
        <span className="font-semibold text-on-surface">{currentVal}</span>
        <span className="material-symbols-outlined text-[16px]">expand_more</span>
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 left-0 w-48 bg-surface-container-lowest border border-outline-variant/30 rounded-md shadow-lg py-1 z-50">
          {options.map(option => (
            <button
              key={option}
              onClick={() => {
                setFilters(prev => ({ ...prev, [filterKey]: option }));
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-2 text-body-sm font-body-sm hover:bg-surface-container-low transition-colors ${currentVal === option ? 'text-primary font-bold bg-primary-container/5' : 'text-on-surface'}`}
            >
              {option}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Header() {
  return (
    <header className="fixed top-0 right-0 left-0 lg:left-[260px] z-30 bg-surface-bright dark:bg-surface-dim border-b border-outline-variant shadow-sm flex flex-col sm:flex-row justify-between sm:items-center h-auto sm:h-16 px-4 lg:px-gutter py-3 sm:py-0 gap-3 sm:gap-0 overflow-x-auto overflow-y-visible">
      <div className="flex items-center gap-6 pl-12 lg:pl-0">
        <div className="font-title-md sm:font-headline-md text-title-md sm:text-headline-md font-bold text-on-surface tracking-tight whitespace-nowrap">Category Discovery Insights</div>
      </div>
      <div className="flex items-center gap-2 sm:gap-4 overflow-x-auto pb-1 sm:pb-0 scrollbar-hide">
        <nav className="flex items-center gap-1 sm:gap-1">
          <Dropdown label="Source" filterKey="source" options={['All', 'Play Store', 'App Store', 'Reddit', 'Forum']} />
          <Dropdown label="Date Range" filterKey="dateRange" options={['Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'All Time']} />
          <Dropdown label="Category" filterKey="category" options={['All', 'Personal Care', 'Electronics', 'Grocery', 'Baby Care']} />
        </nav>
      </div>
    </header>
  );
}

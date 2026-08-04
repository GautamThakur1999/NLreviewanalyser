import "./globals.css";

export const metadata = {
  title: "Category Discovery Insights - Overview",
  description: "Quick-Commerce Insights",
};

import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import { FilterProvider } from "@/context/FilterContext";

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body className="font-body-md text-on-surface antialiased bg-[#F4F5F7] min-h-screen">
        <FilterProvider>
          <Sidebar />
          <Header />

          {/* Main Content Canvas */}
          <main className="ml-0 lg:ml-[260px] pt-[120px] sm:pt-[88px] min-h-screen px-4 lg:px-container-margin pb-container-margin">
            {children}
          </main>
        </FilterProvider>
      </body>
    </html>
  );
}

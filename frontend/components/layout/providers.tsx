"use client";

import { SWRConfig } from "swr";

import { TooltipProvider } from "@/components/ui/tooltip";
import { StudentProvider } from "@/lib/student-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig value={{ revalidateOnFocus: false, keepPreviousData: true, errorRetryCount: 1 }}>
      <StudentProvider>
        <TooltipProvider>{children}</TooltipProvider>
      </StudentProvider>
    </SWRConfig>
  );
}

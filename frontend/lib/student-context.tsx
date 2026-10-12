"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { mutate } from "swr";

import { api } from "@/lib/api";

export const DEMO_STUDENT = "demo_student";
const KEY = "curio.studentId";

interface Ctx {
  studentId: string;
  setStudentId: (id: string) => void;
  resetDemo: () => Promise<void>;
  refreshAll: () => void;
}

const StudentContext = createContext<Ctx>({
  studentId: DEMO_STUDENT,
  setStudentId: () => {},
  resetDemo: async () => {},
  refreshAll: () => {},
});

export function StudentProvider({ children }: { children: React.ReactNode }) {
  const [studentId, setId] = useState(DEMO_STUDENT);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(KEY);
      if (saved) setId(saved);
    } catch {
      /* storage unavailable — keep the demo student */
    }
  }, []);

  const setStudentId = useCallback((id: string) => {
    setId(id);
    try {
      localStorage.setItem(KEY, id);
    } catch {
      /* ignore */
    }
  }, []);

  const refreshAll = useCallback(() => {
    mutate(() => true, undefined, { revalidate: true });
  }, []);

  const resetDemo = useCallback(async () => {
    await api.resetDemo();
    setStudentId(DEMO_STUDENT);
    refreshAll();
  }, [refreshAll, setStudentId]);

  return <StudentContext.Provider value={{ studentId, setStudentId, resetDemo, refreshAll }}>{children}</StudentContext.Provider>;
}

export const useStudent = () => useContext(StudentContext);

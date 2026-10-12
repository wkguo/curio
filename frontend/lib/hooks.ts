"use client";

import { useSyncExternalStore } from "react";
import useSWR from "swr";

import { api, offlineStore } from "@/lib/api";
import { useStudent } from "@/lib/student-context";

export function useOffline() {
  return useSyncExternalStore(offlineStore.subscribe, offlineStore.get, () => false);
}

export function useHealth() {
  return useSWR("health", api.health, { revalidateOnFocus: false });
}

export function useStudents() {
  return useSWR("students", api.students);
}

export function useDashboard() {
  const { studentId } = useStudent();
  return useSWR(["dashboard", studentId], () => api.dashboard(studentId));
}

export function useMastery() {
  const { studentId } = useStudent();
  return useSWR(["mastery", studentId], () => api.mastery(studentId));
}

export function useTopics() {
  const { studentId } = useStudent();
  return useSWR(["topics", studentId], () => api.topics(studentId));
}

export function useTopic(topicId: string | null) {
  const { studentId } = useStudent();
  return useSWR(topicId ? ["topic", topicId, studentId] : null, () => api.topic(topicId!, studentId));
}

export function useAnalytics() {
  return useSWR("analytics", api.analytics, { refreshInterval: 15000 });
}

export function useTraces(limit = 30, studentId?: string) {
  return useSWR(["traces", limit, studentId], () => api.traces(limit, studentId), { refreshInterval: 15000 });
}

export function useTrace(id: string | null) {
  return useSWR(id ? ["trace", id] : null, () => api.trace(id!));
}

export function useQueue(status = "open") {
  return useSWR(["queue", status], () => api.queue(status), { refreshInterval: 15000 });
}

export function usePathways(topicId?: string) {
  return useSWR(["pathways", topicId], () => api.pathways(topicId));
}

export function usePrivacy() {
  const { studentId } = useStudent();
  return useSWR(["privacy", studentId], () => api.privacy(studentId));
}

export function useEvaluation() {
  return useSWR("evaluation", api.evaluation, { revalidateOnFocus: false });
}

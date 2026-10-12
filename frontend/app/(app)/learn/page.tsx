"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { LearningSession } from "@/components/learn/learning-session";
import { TopicPicker } from "@/components/learn/topic-picker";
import { useStudent } from "@/lib/student-context";

function Learn() {
  const params = useSearchParams();
  const router = useRouter();
  const { studentId } = useStudent();
  const topic = params.get("topic");

  if (!topic) return <TopicPicker onPick={(t) => router.push(`/learn?topic=${t}`)} />;
  return <LearningSession key={`${topic}-${studentId}`} topicId={topic} onExit={() => router.push("/learn")} />;
}

export default function LearnPage() {
  return (
    <Suspense>
      <Learn />
    </Suspense>
  );
}

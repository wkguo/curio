"use client";

import "@xyflow/react/dist/style.css";

import { Background, Handle, MarkerType, Position, ReactFlow, type Edge, type Node, type NodeProps } from "@xyflow/react";
import { motion } from "framer-motion";
import { Lock } from "lucide-react";
import { useMemo } from "react";

import { StatusIcon } from "@/components/shared/status-icon";
import { Emoji } from "@/components/ui/emoji";
import { Ring } from "@/components/ui/ring";
import { STATUS } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { ConceptNode } from "@/types/api";

type ConceptData = { concept: ConceptNode; selected: boolean };

function ConceptNodeView({ data }: NodeProps<Node<ConceptData>>) {
  const c = data.concept;
  const s = STATUS[c.status];
  const locked = c.status === "locked";
  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ y: -3 }}
      className={cn(
        "relative w-[210px] cursor-pointer rounded-3xl border-2 bg-white p-3 shadow-soft transition",
        data.selected ? "border-curio-400 shadow-glow" : "border-transparent",
        locked && "bg-ink-50",
      )}
      style={{ boxShadow: data.selected ? undefined : `0 0 0 2px ${s.color}33, 0 10px 24px -14px rgba(30,27,58,.25)` }}
    >
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center gap-3">
        <Ring value={c.mastery} size={52} stroke={6} color={s.color}>
          {locked ? <Lock className="h-5 w-5 text-ink-300" /> : <Emoji name={c.emoji} size={28} />}
        </Ring>
        <div className="min-w-0">
          <div className={cn("line-clamp-2 text-[14px] font-black leading-tight", locked ? "text-ink-400" : "text-ink-900")}>{c.name}</div>
          <div className={cn("mt-0.5 flex items-center gap-1 text-[11px] font-extrabold", s.text)}>
            <StatusIcon status={c.status} className="h-3.5 w-3.5" />
            {locked ? "Locked" : `${Math.round(c.mastery * 100)}% · ${s.label}`}
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </motion.div>
  );
}

const nodeTypes = { concept: ConceptNodeView };

/** Prerequisite graph (spec §12) — nodes colored by mastery state, edges animate into what you're learning. */
export function ConceptGraph({ concepts, edges, selected, onSelect }: { concepts: ConceptNode[]; edges: { source: string; target: string }[]; selected?: string; onSelect: (id: string) => void }) {
  const byId = useMemo(() => Object.fromEntries(concepts.map((c) => [c.id, c])), [concepts]);
  const nodes: Node<ConceptData>[] = useMemo(
    () =>
      concepts.map((c) => ({
        id: c.id,
        type: "concept",
        position: { x: c.position.x * 250, y: c.position.y * 118 },
        data: { concept: c, selected: c.id === selected },
      })),
    [concepts, selected],
  );
  const flowEdges: Edge[] = useMemo(
    () =>
      edges.map((e) => {
        const target = byId[e.target];
        const src = byId[e.source];
        const active = target && (target.status === "learning" || target.status === "needs_practice");
        const color = src?.status === "mastered" ? "#1FB978" : "#C9C7D8";
        return {
          id: `${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
          type: "smoothstep",
          animated: active,
          style: { stroke: color, strokeWidth: 2.5 },
          markerEnd: { type: MarkerType.ArrowClosed, color, width: 16, height: 16 },
        };
      }),
    [edges, byId],
  );

  return (
    <div className="h-[560px] w-full overflow-hidden rounded-3xl bg-gradient-to-b from-curio-50/60 to-white">
      <ReactFlow
        nodes={nodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.12, maxZoom: 1.15 }}
        nodesDraggable={false}
        nodesConnectable={false}
        panOnScroll={false}
        zoomOnScroll={false}
        minZoom={0.4}
        maxZoom={1.4}
        onNodeClick={(_, n) => onSelect(n.id)}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={22} size={1.4} color="#D6CBFF" />
      </ReactFlow>
    </div>
  );
}

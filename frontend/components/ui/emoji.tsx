/* eslint-disable @next/next/no-img-element */
import { cn } from "@/lib/utils";

/** Microsoft Fluent 3D emoji (MIT) — see public/assets/emoji/LICENSE.md. */
export function Emoji({ name, size = 32, className, alt = "" }: { name: string; size?: number; className?: string; alt?: string }) {
  return (
    <img
      src={`/assets/emoji/${name}.png`}
      alt={alt}
      width={size}
      height={size}
      draggable={false}
      className={cn("inline-block select-none object-contain", className)}
      style={{ width: size, height: size }}
      onError={(e) => {
        (e.currentTarget as HTMLImageElement).src = "/assets/emoji/sparkles.png";
      }}
    />
  );
}

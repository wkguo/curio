import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

// Chunky "lip" buttons: a solid bottom shadow that presses down on click.
const buttonVariants = cva(
  "relative inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-2xl font-extrabold tracking-tight transition-all duration-150 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-curio-200 disabled:pointer-events-none disabled:opacity-50 active:translate-y-[3px] [&_svg]:size-[1.1em] [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-curio-500 text-white shadow-[0_4px_0_0_#5631D6] hover:bg-curio-400 active:shadow-[0_1px_0_0_#5631D6]",
        mint: "bg-mint-500 text-white shadow-[0_4px_0_0_#0F7A4F] hover:bg-mint-400 active:shadow-[0_1px_0_0_#0F7A4F]",
        sun: "bg-sun-400 text-ink-900 shadow-[0_4px_0_0_#C98500] hover:bg-sun-300 active:shadow-[0_1px_0_0_#C98500]",
        coral: "bg-coral-500 text-white shadow-[0_4px_0_0_#B63A12] hover:bg-coral-400 active:shadow-[0_1px_0_0_#B63A12]",
        secondary: "border-2 border-ink-200 bg-white text-ink-700 shadow-[0_3px_0_0_#E6E4EF] hover:bg-ink-50 active:shadow-none",
        ghost: "text-ink-600 hover:bg-ink-100 active:translate-y-0",
        soft: "bg-curio-50 text-curio-700 hover:bg-curio-100 active:translate-y-0",
        link: "text-curio-600 underline-offset-4 hover:underline active:translate-y-0",
      },
      size: {
        sm: "h-9 px-3.5 text-sm",
        md: "h-11 px-5 text-[15px]",
        lg: "h-12 px-6 text-base",
        xl: "h-14 px-8 text-lg rounded-3xl",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "md" },
  },
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
});
Button.displayName = "Button";

export { buttonVariants };

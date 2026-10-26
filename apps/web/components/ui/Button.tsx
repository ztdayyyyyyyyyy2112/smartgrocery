import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
};

export default function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: ButtonProps) {
  const variantClasses: Record<ButtonVariant, string> = {
    primary:
      "bg-primary text-white hover:bg-primary-dark focus-visible:outline-primary-dark",
    secondary:
      "border border-border bg-white text-foreground hover:border-primary hover:text-primary focus-visible:outline-primary",
    ghost:
      "bg-transparent text-foreground hover:bg-primary-light hover:text-primary-dark focus-visible:outline-primary",
  };

  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus-visible:outline-4 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${variantClasses[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

import type { ReactNode } from "react";

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  type?: "button" | "submit";
  variant?: "primary" | "secondary" | "outline";
  className?: string;
  fullWidth?: boolean;
}

export function Button({
  children,
  onClick,
  disabled,
  type = "button",
  variant = "primary",
  className = "",
  fullWidth = false,
}: ButtonProps) {
  const variants = {
    primary: "bg-terracotta-500 text-cream-50 hover:bg-terracotta-600 shadow-warm",
    secondary: "bg-sage-400 text-cream-50 hover:bg-sage-500 shadow-warm",
    outline: "bg-cream-50 text-ink-800 border-2 border-sage-300 hover:border-sage-400 hover:bg-sage-100",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`btn-press card-hover rounded-2xl px-6 py-3.5 font-body text-base font-semibold
        ${variants[variant]}
        ${fullWidth ? "w-full" : ""}
        ${disabled ? "opacity-50 cursor-not-allowed hover:translate-y-0 hover:scale-100" : ""}
        ${className}`}
    >
      {children}
    </button>
  );
}

export function LoadingBreath({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-5 py-12">
      <div className="relative flex h-24 w-24 items-center justify-center">
        <div className="absolute h-20 w-20 rounded-full bg-sage-300/50 animate-breath" />
        <div className="absolute h-14 w-14 rounded-full bg-sage-400/60 animate-breath-delayed" />
        <div className="absolute h-8 w-8 rounded-full bg-sage-500/70 animate-breath" />
      </div>
      {label && (
        <p className="font-body text-base text-dustyblue-600 animate-pulse">{label}</p>
      )}
    </div>
  );
}

"use client";

type HeaderBarProps = {
  headerBorderClass: string;
};

export function HeaderBar({ headerBorderClass }: HeaderBarProps) {
  return (
    <header className={`flex items-center justify-between border-b pb-4 ${headerBorderClass}`}>
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-[#F97316] to-[#F43F5E] text-sm font-semibold text-white">
          SI
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-[#F97316]">Perseval</p>
          <p className="text-base font-semibold">Scam Intelligence</p>
        </div>
      </div>
      <span className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">One card · three states</span>
    </header>
  );
}

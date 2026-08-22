import React from "react";

/**
 * Shared page primitives for a consistent, premium layout across all pages.
 *   <PageHeader eyebrow="Договоры" title="История" subtitle="..." icon={Icon} actions={...} />
 *   <Section title="..." description="..." right={...}> ... </Section>
 */

export function PageHeader({ eyebrow, title, subtitle, icon: Icon, actions }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
      <div className="flex items-start gap-4">
        {Icon && (
          <div className="chip h-12 w-12 shrink-0">
            <Icon className="h-6 w-6 text-[#F43F5E]" strokeWidth={2} />
          </div>
        )}
        <div>
          {eyebrow && <div className="eyebrow mb-1.5">{eyebrow}</div>}
          <h1 className="font-heading text-4xl sm:text-[2.75rem] leading-none font-black tracking-tight text-gradient">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-2.5 max-w-2xl">{subtitle}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Section({ title, description, right, icon: Icon, className = "", children }) {
  return (
    <section className={`card-premium p-6 ${className}`}>
      {(title || right) && (
        <div className="flex items-start justify-between gap-4 mb-5">
          <div className="flex items-start gap-3">
            {Icon && (
              <div className="chip-muted h-9 w-9 rounded-lg flex items-center justify-center shrink-0">
                <Icon className="h-4 w-4 text-[#F43F5E]" strokeWidth={2} />
              </div>
            )}
            <div>
              {title && (
                <h2 className="font-heading text-2xl font-bold tracking-tight leading-none">
                  {title}
                </h2>
              )}
              {description && (
                <p className="text-[13px] text-muted-foreground mt-1.5 max-w-2xl">{description}</p>
              )}
            </div>
          </div>
          {right && <div className="flex items-center gap-2 shrink-0">{right}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function StatTile({ label, value, icon: Icon, hint }) {
  return (
    <div className="card-premium hover-lift p-5 overflow-hidden relative">
      <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-[#E11D48]/8 blur-2xl" />
      <div className="relative flex items-start justify-between">
        <div>
          <div className="eyebrow">{label}</div>
          <div className="font-heading text-4xl font-black tracking-tight mt-3">{value}</div>
          {hint && <div className="text-[11px] text-muted-foreground mt-1">{hint}</div>}
        </div>
        {Icon && (
          <div className="chip h-10 w-10">
            <Icon className="h-5 w-5 text-[#F43F5E]" strokeWidth={2} />
          </div>
        )}
      </div>
    </div>
  );
}

export function ActionTile({ title, description, icon: Icon, onClick, primary, testid }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testid}
      className={`card-premium hover-lift group text-left p-6 flex flex-col gap-4 h-full ${
        primary ? "ring-accent" : ""
      }`}
    >
      <div className={`h-12 w-12 rounded-xl flex items-center justify-center ${primary ? "chip" : "chip-muted"}`}>
        <Icon className="h-6 w-6 text-[#F43F5E]" strokeWidth={2} />
      </div>
      <div className="flex-1">
        <div className="font-heading text-xl font-bold tracking-tight">{title}</div>
        <p className="text-[13px] text-muted-foreground mt-1.5 leading-relaxed">{description}</p>
      </div>
      <div className="text-[12px] font-mono uppercase tracking-widest text-[#F43F5E] opacity-0 group-hover:opacity-100 transition-opacity">
        Открыть →
      </div>
    </button>
  );
}

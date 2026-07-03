export default function Header() {
  return (
    <header className="h-14 shrink-0 flex items-center justify-between px-5 border-b border-[var(--border)] bg-[var(--surface)]">
      <div className="flex items-center gap-2">
        <span className="text-lg font-extrabold tracking-tight text-[var(--foreground)]">
          Valor<span className="text-[var(--accent)]">Real</span>
        </span>
        <span className="hidden sm:inline text-xs font-medium text-[var(--muted)] ml-1">
          Preços reais de imóveis no Brasil
        </span>
      </div>
      <nav className="flex items-center gap-4 text-sm text-[var(--muted)]">
        <a href="/api/v1/transactions" className="hover:text-[var(--accent)] transition-colors font-mono text-xs">
          API
        </a>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-[var(--accent)] transition-colors"
        >
          GitHub
        </a>
      </nav>
    </header>
  );
}

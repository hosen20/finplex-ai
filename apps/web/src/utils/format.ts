export function formatCurrency(value?: number | null, currency = "USD"): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}

export function formatDate(value?: string | null): string {
  if (!value) {
    return "—";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric"
  });
}

export function humanize(value?: string | null): string {
  if (!value) {
    return "—";
  }

  return value
    .replace(/_/g, " ")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function riskLabel(value?: string): string {
  if (!value) {
    return "Unknown";
  }

  return humanize(value);
}

export function clampPercentage(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

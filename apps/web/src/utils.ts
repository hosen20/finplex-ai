export function normalizeStatus(value: string): string {
  return value.split("_").join(" ").toLowerCase();
}

export function formatDate(value?: string | null): string {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function asMoney(value: unknown): string {
  if (typeof value !== "string" && typeof value !== "number") {
    return "Not available";
  }

  const numberValue = Number(value);

  if (Number.isNaN(numberValue)) {
    return String(value);
  }

  return new Intl.NumberFormat("en", {
    style: "currency",
    currency: "USD",
  }).format(numberValue);
}

export function riskClass(value: string): string {
  const normalized = value.toLowerCase();

  if (normalized.includes("high")) {
    return "danger";
  }

  if (normalized.includes("medium")) {
    return "warning";
  }

  return "success";
}

export const WEEKDAYS = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"];
export const GREG_MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
  "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
];
export const MONTH_NAMES = [
  "Muharram", "Safar", "Rabiul Awal", "Rabiul Akhir",
  "Jumadil Awal", "Jumadil Akhir", "Rajab", "Sya'ban",
  "Ramadhan", "Syawal", "Dzulqa'dah", "Dzulhijjah",
];

export const EVENT_SHORT = {
  "1_muharram": "1 Muharram",
  maulid_nabi: "Maulid",
  awal_ramadan: "1 Ramadhan",
  idul_fitri: "1 Syawal",
  idul_adha: "10 Dzulhijjah",
};

const STATUS_OK_ID =
  "Data kalender MABIMS resmi dari Kemenag saat ini mencakup: {cov} Di luar cakupan ini, menggunakan perhitungan Neo MABIMS.";
const STATUS_OK_ID_PLAIN =
  "Data kalender MABIMS resmi dari Kemenag saat ini mencakup: {cov}";
const STATUS_OK_EN =
  "Official MABIMS calendar data from Kemenag currently covers: {cov} Outside this range, Neo MABIMS computation is used.";
const STATUS_OK_EN_PLAIN =
  "Official MABIMS calendar data from Kemenag currently covers: {cov}";
const STATUS_WARN_ID =
  "API tidak dapat diakses dari sini — mungkin belum di-deploy.";
const STATUS_WARN_EN = "API unreachable from here — it may not be deployed yet.";

const TEMPLATES = {
  id: { ok: STATUS_OK_ID, okPlain: STATUS_OK_ID_PLAIN, warn: STATUS_WARN_ID },
  en: { ok: STATUS_OK_EN, okPlain: STATUS_OK_EN_PLAIN, warn: STATUS_WARN_EN },
};

export async function fetchStatus(apiBase, statusEl, locale = "id") {
  const t = TEMPLATES[locale] ?? TEMPLATES.id;
  try {
    const res = await fetch(`${apiBase}/api/v1/meta`);
    if (!res.ok) throw new Error(res.status);
    const meta = await res.json();
    statusEl.className = "pg-status pg-ok";
    statusEl.textContent =
      (meta.computed_active ? t.ok : t.okPlain).replace(
        "{cov}",
        `${meta.coverage.first} → ${meta.coverage.last}`
      );
  } catch {
    statusEl.className = "pg-status pg-warn";
    statusEl.textContent = t.warn;
  }
}

export async function fetchToday(apiBase) {
  const res = await fetch(`${apiBase}/api/v1/today`);
  if (!res.ok) throw new Error(`today failed: ${res.status}`);
  return res.json();
}

export async function fetchMonth(apiBase, year, month) {
  const params = new URLSearchParams({ year: String(year), month: String(month), calendar: "hijri" });
  const res = await fetch(`${apiBase}/api/v1/month?${params}`);
  if (!res.ok) return null;
  return res.json();
}

export async function fetchYear(apiBase, year) {
  const params = new URLSearchParams({ year: String(year), calendar: "hijri" });
  const res = await fetch(`${apiBase}/api/v1/year?${params}`);
  if (!res.ok) return null;
  return res.json();
}

export async function fetchHijriEvents(apiBase, year) {
  const params = new URLSearchParams({ year: String(year), calendar: "hijri" });
  try {
    const res = await fetch(`${apiBase}/api/v1/events?${params}`);
    if (!res.ok) return [];
    const body = await res.json();
    return body.events ?? [];
  } catch {
    return [];
  }
}

export function weekdayIndex(iso) {
  return (new Date(`${iso}T00:00:00`).getDay() + 6) % 7;
}

export function buildWall(wallEl, year, monthsByMonth, events, todayHijri, config) {
  const { weekdays, gregMonths, hijriMonths, eventShortNames } = config;
  const eventsByHijri = new Map(
    (events ?? []).map((e) => [e.hijri, eventShortNames[e.event] ?? e.name])
  );

  const daysByMonth = new Map();
  for (const mt of monthsByMonth.keys()) {
    for (const item of monthsByMonth.get(mt)) {
      const key = item.hijri.slice(0, 7);
      if (!daysByMonth.has(key)) daysByMonth.set(key, []);
      daysByMonth.get(key).push(item);
    }
  }

  let frag = "";
  for (let m = 1; m <= 12; m++) {
    const key = `${year}-${String(m).padStart(2, "0")}`;
    const days = daysByMonth.get(key) ?? [];
    let headCells = "";
    for (let i = 0; i < 7; i++) {
      const fri = i === 4;
      headCells += `<span class="kal-dow${fri ? " is-fri" : ""}">${weekdays[i]}</span>`;
    }

    let cells = "";
    const monthEvents = [];
    let leading = days.length ? weekdayIndex(days[0].gregorian) : 0;
    for (let i = 0; i < leading; i++) cells += `<div class="kal-cell is-empty"></div>`;

    for (const item of days) {
      const hijriDay = Number(item.hijri.slice(8, 10));
      const greg = item.gregorian;
      const [, gm, gd] = greg.split("-").map(Number);
      const isFri = weekdayIndex(greg) === 4;
      const isToday = item.hijri === todayHijri;
      const ev = eventsByHijri.get(item.hijri);
      if (ev) monthEvents.push(ev);
      cells += `<div class="kal-cell${isFri ? " is-fri" : ""}${isToday ? " is-today" : ""}${ev ? " has-event" : ""}">` +
        `<span class="kal-day">${hijriDay}</span>` +
        `<span class="kal-greg">${gd} ${gregMonths[gm - 1]}</span>` +
        `</div>`;
    }

    let filled = leading + days.length;
    let total = Math.ceil(filled / 7) * 7;
    for (let i = filled; i < total; i++) {
      cells += `<div class="kal-cell is-empty"></div>`;
    }

    let eventsFooter = "";
    if (monthEvents.length) {
      eventsFooter = `<div class="kal-events">${monthEvents.map((e) => `<span class="kal-ev-badge">${e}</span>`).join("")}</div>`;
    }

    frag += `<section class="kal-card">` +
      `<header class="kal-card-head"><span class="kal-mnum">${m}</span><h3 class="kal-mname">${hijriMonths[m - 1]} <span class="kal-myear">${year}</span></h3></header>` +
      `<div class="kal-week">${headCells}</div>` +
      `<div class="kal-grid">${cells}</div>` +
      eventsFooter +
      `</section>`;
  }

  wallEl.innerHTML = frag;
}
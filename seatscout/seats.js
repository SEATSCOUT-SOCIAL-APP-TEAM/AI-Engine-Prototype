// seats.js: SeatScout's seat rules as a small, pure state machine.
//
//   free  --(a person stays on the seat for `confirm` ms)--------------------> taken   (the clock starts)
//   taken --(nobody on the seat for `absence` ms)-----------------------------> away    (the clock keeps running)
//   away  --(the person is back)----------------------------------------------> taken   (same clock)
//   away  --(nothing left behind, away for `grace` ms)------------------------> free    (the clock resets)
//   away  --(belongings left behind, away for `limit` ms)---------------------> check   (staff are asked to look)
//   check --(the person is back)----------------------------------------------> taken
//   check --(staff clear the seat, or the belongings are gone for `grace`)----> free
//
// No DOM, no detector: feed it observations and a clock, and it returns events.

export const DEFAULT_RULES = { confirm: 1000, absence: 1500, grace: 8000, limit: 20000 };

export function createSeat(id, zone) {
  return { id, zone, state: 'free', since: null, awayAt: null, personSince: null, lastPerson: null, belongings: false, hidden: false };
}

// obs = { person: boolean, belongings: boolean }; returns a list of events
export function updateSeat(seat, obs, now, rules = DEFAULT_RULES) {
  const ev = [], say = (type, text) => ev.push({ type, seat: seat.id, text, at: now });
  if (obs.person) { seat.lastPerson = now; if (seat.personSince === null) seat.personSince = now }
  else seat.personSince = null;
  seat.belongings = !!obs.belongings;
  const awayFor = seat.awayAt === null ? 0 : now - seat.awayAt;
  switch (seat.state) {
    case 'free':
      if (obs.person && now - seat.personSince >= rules.confirm) { seat.state = 'taken'; seat.since = seat.personSince; say('taken', 'A guest sat down. Taken, the clock starts.') }
      break;
    case 'taken':
      if (!obs.person && seat.lastPerson !== null && now - seat.lastPerson >= rules.absence) {
        seat.state = 'away'; seat.awayAt = seat.lastPerson;
        say('away', seat.belongings ? 'The guest stepped away and left belongings. Away, the seat is held.' : 'The guest stepped away. Away, the grace period starts.');
      }
      break;
    case 'away':
    case 'check':
      if (obs.person) { const was = seat.state; seat.state = 'taken'; seat.awayAt = null; say('back', was === 'check' ? 'The guest is back. Taken again, the staff check is cancelled.' : 'The guest is back. Taken, on the same clock.'); break }
      if (!seat.belongings && awayFor >= rules.grace) { seat.state = 'free'; seat.since = null; seat.awayAt = null; say('free', 'Away past the grace period with nothing left. Free, the clock resets.'); break }
      if (seat.state === 'away' && seat.belongings && awayFor >= rules.limit) { seat.state = 'check'; say('check', 'Away too long with belongings left. Staff are asked to check this seat.') }
      break;
  }
  return ev;
}

export function clearSeat(seat, now) {
  seat.state = 'free'; seat.since = null; seat.awayAt = null; seat.personSince = null;
  return [{ type: 'free', seat: seat.id, text: 'Staff checked and cleared the seat. Free.', at: now }];
}

// how long the current guest has had the seat, in ms (0 when free)
export const stayed = (seat, now) => seat.since === null ? 0 : now - seat.since;
export const away = (seat, now) => seat.awayAt === null ? 0 : now - seat.awayAt;

// Which detections belong to a zone. Zones and boxes are in 0..1 video coordinates.
const inter = (a, b) => Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) * Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
export function observe(zone, dets) {
  let person = false, belongings = false;
  for (const d of dets) {
    const i = inter(zone, d);
    if (d.kind === 'person') { if (i / (zone.w * zone.h) >= 0.25 || i / (d.w * d.h) >= 0.5) person = true }
    else if (i / (d.w * d.h) >= 0.5) belongings = true;
  }
  return { person, belongings };
}

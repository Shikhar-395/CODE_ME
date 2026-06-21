import assert from 'node:assert/strict';
import test from 'node:test';

import {
  formatCountdown,
  getRemainingSeconds,
  getServerOffsetMs,
} from './contestClock.ts';

test('formats contest time with stable hours, minutes, and seconds', () => {
  assert.equal(formatCountdown(0), '00:00:00');
  assert.equal(formatCountdown(65), '00:01:05');
  assert.equal(formatCountdown(3_661), '01:01:01');
});

test('reconciles the countdown against server time after a refresh', () => {
  const clientNow = Date.parse('2026-06-21T10:00:00.000Z');
  const offset = getServerOffsetMs('2026-06-21T10:00:05.000Z', clientNow);
  const remaining = getRemainingSeconds(
    '2026-06-21T10:10:05.000Z',
    offset,
    clientNow,
  );
  assert.equal(offset, 5_000);
  assert.equal(remaining, 600);
});

test('clamps an expired contest to zero', () => {
  const now = Date.parse('2026-06-21T10:10:06.000Z');
  assert.equal(
    getRemainingSeconds('2026-06-21T10:10:05.000Z', 0, now),
    0,
  );
});

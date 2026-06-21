import { useEffect, useMemo, useState } from 'react';
import type { Attempt } from './api';
import {
  formatCountdown,
  getRemainingSeconds,
  getServerOffsetMs,
} from './contestClock';

export { formatCountdown, getRemainingSeconds, getServerOffsetMs } from './contestClock';

export const useContestCountdown = (
  attempt: Attempt | null | undefined,
  onExpire?: () => void,
) => {
  const serverOffsetMs = useMemo(
    () => attempt ? getServerOffsetMs(attempt.server_time) : 0,
    [attempt],
  );
  const [remaining, setRemaining] = useState(() =>
    attempt ? getRemainingSeconds(attempt.expires_at, serverOffsetMs) : 0
  );

  useEffect(() => {
    if (!attempt || attempt.status !== 'active') {
      return;
    }

    let expired = false;
    const update = () => {
      const next = getRemainingSeconds(attempt.expires_at, serverOffsetMs);
      setRemaining(next);
      if (next === 0 && !expired) {
        expired = true;
        onExpire?.();
      }
    };
    update();
    const interval = window.setInterval(update, 1000);
    return () => window.clearInterval(interval);
  }, [attempt, onExpire, serverOffsetMs]);

  return {
    remaining: attempt?.status === 'active' ? remaining : 0,
    formatted: formatCountdown(attempt?.status === 'active' ? remaining : 0),
  };
};

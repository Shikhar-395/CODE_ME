export const getServerOffsetMs = (serverTime: string, clientNow = Date.now()) =>
  new Date(serverTime).getTime() - clientNow;

export const getRemainingSeconds = (
  expiresAt: string,
  serverOffsetMs = 0,
  clientNow = Date.now(),
) => Math.max(
  0,
  Math.ceil((new Date(expiresAt).getTime() - (clientNow + serverOffsetMs)) / 1000),
);

export const formatCountdown = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remaining = seconds % 60;
  return [hours, minutes, remaining]
    .map((value) => value.toString().padStart(2, '0'))
    .join(':');
};

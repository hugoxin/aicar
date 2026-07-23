export function formatTime(totalSeconds) {
  const value = Math.max(0, Math.round(totalSeconds));
  const minutes = Math.floor(value / 60);
  const seconds = value % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function stateStartTimes(points) {
  const starts = [];
  let previous = null;
  points.forEach((point) => {
    if (point.state_id !== previous) {
      starts.push({ stateId: point.state_id, time: point.relative_time_s });
      previous = point.state_id;
    }
  });
  return starts;
}

export function adjacentStateTime(starts, currentTime, direction) {
  if (direction < 0) {
    const previous = [...starts].reverse().find((item) => item.time < currentTime - 0.05);
    return previous?.time ?? 0;
  }
  const next = starts.find((item) => item.time > currentTime + 0.05);
  return next?.time ?? starts.at(-1)?.time ?? 0;
}

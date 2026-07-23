export function createPlaybackController({ duration, defaultSpeed = 1, loop = false }) {
  let time = 0;
  let speed = defaultSpeed;
  let playing = false;
  let shouldLoop = loop;

  function update(deltaSeconds) {
    if (!playing) return false;
    time += deltaSeconds * speed;
    if (time >= duration) {
      if (shouldLoop) time %= duration;
      else {
        time = duration;
        playing = false;
      }
    }
    return true;
  }

  return {
    update,
    play() {
      if (time >= duration) time = 0;
      playing = true;
    },
    pause() {
      playing = false;
    },
    reset() {
      time = 0;
      playing = false;
    },
    seek(nextTime) {
      time = Math.max(0, Math.min(duration, nextTime));
    },
    setSpeed(nextSpeed) {
      speed = Number(nextSpeed);
    },
    setLoop(nextLoop) {
      shouldLoop = Boolean(nextLoop);
    },
    get time() {
      return time;
    },
    get playing() {
      return playing;
    },
    get speed() {
      return speed;
    },
  };
}

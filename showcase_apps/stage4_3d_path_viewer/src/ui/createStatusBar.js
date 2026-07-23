export function createStatusBar(profile, handlers) {
  const speedSelect = document.getElementById("speed-select");
  profile.available_playback_speeds.forEach((speed) => {
    const option = document.createElement("option");
    option.value = String(speed);
    option.textContent = `${speed}×`;
    option.selected = speed === profile.default_playback_speed;
    speedSelect.appendChild(option);
  });

  document.getElementById("play-button").addEventListener("click", handlers.play);
  document.getElementById("pause-button").addEventListener("click", handlers.pause);
  document.getElementById("reset-button").addEventListener("click", handlers.reset);
  document.getElementById("previous-state-button").addEventListener("click", handlers.previousState);
  document.getElementById("next-state-button").addEventListener("click", handlers.nextState);
  speedSelect.addEventListener("change", () => handlers.speed(Number(speedSelect.value)));

  const loopToggle = document.getElementById("loop-toggle");
  loopToggle.checked = profile.loop_playback;
  loopToggle.addEventListener("change", () => handlers.loop(loopToggle.checked));

  const slider = document.getElementById("progress-slider");
  slider.addEventListener("input", () => handlers.seek(Number(slider.value) / 1000));
  return {
    update(progress) {
      slider.value = String(Math.round(progress * 1000));
    },
  };
}

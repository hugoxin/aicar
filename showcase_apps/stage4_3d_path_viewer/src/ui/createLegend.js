import { pathColor } from "../config/colors.js";
import { stateLabel } from "../config/labels.js";

export function createLegend(container, states, onToggle) {
  const entries = states
    .filter((state) => state.state_id !== "dwell")
    .map((state) => ({
      id: state.state_id,
      label: state.label_zh || stateLabel(state.state_id),
      color: state.color || pathColor(state.state_id),
    }));
  entries.push({ id: "transition", label: "状态切换", color: pathColor("transition", true) });

  entries.forEach((entry) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "legend-item active";
    button.dataset.state = entry.id;
    button.innerHTML = `<span class="legend-swatch" style="--swatch:${entry.color}"></span><span>${entry.label}</span>`;
    button.addEventListener("click", () => {
      button.classList.toggle("active");
      const visible = button.classList.contains("active");
      button.setAttribute("aria-pressed", String(visible));
      onToggle(entry.id, visible);
    });
    button.setAttribute("aria-pressed", "true");
    container.appendChild(button);
  });
}

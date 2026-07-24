function toggles(profile) {
  return [
    ["vehicle", "显示车体", true],
    ["fullPath", "完整路径", profile.show_full_path],
    ["executedPath", "已执行路径", profile.show_executed_path],
    ["trail", "扫描尾迹", profile.show_trail],
    ["focusCurrentState", "聚焦当前状态", profile.focus_current_state_default],
    ["auxiliaryPaths", "显示辅助连接线", profile.show_auxiliary_paths_default],
    ["axes", "坐标轴", profile.show_axes],
    ["grid", "地面网格", profile.show_grid],
    ["pointLabel", "点位标签", profile.show_point_label],
    ["lightMode", "浅色背景", false],
  ];
}

export function createControlPanel(container, profile, handlers) {
  toggles(profile).forEach(([key, label, initial]) => {
    const wrapper = document.createElement("label");
    wrapper.className = "switch-control";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.dataset.control = key;
    input.checked = initial;
    input.addEventListener("change", () => handlers.onToggle?.(key, input.checked));
    const text = document.createElement("span");
    text.textContent = label;
    wrapper.append(input, text);
    container.appendChild(wrapper);
  });

  const modeWrapper = document.createElement("label");
  modeWrapper.className = "select-control";
  const modeText = document.createElement("span");
  modeText.textContent = "车体模式";
  const select = document.createElement("select");
  select.id = "vehicle-mode-select";
  select.setAttribute("aria-label", "车体显示模式");
  [
    ["solid-wireframe", "实体+线框"],
    ["solid", "半透明实体"],
    ["wireframe", "线框"],
  ].forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  });
  select.addEventListener("change", () => {
    handlers.onMode?.(select.value);
    document.getElementById("display-mode-label").textContent = select.selectedOptions[0].text;
  });
  modeWrapper.append(modeText, select);
  container.appendChild(modeWrapper);

  const explanation = document.createElement("p");
  explanation.className = "control-explanation";
  explanation.textContent =
    "辅助连接线表示不同扫描区域之间的移动，不代表持续喷洗。";
  container.appendChild(explanation);
}

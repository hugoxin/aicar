const TOGGLES = [
  ["vehicle", "显示车体", true],
  ["fullPath", "完整路径", true],
  ["executedPath", "已执行路径", true],
  ["trail", "扫描尾迹", true],
  ["axes", "坐标轴", false],
  ["grid", "地面网格", true],
  ["pointLabel", "点位标签", true],
  ["lightMode", "浅色背景", false],
];

export function createControlPanel(container, handlers) {
  TOGGLES.forEach(([key, label, initial]) => {
    const wrapper = document.createElement("label");
    wrapper.className = "switch-control";
    const input = document.createElement("input");
    input.type = "checkbox";
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
}

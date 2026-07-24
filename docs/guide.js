(() => {
  "use strict";

  const isChinese = document.documentElement.lang.toLowerCase().startsWith("zh");
  const labels = isChinese
    ? { idle: "复制", success: "已复制", failure: "复制失败" }
    : { idle: "Copy", success: "Copied", failure: "Copy failed" };

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) {
      throw new Error("copy command was rejected");
    }
  }

  document.querySelectorAll("pre > code").forEach((code, index) => {
    const pre = code.parentElement;
    pre.classList.add("copy-ready");

    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-code";
    button.textContent = labels.idle;
    button.setAttribute("aria-label", `${labels.idle} ${index + 1}`);
    button.setAttribute("aria-live", "polite");

    let resetTimer;
    button.addEventListener("click", async () => {
      window.clearTimeout(resetTimer);
      try {
        await copyText(code.textContent);
        button.textContent = labels.success;
        button.classList.remove("copy-failed");
      } catch {
        button.textContent = labels.failure;
        button.classList.add("copy-failed");
      }
      resetTimer = window.setTimeout(() => {
        button.textContent = labels.idle;
        button.classList.remove("copy-failed");
      }, 1800);
    });

    pre.appendChild(button);
  });
})();

(() => {
  "use strict";

  const root = document.querySelector("[data-interview-demo]");
  if (!root) return;

  const steps = Array.from(root.querySelectorAll("[data-demo-step]"));
  const progressItems = Array.from(root.querySelectorAll("[data-progress-step]"));
  const counter = root.querySelector("[data-step-counter]");
  const announcer = root.querySelector("[data-demo-announcer]");
  const back = root.querySelector('[data-demo-action="back"]');
  const next = root.querySelector('[data-demo-action="next"]');
  const restart = root.querySelector('[data-demo-action="restart"]');
  let current = 0;

  const render = (focusHeading = false) => {
    steps.forEach((step, index) => {
      const active = index === current;
      step.hidden = !active;
      step.setAttribute("aria-hidden", String(!active));
    });

    progressItems.forEach((item, index) => {
      item.classList.toggle("is-complete", index < current);
      if (index === current) item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    });

    counter.textContent = String(current + 1) + " / " + String(steps.length);
    back.disabled = current === 0;
    next.disabled = current === steps.length - 1;
    announcer.textContent = steps[current].dataset.announcement || "";

    if (focusHeading) {
      const heading = steps[current].querySelector("h2");
      if (heading) {
        heading.setAttribute("tabindex", "-1");
        heading.focus();
      }
    }
  };

  back.addEventListener("click", () => {
    if (current > 0) {
      current -= 1;
      render(true);
    }
  });

  next.addEventListener("click", () => {
    if (current < steps.length - 1) {
      current += 1;
      render(true);
    }
  });

  restart.addEventListener("click", () => {
    current = 0;
    render(true);
  });

  render();
})();

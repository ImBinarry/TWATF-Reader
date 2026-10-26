(() => {
  const root = document.querySelector(".developer-carousel");
  if (!root) return;
  const cards = [...root.querySelectorAll("[data-profile]")];
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  let current = 0,
    paused = reducedMotion.matches,
    timer;
  function show(index) {
    current = index;
    cards.forEach((card, i) => (card.hidden = i !== current));
  }
  function schedule() {
    clearInterval(timer);
    if (
      !paused &&
      !document.hidden &&
      !root.matches(":hover") &&
      !root.contains(document.activeElement)
    ) {
      timer = setInterval(() => show((current + 1) % cards.length), 4000);
    }
  }
  root.addEventListener("mouseenter", schedule);
  root.addEventListener("mouseleave", schedule);
  root.addEventListener("focusin", schedule);
  root.addEventListener("focusout", () => setTimeout(schedule, 0));
  document.addEventListener("visibilitychange", schedule);
  reducedMotion.addEventListener("change", () => {
    paused = reducedMotion.matches;
    schedule();
  });
  schedule();
})();

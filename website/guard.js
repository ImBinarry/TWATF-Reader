// A lightweight deterrent only. Browser menus and external inspection remain available.
addEventListener("contextmenu", (event) => {
  if (!event.target.closest("input,textarea")) event.preventDefault();
});
addEventListener(
  "keydown",
  (event) => {
    const key = event.key.toLowerCase();
    const inspect =
      key === "f12" ||
      (event.ctrlKey && event.shiftKey && ["i", "j", "c"].includes(key)) ||
      (event.metaKey && event.altKey && ["i", "j", "c"].includes(key)) ||
      ((event.ctrlKey || event.metaKey) && key === "u");
    if (inspect) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  },
  true,
);

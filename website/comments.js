// Giscus uses a stable edition/chapter key, never the shared index.html pathname.
(() => {
  let active = null,
    activeEdition = null,
    started = false;
  const theme = () =>
    ["light", "sepia"].includes(document.body.dataset.theme) ? "light" : "dark";
  const mount = () => document.getElementById("giscus-thread");
  function sync() {
    const frame = mount()?.querySelector("iframe.giscus-frame");
    const category = window.READER_CONFIG?.giscus?.categories?.[activeEdition];
    if (frame && active && category?.name && category?.id)
      frame.contentWindow.postMessage(
        {
          giscus: {
            setConfig: {
              term: active,
              theme: theme(),
              category: category.name,
              categoryId: category.id,
            },
          },
        },
        "https://giscus.app",
      );
  }
  window.readerComments = {
    clear() {
      document.getElementById("comments").hidden = true;
      active = null;
      activeEdition = null;
    },
    show(edition, number) {
      active = `twatf-${edition}-chapter-${number}`;
      activeEdition = edition;
      const section = document.getElementById("comments"),
        status = document.getElementById("comments-status");
      section.hidden = false;
      const c = window.READER_CONFIG?.giscus;
      const category = c?.categories?.[edition];
      if (!c || !c.repo || !c.repoId || !category?.name || !category?.id) {
        status.textContent = "Comments are coming soon.";
        return;
      }
      status.textContent =
        "Comments and reactions are powered by GitHub Discussions. Sign in with GitHub to join in.";
      if (started) {
        sync();
        return;
      }
      started = true;
      const observer = new MutationObserver(() => {
        const frame = mount().querySelector("iframe.giscus-frame");
        if (frame) {
          frame.title = "Chapter comments";
          frame.addEventListener("load", sync);
          sync();
          observer.disconnect();
        }
      });
      observer.observe(mount(), { childList: true, subtree: true });
      const script = document.createElement("script");
      script.src = "https://giscus.app/client.js";
      script.async = true;
      script.crossOrigin = "anonymous";
      const attrs = {
        repo: c.repo,
        "repo-id": c.repoId,
        category: category.name,
        "category-id": category.id,
        mapping: "specific",
        term: active,
        strict: "1",
        "reactions-enabled": "1",
        "emit-metadata": "0",
        "input-position": "top",
        theme: theme(),
        lang: "en",
        loading: "lazy",
      };
      Object.entries(attrs).forEach(([k, v]) =>
        script.setAttribute("data-" + k, v),
      );
      script.onerror = () => {
        status.textContent =
          "Comments could not load. Please check your connection and reload to try again.";
        observer.disconnect();
      };
      mount().append(script);
    },
    theme: sync,
  };
})();

// Fades the page scrollbar out when idle; without this script it stays visible.
(() => {
  const root = document.documentElement;
  const EDGE_PX = 24;
  const IDLE_MS = 1000;
  let timer;
  let nearEdge = false;

  const hide = () => root.classList.remove("sb-on");
  const show = () => {
    root.classList.add("sb-on");
    clearTimeout(timer);
    if (!nearEdge) timer = setTimeout(hide, IDLE_MS);
  };
  const setNearEdge = (near) => {
    if (near === nearEdge) return;
    nearEdge = near;
    show();
  };

  root.classList.add("sb-auto");
  show();
  addEventListener("scroll", show, { passive: true });
  addEventListener(
    "pointermove",
    (event) => setNearEdge(event.pointerType === "mouse" && event.clientX >= root.clientWidth - EDGE_PX),
    { passive: true }
  );
  root.addEventListener("pointerleave", () => setNearEdge(false));
})();

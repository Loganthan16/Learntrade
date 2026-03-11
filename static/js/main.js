/**
 * TradeLog — main.js
 * Small utilities that run on every page.
 */

// ── Market Status Indicator ────────────────────────────────────────────────
// NSE is open Mon-Fri 09:15 – 15:30 IST (UTC+5:30)
function updateMarketStatus() {
  const now    = new Date();
  const ist    = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" }));
  const day    = ist.getDay();    // 0=Sun, 6=Sat
  const hour   = ist.getHours();
  const minute = ist.getMinutes();
  const mins   = hour * 60 + minute;

  const isWeekday = day >= 1 && day <= 5;
  const inSession = mins >= 9 * 60 + 15 && mins <= 15 * 60 + 30;
  const isOpen    = isWeekday && inSession;

  const dot  = document.querySelector(".status-dot");
  const text = document.querySelector(".status-text");

  if (!dot || !text) return;

  if (isOpen) {
    dot.classList.add("open");
    text.textContent = "Market Open 🟢";
  } else {
    dot.classList.remove("open");
    const nextOpen = isWeekday && mins < 9 * 60 + 15
      ? "Opens at 9:15 AM"
      : "Opens Monday";
    text.textContent = `Market Closed`;
  }
}

updateMarketStatus();
setInterval(updateMarketStatus, 60_000);   // refresh every minute


// ── Auto-dismiss flash messages ─────────────────────────────────────────────
setTimeout(() => {
  document.querySelectorAll(".flash").forEach(el => {
    el.style.transition = "opacity 0.4s, transform 0.4s";
    el.style.opacity    = "0";
    el.style.transform  = "translateY(-6px)";
    setTimeout(() => el.remove(), 400);
  });
}, 4000);


// ── Number formatting helper (for inline use) ───────────────────────────────
window.formatINR = (num) => {
  const abs = Math.abs(num).toFixed(2);
  return (num >= 0 ? "+" : "-") + "₹" + abs;
};

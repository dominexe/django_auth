(() => {
    "use strict";
    const refresh = document.getElementById("dashboard-refresh");
    if (!refresh) return;

    refresh.addEventListener("click", () => window.location.reload());
})();
(function () {
  const STORAGE_KEY = "demobuy-theme";
  const toggleBtn = document.getElementById("theme-toggle");
  const body = document.body;

  // Function to apply the theme to the body and update the button icon
  function applyTheme(theme) {
    if (theme === "dark") {
      body.classList.add("dark");
      if (toggleBtn) toggleBtn.textContent = "☀️";
    } else {
      body.classList.remove("dark");
      if (toggleBtn) toggleBtn.textContent = "🌙";
    }
  }

  // Determine initial theme on load
  const saved = localStorage.getItem(STORAGE_KEY);
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(saved || (prefersDark ? "dark" : "light"));

  // Attach event listener for the toggle button
  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      const isDark = body.classList.contains("dark");
      const newTheme = isDark ? "light" : "dark";
      
      applyTheme(newTheme);
      localStorage.setItem(STORAGE_KEY, newTheme);
    });
  }
})();
(function () {
  const root = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const saved = localStorage.getItem('theme');
  const navLinks = Array.from(document.querySelectorAll('[data-nav]'));

  // Initialize theme
  if (saved === 'light') {
    root.setAttribute('data-theme', 'light');
    if (themeToggle) themeToggle.textContent = '🌚';
  } else {
    root.removeAttribute('data-theme');
    if (themeToggle) themeToggle.textContent = '🌙';
  }

  // Toggle theme
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      const isLight = root.getAttribute('data-theme') === 'light';
      if (isLight) {
        root.removeAttribute('data-theme');
        localStorage.setItem('theme', 'dark');
        themeToggle.textContent = '🌙';
      } else {
        root.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        themeToggle.textContent = '🌚';
      }
    });
  }

  // Current year in footer
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear().toString();

  // Scroll spy
  const sections = navLinks.map(function (a) {
    var id = a.getAttribute('href');
    try { return document.querySelector(id); } catch (_) { return null; }
  }).filter(Boolean);

  var ticking = false;
  function onScroll() {
    if (!ticking) {
      window.requestAnimationFrame(function () {
        var fromTop = window.scrollY + 120; // offset for highlight
        var currentIndex = -1;
        for (var i = 0; i < sections.length; i++) {
          var sec = sections[i];
          if (sec && sec.offsetTop <= fromTop) currentIndex = i;
        }
        navLinks.forEach(function (a, idx) {
          if (idx === currentIndex) a.classList.add('active');
          else a.classList.remove('active');
        });
        ticking = false;
      });
      ticking = true;
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();


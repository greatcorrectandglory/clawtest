(function () {
  const links = Array.from(document.querySelectorAll('.top-nav a[href^="#"]'));
  const sections = links
    .map((link) => document.querySelector(link.getAttribute('href')))
    .filter(Boolean);

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((link) => {
        link.toggleAttribute('aria-current', link.getAttribute('href') === `#${entry.target.id}`);
      });
    });
  }, { rootMargin: '-30% 0px -55% 0px', threshold: 0.01 });

  sections.forEach((section) => observer.observe(section));
})();

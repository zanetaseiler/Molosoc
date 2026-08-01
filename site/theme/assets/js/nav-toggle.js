/*
  Molosoc — shared mobile hamburger nav toggle.

  Works for both headers on the site: .molosoc-site-header (every page
  except the homepage, header.php) and .molosoc-home-header (front-page.php
  only) — same markup pattern (a button.molosoc-nav-toggle right next to
  wp_nav_menu()'s output), same open/close behavior, just different colors
  (see components.css / homepage.css). Only one header is ever present on
  a given page, so this just looks for whichever one exists.

  No animation library — a class toggle plus the CSS transitions already
  defined on the nav panel (max-height) and the toggle icon (bar rotation).
*/
(function () {
  "use strict";

  var toggle = document.querySelector(".molosoc-nav-toggle");
  if (!toggle) return;

  var header = toggle.closest(".molosoc-site-header, .molosoc-home-header");
  if (!header) return;

  function closeNav() {
    header.classList.remove("is-nav-open");
    toggle.setAttribute("aria-expanded", "false");
  }

  function openNav() {
    header.classList.add("is-nav-open");
    toggle.setAttribute("aria-expanded", "true");
  }

  toggle.addEventListener("click", function () {
    if (header.classList.contains("is-nav-open")) {
      closeNav();
    } else {
      openNav();
    }
  });

  document.addEventListener("click", function (event) {
    if (!header.classList.contains("is-nav-open")) return;
    if (header.contains(event.target)) return;
    closeNav();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeNav();
  });

  header.querySelectorAll(".molosoc-nav-toggle ~ nav a").forEach(function (link) {
    link.addEventListener("click", closeNav);
  });
})();

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

  // Submenu arrows (e.g. "Foot Cover" > "Molosoc Foot Cover") — WordPress
  // marks any parent item as .menu-item-has-children and nests the child
  // list as ul.sub-menu; neither has any show/hide behavior by default, so
  // we inject a dedicated arrow button here rather than via a custom PHP
  // nav walker. The parent link still navigates normally — only the arrow
  // toggles the child list open/closed, inline (not a separate drawer).
  header.querySelectorAll(".menu-item-has-children").forEach(function (item) {
    var link = item.querySelector(":scope > a");
    var submenu = item.querySelector(":scope > .sub-menu");
    if (!link || !submenu) return;

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "molosoc-submenu-toggle";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Show " + link.textContent.trim() + " submenu");
    toggle.innerHTML =
      '<svg viewBox="0 0 12 8" fill="none" aria-hidden="true"><path d="M1 1l5 5 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    link.insertAdjacentElement("afterend", toggle);

    toggle.addEventListener("click", function () {
      var isOpen = item.classList.toggle("is-submenu-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      toggle.setAttribute(
        "aria-label",
        (isOpen ? "Hide " : "Show ") + link.textContent.trim() + " submenu"
      );
    });
  });
})();

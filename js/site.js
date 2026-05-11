(function () {
  "use strict";

  function currentPage() {
    var path = (location.pathname || "").replace(/\\/g, "/");
    var parts = path.split("/").filter(function (p) {
      return p;
    });
    var name = parts.length ? parts[parts.length - 1] : "index.html";
    if (!name) name = "index.html";
    return name;
  }

  function markNavActive() {
    var page = currentPage();
    var force = document.body.getAttribute("data-nav-active");
    document.querySelectorAll(".site-nav a[href]").forEach(function (a) {
      var href = a.getAttribute("href");
      if (!href || href.indexOf("http") === 0 || href.indexOf("#") === 0) return;
      var file = href.split("/").pop();
      var match = file === page;
      if (force && href === force) match = true;
      if (match) {
        a.classList.add("is-active");
        var branch = a.closest(".nav-item.has-submenu");
        if (branch) branch.classList.add("is-active-branch");
      }
    });
  }

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-nav");

  function closeAllSubmenus() {
    document.querySelectorAll(".nav-item.has-submenu.is-open").forEach(function (li) {
      li.classList.remove("is-open");
      var b = li.querySelector(".nav-submenu-toggle");
      if (b) b.setAttribute("aria-expanded", "false");
    });
  }

  function setNavOpen(open) {
    if (!toggle || !nav) return;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    nav.classList.toggle("is-open", open);
    if (!open) closeAllSubmenus();
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      setNavOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    nav.querySelectorAll("a[href]").forEach(function (a) {
      a.addEventListener("click", function () {
        setNavOpen(false);
      });
    });
  }

  document.querySelectorAll(".nav-submenu-toggle").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      if (!window.matchMedia("(max-width: 1040px)").matches) return;
      e.preventDefault();
      e.stopPropagation();
      var li = btn.closest(".nav-item.has-submenu");
      if (!li) return;
      var opening = !li.classList.contains("is-open");
      document.querySelectorAll(".nav-item.has-submenu.is-open").forEach(function (other) {
        if (other !== li) {
          other.classList.remove("is-open");
          var ob = other.querySelector(".nav-submenu-toggle");
          if (ob) ob.setAttribute("aria-expanded", "false");
        }
      });
      li.classList.toggle("is-open", opening);
      btn.setAttribute("aria-expanded", opening ? "true" : "false");
    });
  });

  document.addEventListener("click", function (e) {
    if (!window.matchMedia("(max-width: 1040px)").matches) return;
    if (!nav || !toggle) return;
    if (nav.contains(e.target) || toggle.contains(e.target)) return;
    setNavOpen(false);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      setNavOpen(false);
      closeAllSubmenus();
    }
  });

  markNavActive();

  var y = document.getElementById("year");
  if (y) y.textContent = String(new Date().getFullYear());
})();

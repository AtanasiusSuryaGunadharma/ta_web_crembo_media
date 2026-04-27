/**
 * _sidebar-fix.js  v2
 * Crembo Media — Auto-fix sidebar active state, toggle, mobile
 * Place BEFORE </body> on every dashboard page
 */
(function () {
  'use strict';

  if (window.__cremboSidebarFixed) {
    return;
  }
  window.__cremboSidebarFixed = true;

  var path = window.location.pathname.split('/').pop() || 'index.html';

  function getLinkFilename(href) {
    if (!href) return '';
    return href.split('?')[0].split('#')[0].split('/').pop();
  }

  /* ── 1. Remove all existing active classes ── */
  var allLinks = Array.from(document.querySelectorAll('.menu-link'));
  allLinks.forEach(function (link) { link.classList.remove('active'); });

  /* ── 2. Mark active links & auto-open their parent group ── */
  allLinks.forEach(function (link) {
    var linkFile = getLinkFilename(link.getAttribute('href'));
    var isDashboardHash = !linkFile
      && (path === 'dashboard.html' || path === 'dashboard-anggota.html')
      && /dashboard/i.test(String(link.textContent || ''));

    if ((linkFile && linkFile === path) || isDashboardHash) {
      link.classList.add('active');
      var group = link.closest('.menu-group');
      if (group) {
        group.classList.add('open');
        var toggleBtn = group.querySelector('.group-toggle, .menu-toggle');
        if (toggleBtn) {
          var marker = toggleBtn.querySelector('span');
          if (marker) marker.textContent = '-';
        }
      }
    }
  });

  /* ── 3. REPLACE toggle handlers (prevents double-binding bug) ── */
  var groups = Array.from(document.querySelectorAll('.menu-group'));
  groups.forEach(function (group) {
    if (group.dataset.sidebarFixed === '1') return;
    group.dataset.sidebarFixed = '1';

    var btn = group.querySelector('.group-toggle, .menu-toggle');
    if (!btn) return;

    /* Clone the button to wipe ALL previous listeners */
    var freshBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(freshBtn, btn);

    freshBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      group.classList.toggle('open');
      var marker = freshBtn.querySelector('span');
      if (marker) marker.textContent = group.classList.contains('open') ? '-' : '+';
    });
  });

  /* ── 4. Mobile sidebar toggle ── */
  var sidebar = document.getElementById('sidebar');
  var mobileBtns = Array.from(document.querySelectorAll(
    '#mobileSidebarBtn, #mobileMenuBtn, .mobile-toggle, .mobile-menu'
  ));

  if (sidebar && mobileBtns.length === 0) {
    var headerHost = document.querySelector('.headline, .topbar, .header, .head, .dashboard-headline-bar');
    if (headerHost) {
      var autoMenu = document.createElement('button');
      autoMenu.id = 'mobileSidebarBtn';
      autoMenu.type = 'button';
      autoMenu.className = 'mobile-toggle';
      autoMenu.textContent = 'Menu';

      var firstBlock = headerHost.firstElementChild;
      if (firstBlock && firstBlock !== autoMenu) {
        firstBlock.parentNode.insertBefore(autoMenu, firstBlock);
      } else {
        headerHost.insertBefore(autoMenu, headerHost.firstChild);
      }
      mobileBtns.push(autoMenu);
    }
  }

  /* Remove any existing page-level click handlers by replacing buttons */
  var uniqueMobileBtns = [];
  mobileBtns.forEach(function (btn) {
    if (btn && uniqueMobileBtns.indexOf(btn) === -1) {
      uniqueMobileBtns.push(btn);
    }
  });

  mobileBtns = uniqueMobileBtns.map(function (btn) {
    if (!btn || !btn.parentNode) return btn;
    var freshBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(freshBtn, btn);
    return freshBtn;
  });

  var sidebarBackdrop = document.getElementById('sidebarBackdrop');
  if (sidebar && !sidebarBackdrop) {
    sidebarBackdrop = document.createElement('div');
    sidebarBackdrop.id = 'sidebarBackdrop';
    sidebarBackdrop.className = 'sidebar-backdrop';
    sidebarBackdrop.setAttribute('aria-hidden', 'true');
    if (sidebar.parentNode) {
      sidebar.parentNode.insertBefore(sidebarBackdrop, sidebar.nextSibling);
    } else {
      document.body.appendChild(sidebarBackdrop);
    }
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('show');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('show');
    document.body.style.overflow = '';
  }

  mobileBtns.forEach(function (btn) {
    if (!btn || btn._mobileFixed) return;
    btn._mobileFixed = true;
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (!sidebar) return;
      var isOpen = sidebar.classList.toggle('show');
      if (sidebarBackdrop) sidebarBackdrop.classList.toggle('show', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });
  });

  /* ── 5. Click outside to close sidebar (mobile) ── */
  document.addEventListener('click', function (e) {
    if (!sidebar || !sidebar.classList.contains('show')) return;
    if (sidebar.contains(e.target)) return;
    var isMobileBtn = mobileBtns.some(function (b) { return b && b.contains(e.target); });
    if (!isMobileBtn) closeSidebar();
  });

  if (sidebarBackdrop && !sidebarBackdrop._mobileFixed) {
    sidebarBackdrop._mobileFixed = true;
    sidebarBackdrop.addEventListener('click', closeSidebar);
  }

  window.addEventListener('resize', function () {
    if (window.innerWidth > 860) {
      closeSidebar();
    }
  });

  /* ── 6. Consistent topbar: inject datetime + globe if missing ── */
  var dateEl = document.getElementById('liveDateTime');
  var dayNames = ['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'];
  var monthNames = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];

  function fmtDate(now) {
    return dayNames[now.getDay()] + ', '
      + String(now.getDate()).padStart(2,'0') + ' '
      + monthNames[now.getMonth()] + ' '
      + now.getFullYear() + '  '
      + String(now.getHours()).padStart(2,'0') + ':'
      + String(now.getMinutes()).padStart(2,'0') + ':'
      + String(now.getSeconds()).padStart(2,'0');
  }

  if (dateEl) {
    dateEl.textContent = fmtDate(new Date());
    setInterval(function () { dateEl.textContent = fmtDate(new Date()); }, 1000);
  }

  /* ── 7. Inject globe link into topbar/header if missing ── */
  var header = document.querySelector('.headline, .topbar, .header, .head, .dashboard-headline-bar');
  if (header && !header.querySelector('.world-link, .home-globe')) {
    var sessionRaw = localStorage.getItem('crembo-login-session');
    var role = 'admin';
    try { role = JSON.parse(sessionRaw).role || 'admin'; } catch(e) {}
    var homeHref = role === 'anggota' ? 'dashboard-anggota.html' : 'dashboard.html';

    /* datetime chip if not already there */
    if (!dateEl) {
      var dtSpan = document.createElement('span');
      dtSpan.id = 'liveDateTime';
      dtSpan.className = 'chip';
      dtSpan.textContent = fmtDate(new Date());
      header.appendChild(dtSpan);
      setInterval(function () { dtSpan.textContent = fmtDate(new Date()); }, 1000);
    }

    /* globe link */
    var globe = document.createElement('a');
    globe.className = 'world-link';
    globe.href = homeHref;
    globe.title = 'Kembali ke Dashboard';
    globe.setAttribute('aria-label', 'Kembali ke Dashboard');
    globe.innerHTML = '<svg viewBox="0 0 24 24" fill="none" width="17" height="17" aria-hidden="true">'
      + '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8"/>'
      + '<path d="M3 12H21" stroke="currentColor" stroke-width="1.8"/>'
      + '<path d="M12 3C14.3 5.5 15.6 8.7 15.6 12C15.6 15.3 14.3 18.5 12 21" stroke="currentColor" stroke-width="1.8"/>'
      + '<path d="M12 3C9.7 5.5 8.4 8.7 8.4 12C8.4 15.3 9.7 18.5 12 21" stroke="currentColor" stroke-width="1.8"/>'
      + '</svg>';

    /* Append to right side of header */
    var right = header.querySelector('.head-right, .header-right, .head-meta');
    if (right) right.appendChild(globe);
    else header.appendChild(globe);
  }

})();

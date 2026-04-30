(function () {
  'use strict';

  if (window.__cremboPublicNavSync) {
    return;
  }
  window.__cremboPublicNavSync = true;

  var STORAGE_KEY = 'crembo-profile-menu';
  var API_URL = '/api/profiles';
  var DEFAULT_MENU = [
    { id: 'sejarah', label: 'Sejarah' },
    { id: 'tentang-crembo', label: 'Tentang Crembo' },
    { id: 'struktur', label: 'Struktur' },
    { id: 'visi-misi', label: 'Visi & Misi' }
  ];

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function normalizeMenuItem(item) {
    if (!item) {
      return null;
    }

    if (typeof item === 'string') {
      var text = String(item).trim();
      if (!text) {
        return null;
      }
      return {
        id: text.toLowerCase().replace(/\s+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, ''),
        label: text
      };
    }

    if (typeof item !== 'object') {
      return null;
    }

    var label = String(item.label || item.title || item.name || '').trim();
    var id = String(item.id || item.slug || label || '').trim();
    if (!label && !id) {
      return null;
    }

    if (!label) {
      label = id || 'Profil';
    }
    if (!id) {
      id = label;
    }

    return {
      id: id.toLowerCase().replace(/\s+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, ''),
      label: label
    };
  }

  function normalizeMenuList(value) {
    if (!value) {
      return [];
    }

    var rawItems = value;
    if (typeof value === 'string') {
      try {
        rawItems = JSON.parse(value);
      } catch (error) {
        return [];
      }
    }

    if (!Array.isArray(rawItems)) {
      return [];
    }

    return rawItems.map(normalizeMenuItem).filter(Boolean);
  }

  function readCachedMenu() {
    try {
      return normalizeMenuList(localStorage.getItem(STORAGE_KEY));
    } catch (error) {
      return [];
    }
  }

  function writeCachedMenu(menuItems) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(menuItems));
    } catch (error) {
      // Ignore storage errors.
    }
  }

  function getMenuLists() {
    var lists = Array.from(document.querySelectorAll('.nav-row nav ul, .nav-wrap nav ul'));
    return lists.filter(function (list) {
      return Boolean(list.querySelector('a[href="profil.html"]'));
    });
  }

  function ensureDropdown(profileItem) {
    var dropdown = profileItem.querySelector('.nav-dropdown-menu, .profile-hover-menu, .profile-menu-dropdown');
    if (!dropdown) {
      dropdown = document.createElement('div');
      dropdown.className = 'nav-dropdown-menu profile-hover-menu profile-menu-dropdown';
      profileItem.appendChild(dropdown);
    }
    return dropdown;
  }

  function applyDropdownStyle(profileItem, dropdown, isMobile) {
    profileItem.style.position = isMobile ? 'static' : 'relative';

    if (isMobile) {
      Object.assign(dropdown.style, {
        position: 'static',
        top: 'auto',
        left: 'auto',
        minWidth: '0',
        width: '100%',
        border: '1px solid rgba(128, 0, 0, 0.15)',
        background: 'var(--bg, #faf8f6)',
        boxShadow: 'none',
        padding: '6px',
        display: 'none',
        zIndex: '1300',
        borderRadius: '8px',
        marginTop: '6px'
      });
      return;
    }

    Object.assign(dropdown.style, {
      position: 'absolute',
      top: 'calc(100% - 1px)',
      left: '0',
      minWidth: '200px',
      width: 'auto',
      border: '1px solid rgba(128, 0, 0, 0.15)',
      background: '#fff',
      boxShadow: '0 10px 30px rgba(128, 0, 0, 0.12)',
      padding: '6px',
      display: 'none',
      zIndex: '1300',
      borderRadius: '12px',
      marginTop: '0'
    });
  }

  function renderMenuItems(dropdown, menuItems) {
    dropdown.innerHTML = menuItems.map(function (item) {
      return '<a href="profil.html?profil=' + encodeURIComponent(item.id) + '" style="display:block;padding:8px 12px;font-size:0.87rem;border-radius:8px;color:#4a4a4a;margin-bottom:2px;transition:all 0.2s;">' +
        escapeHtml(item.label) +
      '</a>';
    }).join('');
  }

  function wireDropdown(profileItem, profileAnchor, dropdown) {
    if (profileItem.dataset.cremboProfileDropdownWired === '1') {
      return;
    }
    profileItem.dataset.cremboProfileDropdownWired = '1';

    var mobileQuery = window.matchMedia('(max-width: 760px)');
    var closeTimer = null;

    function showMenu() {
      if (closeTimer) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      if (!mobileQuery.matches) {
        dropdown.style.display = 'block';
      }
    }

    function hideMenu() {
      if (closeTimer) {
        window.clearTimeout(closeTimer);
      }
      closeTimer = window.setTimeout(function () {
        dropdown.style.display = 'none';
        profileItem.classList.remove('open');
        profileAnchor.setAttribute('aria-expanded', 'false');
      }, mobileQuery.matches ? 0 : 120);
    }

    function forceHideMenu() {
      if (closeTimer) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      dropdown.style.display = 'none';
      profileItem.classList.remove('open');
      profileAnchor.setAttribute('aria-expanded', 'false');
    }

    profileAnchor.addEventListener('click', function (event) {
      if (!mobileQuery.matches) {
        return;
      }
      event.preventDefault();
      if (closeTimer) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      var isOpen = dropdown.style.display !== 'block';
      dropdown.style.display = isOpen ? 'block' : 'none';
      profileItem.classList.toggle('open', isOpen);
      profileAnchor.setAttribute('aria-expanded', String(isOpen));
    });

    dropdown.addEventListener('mouseover', function (event) {
      var link = event.target.closest('a');
      if (link) {
        link.style.background = 'rgba(128, 0, 0, 0.06)';
        link.style.color = '#800000';
      }
    });

    dropdown.addEventListener('mouseout', function (event) {
      var link = event.target.closest('a');
      if (link) {
        link.style.background = 'transparent';
        link.style.color = '#4a4a4a';
      }
    });

    dropdown.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        forceHideMenu();
      });
    });

    profileItem.addEventListener('mouseenter', showMenu);
    profileItem.addEventListener('mouseleave', hideMenu);
    dropdown.addEventListener('mouseenter', showMenu);
    dropdown.addEventListener('mouseleave', hideMenu);
    profileItem.addEventListener('focusin', showMenu);
    profileItem.addEventListener('focusout', function () {
      window.setTimeout(function () {
        if (!profileItem.contains(document.activeElement)) {
          forceHideMenu();
        }
      }, 0);
    });

    mobileQuery.addEventListener('change', function () {
      if (!mobileQuery.matches) {
        forceHideMenu();
      } else {
        applyDropdownStyle(profileItem, dropdown, true);
      }
    });
  }

  function enhanceMenuList(navList, menuItems) {
    var profileAnchor = navList.querySelector('a[href="profil.html"]');
    if (!profileAnchor) {
      return;
    }

    var profileItem = profileAnchor.closest('li');
    if (!profileItem) {
      return;
    }

    var mobileQuery = window.matchMedia('(max-width: 760px)');
    var dropdown = ensureDropdown(profileItem);
    var firstLabel = profileAnchor.textContent ? profileAnchor.textContent.trim() : 'Profil';

    if (!profileAnchor.hasAttribute('data-crembo-profile-label')) {
      profileAnchor.setAttribute('data-crembo-profile-label', '1');
      if (firstLabel.slice(-1) !== '▾') {
        profileAnchor.textContent = firstLabel + ' ▾';
      }
    }

    profileAnchor.classList.add('profile-parent-link');
    profileAnchor.setAttribute('aria-expanded', 'false');

    applyDropdownStyle(profileItem, dropdown, mobileQuery.matches);
    renderMenuItems(dropdown, menuItems);
    wireDropdown(profileItem, profileAnchor, dropdown);
  }

  function syncPublicMenus(menuItems) {
    getMenuLists().forEach(function (navList) {
      enhanceMenuList(navList, menuItems);
    });
  }

  function fetchProfileMenu() {
    var cached = readCachedMenu();
    var initialMenu = cached.length ? cached : DEFAULT_MENU;
    syncPublicMenus(initialMenu);

    if (!window.fetch) {
      return;
    }

    fetch(API_URL, { cache: 'no-store', credentials: 'same-origin' })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Failed to load profile menu');
        }
        return response.json();
      })
      .then(function (data) {
        var menuItems = normalizeMenuList(data);
        if (!menuItems.length) {
          return;
        }
        writeCachedMenu(menuItems);
        syncPublicMenus(menuItems);
      })
      .catch(function () {
        // Keep cached/default menu when the API is unavailable.
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fetchProfileMenu);
  } else {
    fetchProfileMenu();
  }
})();
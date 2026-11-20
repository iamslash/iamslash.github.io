// Sidebar enhancements for mdBook 0.4.40. Loaded after book.js
// (additional-js), so the sidebar and its handlers already exist.
(function () {
  var body = document.body;
  var sidebar = document.getElementById('sidebar');
  var anchor = document.getElementById('sidebar-toggle-anchor');
  var opener = document.getElementById('sidebar-toggle');
  if (!sidebar) return;

  // 1. Turn each series row into one disclosure button.
  //
  // A series is an empty-link parent in SUMMARY.md. mdBook renders its name
  // as an inert <div>, and only the small chevron opens it: an <a> without
  // href, so Enter and Space do nothing. A native <button> fixes both.
  sidebar.querySelectorAll('li.chapter-item').forEach(function (li, i) {
    var label = li.querySelector(':scope > div');
    var toggle = li.querySelector(':scope > a.toggle');
    if (!label || !toggle) return;

    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'series-toggle';

    var name = document.createElement('span');
    name.className = 'series-name';
    name.textContent = label.textContent;
    var chevron = document.createElement('span');
    chevron.className = 'series-chevron';
    chevron.setAttribute('aria-hidden', 'true');
    chevron.textContent = '❱';
    button.append(name, chevron);

    var next = li.nextElementSibling;
    var list = next && next.querySelector(':scope > ol.section');
    if (list) {
      list.id = list.id || 'series-' + i;
      button.setAttribute('aria-controls', list.id);
    }

    function sync() {
      button.setAttribute('aria-expanded', li.classList.contains('expanded') ? 'true' : 'false');
    }
    button.addEventListener('click', function () {
      li.classList.toggle('expanded');
      sync();
    });
    // Search note: searcher.js turns Enter anywhere on the page into "open
    // the selected search result". Keep Enter on this button for the button.
    button.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') e.stopPropagation();
    });
    sync();

    label.replaceWith(button);
    toggle.remove();
  });

  // 2. Make the stock sidebar opener usable from the keyboard. It is a
  // <label for> the hidden checkbox, so it takes no focus and no key, and a
  // label tied to a control may not take role=button. Untie it: book.js
  // already shows and hides the sidebar on its click, and step 3 sets the
  // checkbox from that. Without JavaScript the label keeps working as is.
  if (opener) {
    opener.removeAttribute('for');
    opener.tabIndex = 0;
    opener.setAttribute('role', 'button');
    // Act on key release, like a native button on Space. While a key is
    // held, its repeats land here and are swallowed; acting on the first
    // keydown would move focus to the sidebar and let the repeats fall on a
    // link there (and on the search handler, see the search note above).
    var pressed = null;
    function isActivation(e) { return e.key === 'Enter' || e.key === ' '; }
    function shown(el) { return el && el.getClientRects().length > 0; }
    opener.addEventListener('keydown', function (e) {
      if (!isActivation(e)) return;
      e.preventDefault();
      e.stopPropagation();
      if (!e.repeat) pressed = e.key;
    });
    opener.addEventListener('keyup', function (e) {
      if (!isActivation(e)) return;
      e.preventDefault();
      e.stopPropagation();
      if (e.key !== pressed) return;
      pressed = null;
      var opening = body.classList.contains('sidebar-hidden');
      opener.click();
      if (opening) {
        // The current chapter, unless its series was folded; then the first
        // row that can be seen.
        var active = sidebar.querySelector('a.active');
        var target = shown(active) ? active
          : Array.prototype.find.call(sidebar.querySelectorAll('a, button'), shown);
        if (target) target.focus();
      }
    });
    opener.addEventListener('blur', function () { pressed = null; });
  }

  // 3. Keep one notion of "sidebar shown". book.js flips the body class on
  // the opener, on swipe and on a very narrow drag, but only the opener used
  // to move the checkbox that CSS slides the sidebar with. Follow the body
  // class, and keep the checkbox, aria-hidden, the tab order and focus in
  // step with it.
  function syncVisibility() {
    var hidden = body.classList.contains('sidebar-hidden');
    if (anchor) anchor.checked = !hidden;
    sidebar.setAttribute('aria-hidden', hidden ? 'true' : 'false');
    if (opener) opener.setAttribute('aria-expanded', hidden ? 'false' : 'true');
    sidebar.querySelectorAll('a, button').forEach(function (el) {
      el.tabIndex = hidden ? -1 : 0;
    });
    if (hidden && sidebar.contains(document.activeElement) && opener) opener.focus();
  }
  syncVisibility();
  new MutationObserver(syncVisibility).observe(body, { attributes: true, attributeFilter: ['class'] });

  // 4. book.js lets a drag shrink the sidebar to 20px before hiding it, too
  // narrow for any label. Hold it at 150px, the width its own opener restores.
  var MIN_WIDTH = 150;
  new MutationObserver(function () {
    var root = document.documentElement;
    var width = parseInt(root.style.getPropertyValue('--sidebar-width'), 10);
    if (width < MIN_WIDTH && !body.classList.contains('sidebar-hidden')) {
      root.style.setProperty('--sidebar-width', MIN_WIDTH + 'px');
    }
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['style'] });
})();

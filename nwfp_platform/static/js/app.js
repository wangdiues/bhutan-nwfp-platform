(function () {
  'use strict';

  function getCookie(name) {
    return document.cookie
      .split(';')
      .map(function (value) {
        return value.trim();
      })
      .filter(function (value) {
        return value.indexOf(name + '=') === 0;
      })
      .map(function (value) {
        return decodeURIComponent(value.substring(name.length + 1));
      })[0] || '';
  }

  function cartCount() {
    var stored = window.localStorage.getItem('cart_count') || getCookie('cart_count') || '0';
    var count = parseInt(stored, 10);
    return Number.isFinite(count) && count > 0 ? count : 0;
  }

  function updateCartBadges() {
    var count = cartCount();
    document.querySelectorAll('[data-cart-badge]').forEach(function (badge) {
      badge.textContent = String(count);
      badge.hidden = count < 1;
    });
  }

  function setupHtmx() {
    if (window.htmx) {
      window.htmx.config.defaultSwapStyle = 'outerHTML';
    }
  }

  function setupAlpineCartControls() {
    document.addEventListener('alpine:init', function () {
      window.Alpine.data('cartQuantity', function (initialQuantity) {
        return {
          quantity: Math.max(parseInt(initialQuantity || 1, 10), 1),
          increment: function () {
            this.quantity += 1;
          },
          decrement: function () {
            this.quantity = Math.max(this.quantity - 1, 1);
          },
        };
      });
    });
  }

  function setupImageGallery() {
    document.querySelectorAll('[data-product-gallery]').forEach(function (gallery) {
      var mainImage = gallery.querySelector('[data-gallery-main]');
      if (!mainImage) {
        return;
      }

      gallery.querySelectorAll('[data-gallery-thumb]').forEach(function (thumbnail) {
        thumbnail.addEventListener('click', function () {
          var nextSrc = thumbnail.getAttribute('data-full-src') || thumbnail.getAttribute('src');
          var nextAlt = thumbnail.getAttribute('alt') || mainImage.getAttribute('alt') || '';
          if (!nextSrc) {
            return;
          }
          mainImage.setAttribute('src', nextSrc);
          mainImage.setAttribute('alt', nextAlt);
          gallery.querySelectorAll('[data-gallery-thumb]').forEach(function (item) {
            item.classList.toggle('is-active', item === thumbnail);
          });
        });
      });
    });
  }

  function setupPwaInstallPrompt() {
    var deferredPrompt = null;

    window.addEventListener('beforeinstallprompt', function (event) {
      event.preventDefault();
      deferredPrompt = event;
      document.querySelectorAll('[data-pwa-install]').forEach(function (button) {
        button.hidden = false;
      });
    });

    document.addEventListener('click', function (event) {
      var button = event.target.closest('[data-pwa-install]');
      if (!button || !deferredPrompt) {
        return;
      }
      deferredPrompt.prompt();
      deferredPrompt.userChoice.finally(function () {
        deferredPrompt = null;
        button.hidden = true;
      });
    });
  }

  function setupMapPanelToggle() {
    document.addEventListener('click', function (event) {
      var toggle = event.target.closest('[data-map-toggle]');
      if (!toggle) {
        return;
      }

      var selector = toggle.getAttribute('data-map-toggle');
      var panel = selector ? document.querySelector(selector) : document.querySelector('[data-map-panel]');
      if (!panel) {
        return;
      }

      var expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      panel.classList.toggle('is-open', !expanded);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    updateCartBadges();
    setupHtmx();
    setupImageGallery();
    setupPwaInstallPrompt();
    setupMapPanelToggle();
  });

  setupAlpineCartControls();
  window.NWFP = window.NWFP || {};
  window.NWFP.updateCartBadges = updateCartBadges;
})();

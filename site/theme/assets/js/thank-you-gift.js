/*
  Thank You page gift add-on (inc/thank-you-gift.php, GitHub Issue #106).
  Shows one size selector per chosen pair and the matching total. Every
  total is computed and formatted server-side from WooCommerce's own prices
  (data-totals, keyed "<M count>-<L count>") — this file only looks one up.
  Without it the section still works as a plain form for one pair
  (thank-you.css hides the 2- and 3-pair cards until .is-enhanced is set).
*/
(function () {
  var root = document.querySelector('[data-molosoc-gift]');
  var form = root && root.querySelector('form');
  if (!form) {
    return;
  }

  var totals = {};
  try {
    totals = JSON.parse(root.getAttribute('data-totals')) || {};
  } catch (e) {
    totals = {};
  }

  var pairs = Array.prototype.slice.call(root.querySelectorAll('[data-molosoc-gift-pair]'));
  var totalRow = root.querySelector('[data-molosoc-gift-total]');
  var totalAmount = root.querySelector('[data-molosoc-gift-total-amount]');

  function update() {
    var chosen = form.querySelector('input[name="molosoc_gift_pairs"]:checked');
    var count = chosen ? parseInt(chosen.value, 10) : 1;
    var m = 0;
    var l = 0;
    var complete = true;

    pairs.forEach(function (fieldset, index) {
      var active = index < count;
      fieldset.hidden = !active;
      fieldset.disabled = !active;
      if (!active) {
        return;
      }
      var size = fieldset.querySelector('input:checked');
      if (!size) {
        complete = false;
      } else if (size.value === 'M') {
        m += 1;
      } else {
        l += 1;
      }
    });

    var text = complete ? totals[m + '-' + l] : '';
    if (totalRow && totalAmount) {
      totalAmount.textContent = text || '';
      totalRow.hidden = !text;
    }
  }

  form.addEventListener('change', update);
  // Back/forward cache can restore the form with different radios checked.
  window.addEventListener('pageshow', update);
  root.classList.add('is-enhanced');
  update();
})();

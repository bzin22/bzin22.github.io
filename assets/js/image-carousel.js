document.querySelectorAll('[data-carousel]').forEach(function (carousel) {
  var viewport = carousel.querySelector('.image-carousel__viewport');
  var slides = carousel.querySelectorAll('.image-carousel__slide');
  var count = carousel.querySelector('.image-carousel__count');
  var index = 0;

  function show(next, smooth) {
    index = (next + slides.length) % slides.length;
    viewport.scrollTo({
      left: index * viewport.clientWidth,
      behavior: smooth && !window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'smooth' : 'instant'
    });
    count.textContent = (index + 1) + ' / ' + slides.length;
  }

  carousel.querySelector('[data-carousel-prev]').addEventListener('click', function () { show(index - 1, true); });
  carousel.querySelector('[data-carousel-next]').addEventListener('click', function () { show(index + 1, true); });
  viewport.addEventListener('keydown', function (event) {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      show(index + (event.key === 'ArrowRight' ? 1 : -1), true);
    }
  });
  viewport.addEventListener('scroll', function () {
    if (!viewport.clientWidth) return;
    index = Math.max(0, Math.min(slides.length - 1, Math.round(viewport.scrollLeft / viewport.clientWidth)));
    count.textContent = (index + 1) + ' / ' + slides.length;
  }, { passive: true });
  if ('ResizeObserver' in window) {
    var width = 0;
    new ResizeObserver(function () {
      if (viewport.clientWidth && viewport.clientWidth !== width) {
        width = viewport.clientWidth;
        show(index, false);
      }
    }).observe(viewport);
  }
});

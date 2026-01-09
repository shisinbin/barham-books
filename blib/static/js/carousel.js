function initCarousel(root) {
  const viewport = root.querySelector('.carousel__viewport');
  const track = root.querySelector('.carousel__track');
  const controls = root.querySelector('.carousel__controls');
  const prevBtn = root.querySelector('.carousel__btn.prev');
  const nextBtn = root.querySelector('.carousel__btn.next');

  if (!viewport || !track || !prevBtn || !nextBtn) return;

  function getSlideWidth() {
    const SLIDE_MULTIPLE = 2;
    const DEFAULT_COLUMN_GAP = 0;

    const slide = track.querySelector('.carousel__slide');
    if (!slide) return 0;

    const gap = parseInt(
      getComputedStyle(track).columnGap || DEFAULT_COLUMN_GAP,
      10
    );

    return (slide.offsetWidth + gap) * SLIDE_MULTIPLE;
  }

  function update() {
    const { scrollLeft, scrollWidth, clientWidth } = viewport;
    const canScroll = scrollWidth > clientWidth + 2;

    // controls.hidden = !canScroll;
    if (!canScroll) {
      controls.style.display = 'none';
    } else {
      controls.style.display = 'flex';
    }

    prevBtn.disabled = scrollLeft <= 0;
    nextBtn.disabled = scrollLeft + clientWidth >= scrollWidth - 2;
  }

  function scroll(direction) {
    const slideWidth = getSlideWidth();
    if (!slideWidth) return;

    const amount = (viewport.clientWidth = slideWidth);
    viewport.scrollBy({
      left: amount * direction,
      behavior: 'smooth',
    });
  }

  prevBtn.addEventListener('click', () => scroll(-1));
  nextBtn.addEventListener('click', () => scroll(1));
  viewport.addEventListener('scroll', update);
  window.addEventListener('resize', update);

  update();
}

document.querySelectorAll('[data-carousel]').forEach(initCarousel);

/**
 * Shared PhotoSwipe 5.4.4 lightbox for hilal cards (mabims.dev).
 * Programmatic opening: openPswp(src, alt). Theming overrides live in
 * each page's global CSS (.pswp overrides below the import).
 */
import PhotoSwipe from 'photoswipe';
import PhotoSwipeLightbox from 'photoswipe/lightbox';
import 'photoswipe/style.css';

const isTouch = window.matchMedia('(pointer: coarse)').matches;

let lightbox: PhotoSwipeLightbox | null = null;
let bootstrapped = false;

function ensure() {
  if (!lightbox) {
    lightbox = new PhotoSwipeLightbox({
      pswpModule: () => PhotoSwipe,
      wheelToZoom: true,
      zoom: true,
      maxZoomLevel: 6,
      bgOpacity: 0.92,
      showHideAnimationType: 'fade',
      // Mouse: clicking the dark area around the image closes.
      bgClickAction: 'close',
      // Touch: tapping outside the image closes; tapping the image toggles
      // between the initial and secondary zoom levels.
      ...(isTouch
        ? {
            tapAction: (point, event) => {
              const pswp = lightbox?.pswp;
              if (!pswp) return;
              const target = event?.target as HTMLElement | null;
              if (target?.closest('.pswp__img')) {
                pswp.currSlide?.toggleZoom(point);
              } else {
                pswp.close();
              }
            },
          }
        : {}),
    });
    lightbox.on('uiRegister', () => {
      lightbox?.pswp?.ui?.registerElement({
        name: 'hilal-caption',
        order: 8,
        isButton: false,
        appendTo: 'root',
        onInit: (el, pswp) => {
          const update = () => {
            el.textContent = (pswp.currSlide?.data.alt as string) ?? '';
          };
          pswp.on('change', update);
          pswp.on('load', update);
        },
      });
    });
    lightbox.init();
  }
  return lightbox;
}

export function openPswp(src: string, alt: string, w = 1440, h = 1520, index = 0) {
  const lb = ensure();
  lb.loadAndOpen(index, [{ src, alt, w, h }]);
}

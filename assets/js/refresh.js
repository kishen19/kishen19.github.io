// The complete greeting and publications are readable without this enhancement.
const hero = document.querySelector('.hello');
const scene = document.querySelector('.hello-scene');
const line = document.querySelector('.typing-line');
const contact = document.querySelector('.contact');
const contactScene = document.querySelector('.contact-scene');
const comic = document.querySelector('.comic');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
let typingTimer;

function finishTyping() {
  if (!line) return;
  clearTimeout(typingTimer);
  line.querySelector('.typing-prefix').textContent = "I'm ";
  line.querySelector('.typing-name').textContent = 'Kishen';
  line.classList.remove('is-typing');
  line.style.width = '';
}

if (line && !reducedMotion.matches) {
  const prefix = line.querySelector('.typing-prefix');
  const name = line.querySelector('.typing-name');
  const text = "I'm Kishen";
  line.style.width = `${line.getBoundingClientRect().width}px`;
  line.classList.add('is-typing');
  prefix.textContent = '';
  name.textContent = '';
  let position = 0;
  const typeNext = () => {
    position += 1;
    prefix.textContent = text.slice(0, Math.min(position, 4));
    name.textContent = position > 4 ? text.slice(4, position) : '';
    typingTimer = setTimeout(position < text.length ? typeNext : finishTyping, position < text.length ? 105 : 300);
  };
  typingTimer = setTimeout(typeNext, 220);
}

// Move only the photograph, not the content. The extra image bleed hides its edges.
let framePending = false;
let lastOffset = -1;
let lastContactOffset = -1;
let lastComicShift = '';
function updateParallax() {
  framePending = false;
  // Read positions together before writing transforms; nothing changes document flow.
  const heroTop = hero && scene ? hero.getBoundingClientRect().top : 0;
  const contactTop = contact && (contactScene || comic) ? contact.getBoundingClientRect().top : 0;
  const offset = reducedMotion.matches ? 0 : Math.max(0, Math.min(48, -heroTop * .16));
  if (scene && offset !== lastOffset) {
    scene.style.setProperty('--parallax-offset', `${offset.toFixed(1)}px`);
    lastOffset = offset;
  }
  if (contact && contactScene) {
    const contactOffset = reducedMotion.matches ? 0 : Math.max(-36, Math.min(36, (window.innerHeight * .5 - contactTop) * .12));
    if (contactOffset !== lastContactOffset) {
      contactScene.style.setProperty('--contact-parallax-offset', `${contactOffset.toFixed(1)}px`);
      lastContactOffset = contactOffset;
    }
  }
  if (contact && comic) {
    const progress = reducedMotion.matches ? 0 : Math.max(-1, Math.min(1, (.5 - contactTop / window.innerHeight)));
    const shift = (-progress * 7).toFixed(1);
    if (shift !== lastComicShift) {
      comic.style.setProperty('--comic-shift', `${shift}px`);
      comic.style.setProperty('--comic-tilt', `${(2 + progress * .45).toFixed(2)}deg`);
      lastComicShift = shift;
    }
  }
}
function requestParallax() {
  if (!framePending) {
    framePending = true;
    requestAnimationFrame(updateParallax);
  }
}
if ((hero && scene) || (contact && (contactScene || comic))) {
  window.addEventListener('scroll', requestParallax, { passive: true });
  window.addEventListener('resize', requestParallax, { passive: true });
  updateParallax();
}
reducedMotion.addEventListener('change', () => {
  if (reducedMotion.matches) finishTyping();
  requestParallax();
});

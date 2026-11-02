// No browser or dependencies required: exercise both motion-preference paths.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const source = readFileSync(new URL('../assets/js/refresh.js', import.meta.url), 'utf8');

function fixture(reduced = false, { contactPhoto = true, withComic = true } = {}) {
  const timers = new Map();
  const events = new Map();
  const classes = new Set();
  const prefix = { textContent: "I'm " };
  const name = { textContent: 'Kishen' };
  const line = {
    style: {},
    classList: { add: key => classes.add(key), remove: key => classes.delete(key) },
    querySelector: selector => selector === '.typing-prefix' ? prefix : name,
    getBoundingClientRect: () => ({ width: 280 }),
  };
  const hero = { top: 0, getBoundingClientRect() { return { top: this.top }; } };
  const scene = { style: { setProperty(key, value) { this[key] = value; } } };
  const contact = { top: 800, getBoundingClientRect() { return { top: this.top }; } };
  const contactScene = { style: { setProperty(key, value) { this[key] = value; } } };
  const comic = { style: { setProperty(key, value) { this[key] = value; } } };
  const motion = { matches: reduced, addEventListener: (_, handler) => events.set('motion', handler) };
  let nextTimer = 0;
  runInNewContext(source, {
    document: { querySelector: selector => ({ '.hello': hero, '.hello-scene': scene, '.typing-line': line, '.contact': contact, '.contact-scene': contactPhoto ? contactScene : null, '.comic': withComic ? comic : null })[selector] },
    window: { innerHeight: 800, matchMedia: () => motion, addEventListener: (event, handler) => events.set(event, handler) },
    setTimeout: handler => { timers.set(++nextTimer, handler); return nextTimer; },
    clearTimeout: id => timers.delete(id),
    requestAnimationFrame: handler => handler(),
  });
  return { timers, events, classes, prefix, name, line, hero, scene, contact, contactScene, comic, motion };
}

const standard = fixture();
assert(standard.classes.has('is-typing'));
assert.equal(standard.line.style.width, '280px');
assert.equal(standard.prefix.textContent, '');
let steps = 0;
while (standard.timers.size) {
  assert(++steps < 20, 'Typing must finish, not loop forever');
  const [id, handler] = standard.timers.entries().next().value;
  standard.timers.delete(id);
  handler();
}
assert.equal(standard.prefix.textContent + standard.name.textContent, "I'm Kishen");
assert(!standard.classes.has('is-typing'));
assert.equal(standard.line.style.width, '');
standard.hero.top = -125;
standard.events.get('scroll')();
assert.equal(standard.scene.style['--parallax-offset'], '20.0px');
standard.hero.top = -1000;
standard.events.get('scroll')();
assert.equal(standard.scene.style['--parallax-offset'], '48.0px');
assert.equal(standard.contactScene.style['--contact-parallax-offset'], '-36.0px');
standard.contact.top = 400;
standard.events.get('scroll')();
assert.equal(standard.contactScene.style['--contact-parallax-offset'], '0.0px');
standard.contact.top = 100;
standard.events.get('scroll')();
assert.equal(standard.contactScene.style['--contact-parallax-offset'], '36.0px');
standard.contact.top = -1000;
standard.events.get('scroll')();
assert.equal(standard.contactScene.style['--contact-parallax-offset'], '36.0px');
assert.equal(standard.comic.style['--comic-shift'], '-7.0px');
assert.equal(standard.comic.style['--comic-tilt'], '2.45deg');
standard.motion.matches = true;
standard.events.get('motion')();
assert.equal(standard.scene.style['--parallax-offset'], '0.0px');
assert.equal(standard.contactScene.style['--contact-parallax-offset'], '0.0px');
assert.equal(standard.comic.style['--comic-shift'], '0.0px');
assert.equal(standard.comic.style['--comic-tilt'], '2.00deg');

const reduced = fixture(true);
assert.equal(reduced.timers.size, 0);
assert(!reduced.classes.has('is-typing'));
assert.equal(reduced.prefix.textContent + reduced.name.textContent, "I'm Kishen");
reduced.hero.top = -400;
reduced.events.get('scroll')();
assert.equal(reduced.scene.style['--parallax-offset'], '0.0px');
assert.equal(reduced.contactScene.style['--contact-parallax-offset'], '0.0px');
assert.equal(reduced.comic.style['--comic-shift'], '0.0px');

const interrupted = fixture();
interrupted.motion.matches = true;
interrupted.events.get('motion')();
assert.equal(interrupted.timers.size, 0);
assert.equal(interrupted.prefix.textContent + interrupted.name.textContent, "I'm Kishen");
assert(!interrupted.classes.has('is-typing'));

const photoOnly = fixture(false, { withComic: false });
photoOnly.contact.top = 200;
photoOnly.events.get('scroll')();
assert.equal(photoOnly.contactScene.style['--contact-parallax-offset'], '24.0px');
const comicOnly = fixture(false, { contactPhoto: false });
comicOnly.contact.top = -1000;
comicOnly.events.get('scroll')();
assert.equal(comicOnly.comic.style['--comic-shift'], '-7.0px');
console.log('Greeting, hero/contact parallax, comic, and reduced-motion checks passed.');

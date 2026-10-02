// Run after a production Jekyll build so HTML compression is exercised.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const site = process.env.SITE_DIR || path.join(__dirname, '..', '_site');
const routes = ['index.html', ...['about', 'research', 'projects', 'experience', 'resume'].map(route => `${route}/index.html`)];
const publicHosts = ['bryanzin.com', 'www.bryanzin.com', 'bzin22.github.io'];

for (const route of routes) {
  const html = fs.readFileSync(path.join(site, route), 'utf8');
  const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)]
    .map(match => match[1]).filter(script => script.includes('posthog.init('));
  assert.equal(scripts.length, 1, `${route}: expected one analytics snippet`);
  for (const hostname of [...publicHosts, 'localhost', '127.0.0.1', 'preview.example.com']) {
    const inserted = [];
    const context = {
      location: { hostname },
      document: {
        createElement: () => ({}),
        getElementsByTagName: () => [{ parentNode: { insertBefore: script => inserted.push(script) } }],
      },
    };
    context.window = context;
    vm.runInNewContext(scripts[0], context);
    if (publicHosts.includes(hostname)) {
      assert.equal(inserted.length, 1, `${route}: analytics must execute on ${hostname}`);
      assert.equal(context.posthog._i.length, 1);
      const [token, config] = context.posthog._i[0];
      assert.match(token, /^phc_/);
      assert.equal(inserted[0].src, `${config.api_host.replace('.i.posthog.com', '-assets.i.posthog.com')}/static/array.js`);
      assert.notEqual(config.disable_session_recording, true);
    } else {
      assert.equal(inserted.length, 0, `${route}: analytics must stay off on ${hostname}`);
      assert.equal(context.posthog, undefined);
    }
  }
}
console.log('OK: analytics executes on both layouts and stays off on local previews');

// Launch-only adapter: keep the environment's browser sandbox enabled.
// Test actions, fixtures, expectations and floors are unchanged.
const seen = new Set();
for (const moduleName of ['playwright', 'playwright-core']) {
  const type = require(moduleName).chromium;
  if (seen.has(type)) continue;
  seen.add(type);
  for (const method of ['launch', 'launchPersistentContext']) {
    const original = type[method].bind(type);
    type[method] = function (...args) {
      const index = method === 'launch' ? 0 : 1;
      const options = {...(args[index] || {}), chromiumSandbox: true};
      options.args = (options.args || []).filter(arg => !['--no-sandbox', '--disable-setuid-sandbox', '--no-proxy-server'].includes(arg));
      args[index] = options;
      process.stderr.write('CLOSEOUT_BROWSER_LAUNCH '+JSON.stringify({sandbox:true,args:options.args})+'\n');
      return original(...args);
    };
  }
}

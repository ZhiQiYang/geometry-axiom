// Environment-only launcher adapter: this Linux workspace has Chromium,
// not the Chrome channel. The committed #116 acceptance assertions stay intact.
const {chromium} = require('playwright');
const launch = chromium.launch.bind(chromium);
chromium.launch = options => {
  const effective = {...options};
  if (effective.channel === 'chrome') {
    delete effective.channel;
    effective.executablePath = '/usr/bin/chromium';
    effective.args = [...(effective.args || []), '--no-sandbox'];
    console.log('QA_ENVIRONMENT: original assertions; Chromium executable replaces unavailable Chrome channel');
  }
  return launch(effective);
};

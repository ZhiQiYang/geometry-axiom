'use strict';
// Preserve actual Node test events and the actual assertion message. Rendered
// stack/expected/actual text cannot supply code, failure type or a marker.
module.exports = async function* report(source) {
  for await (const event of source) {
    const data = event.data;
    if (event.type === 'test:pass' || event.type === 'test:fail') {
      const wrapper = data.details?.error;
      const assertion = wrapper?.failureType === 'testCodeFailure' ? wrapper.cause : wrapper;
      yield JSON.stringify({type: event.type, name: data.name, testNumber: data.testNumber,
        nesting: data.nesting, skip: !!data.skip, todo: !!data.todo,
        error: wrapper ? {name: assertion?.name, code: assertion?.code,
          failureType: wrapper.failureType, message: assertion?.message} : null}) + '\n';
    } else if (event.type === 'test:summary' && !data.file) {
      yield JSON.stringify({type: event.type, data}) + '\n';
    }
  }
};

/* The one fixed application composition. Core modules never import this file. */
(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('../geometry-templates/woodworking/frontend.js'));
  } else {
    Object.defineProperty(root, 'GeometryApplication', {value: factory(root.GeometryWoodworking)});
  }
})(typeof globalThis === 'object' ? globalThis : this, function (woodworking) {
  'use strict';
  if (!woodworking || woodworking.id !== 'woodworking/1' || !Object.isFrozen(woodworking)) {
    throw Error('應用程式缺少固定木工模板，請重新啟動服務。');
  }
  return Object.freeze({woodworking});
});

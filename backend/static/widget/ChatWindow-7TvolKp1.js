import { r as reactExports, j as jsxRuntimeExports, f as formatRetryTime, E as ErrorSeverity } from "./loader-DJBXa2lt.js";
import { widgetClient, WidgetApiException } from "./widgetClient-DgavxOUn.js";
function getDefaultExportFromCjs(x) {
  return x && x.__esModule && Object.prototype.hasOwnProperty.call(x, "default") ? x["default"] : x;
}
function getAugmentedNamespace(n) {
  if (n.__esModule) return n;
  var f = n.default;
  if (typeof f == "function") {
    var a = function a2() {
      if (this instanceof a2) {
        return Reflect.construct(f, arguments, this.constructor);
      }
      return f.apply(this, arguments);
    };
    a.prototype = f.prototype;
  } else a = {};
  Object.defineProperty(a, "__esModule", { value: true });
  Object.keys(n).forEach(function(k) {
    var d = Object.getOwnPropertyDescriptor(n, k);
    Object.defineProperty(a, k, d.get ? d : {
      enumerable: true,
      get: function() {
        return n[k];
      }
    });
  });
  return a;
}
var focusTrapReact = { exports: {} };
/*!
* tabbable 6.4.0
* @license MIT, https://github.com/focus-trap/tabbable/blob/master/LICENSE
*/
var candidateSelectors = ["input:not([inert]):not([inert] *)", "select:not([inert]):not([inert] *)", "textarea:not([inert]):not([inert] *)", "a[href]:not([inert]):not([inert] *)", "button:not([inert]):not([inert] *)", "[tabindex]:not(slot):not([inert]):not([inert] *)", "audio[controls]:not([inert]):not([inert] *)", "video[controls]:not([inert]):not([inert] *)", '[contenteditable]:not([contenteditable="false"]):not([inert]):not([inert] *)', "details>summary:first-of-type:not([inert]):not([inert] *)", "details:not([inert]):not([inert] *)"];
var candidateSelector = /* @__PURE__ */ candidateSelectors.join(",");
var NoElement = typeof Element === "undefined";
var matches = NoElement ? function() {
} : Element.prototype.matches || Element.prototype.msMatchesSelector || Element.prototype.webkitMatchesSelector;
var getRootNode = !NoElement && Element.prototype.getRootNode ? function(element) {
  var _element$getRootNode;
  return element === null || element === void 0 ? void 0 : (_element$getRootNode = element.getRootNode) === null || _element$getRootNode === void 0 ? void 0 : _element$getRootNode.call(element);
} : function(element) {
  return element === null || element === void 0 ? void 0 : element.ownerDocument;
};
var _isInert = function isInert(node, lookUp) {
  var _node$getAttribute;
  if (lookUp === void 0) {
    lookUp = true;
  }
  var inertAtt = node === null || node === void 0 ? void 0 : (_node$getAttribute = node.getAttribute) === null || _node$getAttribute === void 0 ? void 0 : _node$getAttribute.call(node, "inert");
  var inert = inertAtt === "" || inertAtt === "true";
  var result = inert || lookUp && node && // closest does not exist on shadow roots, so we fall back to a manual
  // lookup upward, in case it is not defined.
  (typeof node.closest === "function" ? node.closest("[inert]") : _isInert(node.parentNode));
  return result;
};
var isContentEditable = function isContentEditable2(node) {
  var _node$getAttribute2;
  var attValue = node === null || node === void 0 ? void 0 : (_node$getAttribute2 = node.getAttribute) === null || _node$getAttribute2 === void 0 ? void 0 : _node$getAttribute2.call(node, "contenteditable");
  return attValue === "" || attValue === "true";
};
var getCandidates = function getCandidates2(el, includeContainer, filter) {
  if (_isInert(el)) {
    return [];
  }
  var candidates = Array.prototype.slice.apply(el.querySelectorAll(candidateSelector));
  if (includeContainer && matches.call(el, candidateSelector)) {
    candidates.unshift(el);
  }
  candidates = candidates.filter(filter);
  return candidates;
};
var _getCandidatesIteratively = function getCandidatesIteratively(elements, includeContainer, options) {
  var candidates = [];
  var elementsToCheck = Array.from(elements);
  while (elementsToCheck.length) {
    var element = elementsToCheck.shift();
    if (_isInert(element, false)) {
      continue;
    }
    if (element.tagName === "SLOT") {
      var assigned = element.assignedElements();
      var content = assigned.length ? assigned : element.children;
      var nestedCandidates = _getCandidatesIteratively(content, true, options);
      if (options.flatten) {
        candidates.push.apply(candidates, nestedCandidates);
      } else {
        candidates.push({
          scopeParent: element,
          candidates: nestedCandidates
        });
      }
    } else {
      var validCandidate = matches.call(element, candidateSelector);
      if (validCandidate && options.filter(element) && (includeContainer || !elements.includes(element))) {
        candidates.push(element);
      }
      var shadowRoot = element.shadowRoot || // check for an undisclosed shadow
      typeof options.getShadowRoot === "function" && options.getShadowRoot(element);
      var validShadowRoot = !_isInert(shadowRoot, false) && (!options.shadowRootFilter || options.shadowRootFilter(element));
      if (shadowRoot && validShadowRoot) {
        var _nestedCandidates = _getCandidatesIteratively(shadowRoot === true ? element.children : shadowRoot.children, true, options);
        if (options.flatten) {
          candidates.push.apply(candidates, _nestedCandidates);
        } else {
          candidates.push({
            scopeParent: element,
            candidates: _nestedCandidates
          });
        }
      } else {
        elementsToCheck.unshift.apply(elementsToCheck, element.children);
      }
    }
  }
  return candidates;
};
var hasTabIndex = function hasTabIndex2(node) {
  return !isNaN(parseInt(node.getAttribute("tabindex"), 10));
};
var getTabIndex = function getTabIndex2(node) {
  if (!node) {
    throw new Error("No node provided");
  }
  if (node.tabIndex < 0) {
    if ((/^(AUDIO|VIDEO|DETAILS)$/.test(node.tagName) || isContentEditable(node)) && !hasTabIndex(node)) {
      return 0;
    }
  }
  return node.tabIndex;
};
var getSortOrderTabIndex = function getSortOrderTabIndex2(node, isScope) {
  var tabIndex = getTabIndex(node);
  if (tabIndex < 0 && isScope && !hasTabIndex(node)) {
    return 0;
  }
  return tabIndex;
};
var sortOrderedTabbables = function sortOrderedTabbables2(a, b) {
  return a.tabIndex === b.tabIndex ? a.documentOrder - b.documentOrder : a.tabIndex - b.tabIndex;
};
var isInput = function isInput2(node) {
  return node.tagName === "INPUT";
};
var isHiddenInput = function isHiddenInput2(node) {
  return isInput(node) && node.type === "hidden";
};
var isDetailsWithSummary = function isDetailsWithSummary2(node) {
  var r = node.tagName === "DETAILS" && Array.prototype.slice.apply(node.children).some(function(child) {
    return child.tagName === "SUMMARY";
  });
  return r;
};
var getCheckedRadio = function getCheckedRadio2(nodes, form) {
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].checked && nodes[i].form === form) {
      return nodes[i];
    }
  }
};
var isTabbableRadio = function isTabbableRadio2(node) {
  if (!node.name) {
    return true;
  }
  var radioScope = node.form || getRootNode(node);
  var queryRadios = function queryRadios2(name) {
    return radioScope.querySelectorAll('input[type="radio"][name="' + name + '"]');
  };
  var radioSet;
  if (typeof window !== "undefined" && typeof window.CSS !== "undefined" && typeof window.CSS.escape === "function") {
    radioSet = queryRadios(window.CSS.escape(node.name));
  } else {
    try {
      radioSet = queryRadios(node.name);
    } catch (err) {
      console.error("Looks like you have a radio button with a name attribute containing invalid CSS selector characters and need the CSS.escape polyfill: %s", err.message);
      return false;
    }
  }
  var checked = getCheckedRadio(radioSet, node.form);
  return !checked || checked === node;
};
var isRadio = function isRadio2(node) {
  return isInput(node) && node.type === "radio";
};
var isNonTabbableRadio = function isNonTabbableRadio2(node) {
  return isRadio(node) && !isTabbableRadio(node);
};
var isNodeAttached = function isNodeAttached2(node) {
  var _nodeRoot;
  var nodeRoot = node && getRootNode(node);
  var nodeRootHost = (_nodeRoot = nodeRoot) === null || _nodeRoot === void 0 ? void 0 : _nodeRoot.host;
  var attached = false;
  if (nodeRoot && nodeRoot !== node) {
    var _nodeRootHost, _nodeRootHost$ownerDo, _node$ownerDocument;
    attached = !!((_nodeRootHost = nodeRootHost) !== null && _nodeRootHost !== void 0 && (_nodeRootHost$ownerDo = _nodeRootHost.ownerDocument) !== null && _nodeRootHost$ownerDo !== void 0 && _nodeRootHost$ownerDo.contains(nodeRootHost) || node !== null && node !== void 0 && (_node$ownerDocument = node.ownerDocument) !== null && _node$ownerDocument !== void 0 && _node$ownerDocument.contains(node));
    while (!attached && nodeRootHost) {
      var _nodeRoot2, _nodeRootHost2, _nodeRootHost2$ownerD;
      nodeRoot = getRootNode(nodeRootHost);
      nodeRootHost = (_nodeRoot2 = nodeRoot) === null || _nodeRoot2 === void 0 ? void 0 : _nodeRoot2.host;
      attached = !!((_nodeRootHost2 = nodeRootHost) !== null && _nodeRootHost2 !== void 0 && (_nodeRootHost2$ownerD = _nodeRootHost2.ownerDocument) !== null && _nodeRootHost2$ownerD !== void 0 && _nodeRootHost2$ownerD.contains(nodeRootHost));
    }
  }
  return attached;
};
var isZeroArea = function isZeroArea2(node) {
  var _node$getBoundingClie = node.getBoundingClientRect(), width = _node$getBoundingClie.width, height = _node$getBoundingClie.height;
  return width === 0 && height === 0;
};
var isHidden = function isHidden2(node, _ref) {
  var displayCheck = _ref.displayCheck, getShadowRoot = _ref.getShadowRoot;
  if (displayCheck === "full-native") {
    if ("checkVisibility" in node) {
      var visible = node.checkVisibility({
        // Checking opacity might be desirable for some use cases, but natively,
        // opacity zero elements _are_ focusable and tabbable.
        checkOpacity: false,
        opacityProperty: false,
        contentVisibilityAuto: true,
        visibilityProperty: true,
        // This is an alias for `visibilityProperty`. Contemporary browsers
        // support both. However, this alias has wider browser support (Chrome
        // >= 105 and Firefox >= 106, vs. Chrome >= 121 and Firefox >= 122), so
        // we include it anyway.
        checkVisibilityCSS: true
      });
      return !visible;
    }
  }
  if (getComputedStyle(node).visibility === "hidden") {
    return true;
  }
  var isDirectSummary = matches.call(node, "details>summary:first-of-type");
  var nodeUnderDetails = isDirectSummary ? node.parentElement : node;
  if (matches.call(nodeUnderDetails, "details:not([open]) *")) {
    return true;
  }
  if (!displayCheck || displayCheck === "full" || // full-native can run this branch when it falls through in case
  // Element#checkVisibility is unsupported
  displayCheck === "full-native" || displayCheck === "legacy-full") {
    if (typeof getShadowRoot === "function") {
      var originalNode = node;
      while (node) {
        var parentElement = node.parentElement;
        var rootNode = getRootNode(node);
        if (parentElement && !parentElement.shadowRoot && getShadowRoot(parentElement) === true) {
          return isZeroArea(node);
        } else if (node.assignedSlot) {
          node = node.assignedSlot;
        } else if (!parentElement && rootNode !== node.ownerDocument) {
          node = rootNode.host;
        } else {
          node = parentElement;
        }
      }
      node = originalNode;
    }
    if (isNodeAttached(node)) {
      return !node.getClientRects().length;
    }
    if (displayCheck !== "legacy-full") {
      return true;
    }
  } else if (displayCheck === "non-zero-area") {
    return isZeroArea(node);
  }
  return false;
};
var isDisabledFromFieldset = function isDisabledFromFieldset2(node) {
  if (/^(INPUT|BUTTON|SELECT|TEXTAREA)$/.test(node.tagName)) {
    var parentNode = node.parentElement;
    while (parentNode) {
      if (parentNode.tagName === "FIELDSET" && parentNode.disabled) {
        for (var i = 0; i < parentNode.children.length; i++) {
          var child = parentNode.children.item(i);
          if (child.tagName === "LEGEND") {
            return matches.call(parentNode, "fieldset[disabled] *") ? true : !child.contains(node);
          }
        }
        return true;
      }
      parentNode = parentNode.parentElement;
    }
  }
  return false;
};
var isNodeMatchingSelectorFocusable = function isNodeMatchingSelectorFocusable2(options, node) {
  if (node.disabled || isHiddenInput(node) || isHidden(node, options) || // For a details element with a summary, the summary element gets the focus
  isDetailsWithSummary(node) || isDisabledFromFieldset(node)) {
    return false;
  }
  return true;
};
var isNodeMatchingSelectorTabbable = function isNodeMatchingSelectorTabbable2(options, node) {
  if (isNonTabbableRadio(node) || getTabIndex(node) < 0 || !isNodeMatchingSelectorFocusable(options, node)) {
    return false;
  }
  return true;
};
var isShadowRootTabbable = function isShadowRootTabbable2(shadowHostNode) {
  var tabIndex = parseInt(shadowHostNode.getAttribute("tabindex"), 10);
  if (isNaN(tabIndex) || tabIndex >= 0) {
    return true;
  }
  return false;
};
var _sortByOrder = function sortByOrder(candidates) {
  var regularTabbables = [];
  var orderedTabbables = [];
  candidates.forEach(function(item, i) {
    var isScope = !!item.scopeParent;
    var element = isScope ? item.scopeParent : item;
    var candidateTabindex = getSortOrderTabIndex(element, isScope);
    var elements = isScope ? _sortByOrder(item.candidates) : element;
    if (candidateTabindex === 0) {
      isScope ? regularTabbables.push.apply(regularTabbables, elements) : regularTabbables.push(element);
    } else {
      orderedTabbables.push({
        documentOrder: i,
        tabIndex: candidateTabindex,
        item,
        isScope,
        content: elements
      });
    }
  });
  return orderedTabbables.sort(sortOrderedTabbables).reduce(function(acc, sortable) {
    sortable.isScope ? acc.push.apply(acc, sortable.content) : acc.push(sortable.content);
    return acc;
  }, []).concat(regularTabbables);
};
var tabbable = function tabbable2(container, options) {
  options = options || {};
  var candidates;
  if (options.getShadowRoot) {
    candidates = _getCandidatesIteratively([container], options.includeContainer, {
      filter: isNodeMatchingSelectorTabbable.bind(null, options),
      flatten: false,
      getShadowRoot: options.getShadowRoot,
      shadowRootFilter: isShadowRootTabbable
    });
  } else {
    candidates = getCandidates(container, options.includeContainer, isNodeMatchingSelectorTabbable.bind(null, options));
  }
  return _sortByOrder(candidates);
};
var focusable = function focusable2(container, options) {
  options = options || {};
  var candidates;
  if (options.getShadowRoot) {
    candidates = _getCandidatesIteratively([container], options.includeContainer, {
      filter: isNodeMatchingSelectorFocusable.bind(null, options),
      flatten: true,
      getShadowRoot: options.getShadowRoot
    });
  } else {
    candidates = getCandidates(container, options.includeContainer, isNodeMatchingSelectorFocusable.bind(null, options));
  }
  return candidates;
};
var isTabbable = function isTabbable2(node, options) {
  options = options || {};
  if (!node) {
    throw new Error("No node provided");
  }
  if (matches.call(node, candidateSelector) === false) {
    return false;
  }
  return isNodeMatchingSelectorTabbable(options, node);
};
var focusableCandidateSelector = /* @__PURE__ */ candidateSelectors.concat("iframe:not([inert]):not([inert] *)").join(",");
var isFocusable$1 = function isFocusable(node, options) {
  options = options || {};
  if (!node) {
    throw new Error("No node provided");
  }
  if (matches.call(node, focusableCandidateSelector) === false) {
    return false;
  }
  return isNodeMatchingSelectorFocusable(options, node);
};
const index_esm = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  focusable,
  getTabIndex,
  isFocusable: isFocusable$1,
  isTabbable,
  tabbable
}, Symbol.toStringTag, { value: "Module" }));
/*!
* focus-trap 8.0.0
* @license MIT, https://github.com/focus-trap/focus-trap/blob/master/LICENSE
*/
function _arrayLikeToArray(r, a) {
  (null == a || a > r.length) && (a = r.length);
  for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e];
  return n;
}
function _arrayWithoutHoles(r) {
  if (Array.isArray(r)) return _arrayLikeToArray(r);
}
function asyncGeneratorStep(n, t, e, r, o, a, c) {
  try {
    var i = n[a](c), u = i.value;
  } catch (n2) {
    return void e(n2);
  }
  i.done ? t(u) : Promise.resolve(u).then(r, o);
}
function _asyncToGenerator(n) {
  return function() {
    var t = this, e = arguments;
    return new Promise(function(r, o) {
      var a = n.apply(t, e);
      function _next(n2) {
        asyncGeneratorStep(a, r, o, _next, _throw, "next", n2);
      }
      function _throw(n2) {
        asyncGeneratorStep(a, r, o, _next, _throw, "throw", n2);
      }
      _next(void 0);
    });
  };
}
function _createForOfIteratorHelper(r, e) {
  var t = "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"];
  if (!t) {
    if (Array.isArray(r) || (t = _unsupportedIterableToArray(r)) || e) {
      t && (r = t);
      var n = 0, F = function() {
      };
      return {
        s: F,
        n: function() {
          return n >= r.length ? {
            done: true
          } : {
            done: false,
            value: r[n++]
          };
        },
        e: function(r2) {
          throw r2;
        },
        f: F
      };
    }
    throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
  }
  var o, a = true, u = false;
  return {
    s: function() {
      t = t.call(r);
    },
    n: function() {
      var r2 = t.next();
      return a = r2.done, r2;
    },
    e: function(r2) {
      u = true, o = r2;
    },
    f: function() {
      try {
        a || null == t.return || t.return();
      } finally {
        if (u) throw o;
      }
    }
  };
}
function _defineProperty$1(e, r, t) {
  return (r = _toPropertyKey$1(r)) in e ? Object.defineProperty(e, r, {
    value: t,
    enumerable: true,
    configurable: true,
    writable: true
  }) : e[r] = t, e;
}
function _iterableToArray(r) {
  if ("undefined" != typeof Symbol && null != r[Symbol.iterator] || null != r["@@iterator"]) return Array.from(r);
}
function _nonIterableSpread() {
  throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function ownKeys(e, r) {
  var t = Object.keys(e);
  if (Object.getOwnPropertySymbols) {
    var o = Object.getOwnPropertySymbols(e);
    r && (o = o.filter(function(r2) {
      return Object.getOwnPropertyDescriptor(e, r2).enumerable;
    })), t.push.apply(t, o);
  }
  return t;
}
function _objectSpread2(e) {
  for (var r = 1; r < arguments.length; r++) {
    var t = null != arguments[r] ? arguments[r] : {};
    r % 2 ? ownKeys(Object(t), true).forEach(function(r2) {
      _defineProperty$1(e, r2, t[r2]);
    }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function(r2) {
      Object.defineProperty(e, r2, Object.getOwnPropertyDescriptor(t, r2));
    });
  }
  return e;
}
function _regenerator() {
  /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */
  var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag";
  function i(r2, n2, o2, i2) {
    var c2 = n2 && n2.prototype instanceof Generator ? n2 : Generator, u2 = Object.create(c2.prototype);
    return _regeneratorDefine(u2, "_invoke", function(r3, n3, o3) {
      var i3, c3, u3, f2 = 0, p = o3 || [], y = false, G = {
        p: 0,
        n: 0,
        v: e,
        a: d,
        f: d.bind(e, 4),
        d: function(t2, r4) {
          return i3 = t2, c3 = 0, u3 = e, G.n = r4, a;
        }
      };
      function d(r4, n4) {
        for (c3 = r4, u3 = n4, t = 0; !y && f2 && !o4 && t < p.length; t++) {
          var o4, i4 = p[t], d2 = G.p, l = i4[2];
          r4 > 3 ? (o4 = l === n4) && (u3 = i4[(c3 = i4[4]) ? 5 : (c3 = 3, 3)], i4[4] = i4[5] = e) : i4[0] <= d2 && ((o4 = r4 < 2 && d2 < i4[1]) ? (c3 = 0, G.v = n4, G.n = i4[1]) : d2 < l && (o4 = r4 < 3 || i4[0] > n4 || n4 > l) && (i4[4] = r4, i4[5] = n4, G.n = l, c3 = 0));
        }
        if (o4 || r4 > 1) return a;
        throw y = true, n4;
      }
      return function(o4, p2, l) {
        if (f2 > 1) throw TypeError("Generator is already running");
        for (y && 1 === p2 && d(p2, l), c3 = p2, u3 = l; (t = c3 < 2 ? e : u3) || !y; ) {
          i3 || (c3 ? c3 < 3 ? (c3 > 1 && (G.n = -1), d(c3, u3)) : G.n = u3 : G.v = u3);
          try {
            if (f2 = 2, i3) {
              if (c3 || (o4 = "next"), t = i3[o4]) {
                if (!(t = t.call(i3, u3))) throw TypeError("iterator result is not an object");
                if (!t.done) return t;
                u3 = t.value, c3 < 2 && (c3 = 0);
              } else 1 === c3 && (t = i3.return) && t.call(i3), c3 < 2 && (u3 = TypeError("The iterator does not provide a '" + o4 + "' method"), c3 = 1);
              i3 = e;
            } else if ((t = (y = G.n < 0) ? u3 : r3.call(n3, G)) !== a) break;
          } catch (t2) {
            i3 = e, c3 = 1, u3 = t2;
          } finally {
            f2 = 1;
          }
        }
        return {
          value: t,
          done: y
        };
      };
    }(r2, o2, i2), true), u2;
  }
  var a = {};
  function Generator() {
  }
  function GeneratorFunction() {
  }
  function GeneratorFunctionPrototype() {
  }
  t = Object.getPrototypeOf;
  var c = [][n] ? t(t([][n]())) : (_regeneratorDefine(t = {}, n, function() {
    return this;
  }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c);
  function f(e2) {
    return Object.setPrototypeOf ? Object.setPrototypeOf(e2, GeneratorFunctionPrototype) : (e2.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine(e2, o, "GeneratorFunction")), e2.prototype = Object.create(u), e2;
  }
  return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine(u), _regeneratorDefine(u, o, "Generator"), _regeneratorDefine(u, n, function() {
    return this;
  }), _regeneratorDefine(u, "toString", function() {
    return "[object Generator]";
  }), (_regenerator = function() {
    return {
      w: i,
      m: f
    };
  })();
}
function _regeneratorDefine(e, r, n, t) {
  var i = Object.defineProperty;
  try {
    i({}, "", {});
  } catch (e2) {
    i = 0;
  }
  _regeneratorDefine = function(e2, r2, n2, t2) {
    function o(r3, n3) {
      _regeneratorDefine(e2, r3, function(e3) {
        return this._invoke(r3, n3, e3);
      });
    }
    r2 ? i ? i(e2, r2, {
      value: n2,
      enumerable: !t2,
      configurable: !t2,
      writable: !t2
    }) : e2[r2] = n2 : (o("next", 0), o("throw", 1), o("return", 2));
  }, _regeneratorDefine(e, r, n, t);
}
function _toConsumableArray(r) {
  return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread();
}
function _toPrimitive$1(t, r) {
  if ("object" != typeof t || !t) return t;
  var e = t[Symbol.toPrimitive];
  if (void 0 !== e) {
    var i = e.call(t, r);
    if ("object" != typeof i) return i;
    throw new TypeError("@@toPrimitive must return a primitive value.");
  }
  return ("string" === r ? String : Number)(t);
}
function _toPropertyKey$1(t) {
  var i = _toPrimitive$1(t, "string");
  return "symbol" == typeof i ? i : i + "";
}
function _unsupportedIterableToArray(r, a) {
  if (r) {
    if ("string" == typeof r) return _arrayLikeToArray(r, a);
    var t = {}.toString.call(r).slice(8, -1);
    return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0;
  }
}
var activeFocusTraps = {
  // Returns the trap from the top of the stack.
  getActiveTrap: function getActiveTrap(trapStack) {
    if ((trapStack === null || trapStack === void 0 ? void 0 : trapStack.length) > 0) {
      return trapStack[trapStack.length - 1];
    }
    return null;
  },
  // Pauses the currently active trap, then adds a new trap to the stack.
  activateTrap: function activateTrap(trapStack, trap) {
    var activeTrap = activeFocusTraps.getActiveTrap(trapStack);
    if (trap !== activeTrap) {
      activeFocusTraps.pauseTrap(trapStack);
    }
    var trapIndex = trapStack.indexOf(trap);
    if (trapIndex === -1) {
      trapStack.push(trap);
    } else {
      trapStack.splice(trapIndex, 1);
      trapStack.push(trap);
    }
  },
  // Removes the trap from the top of the stack, then unpauses the next trap down.
  deactivateTrap: function deactivateTrap(trapStack, trap) {
    var trapIndex = trapStack.indexOf(trap);
    if (trapIndex !== -1) {
      trapStack.splice(trapIndex, 1);
    }
    activeFocusTraps.unpauseTrap(trapStack);
  },
  // Pauses the trap at the top of the stack.
  pauseTrap: function pauseTrap(trapStack) {
    var activeTrap = activeFocusTraps.getActiveTrap(trapStack);
    activeTrap === null || activeTrap === void 0 || activeTrap._setPausedState(true);
  },
  // Unpauses the trap at the top of the stack.
  unpauseTrap: function unpauseTrap(trapStack) {
    var activeTrap = activeFocusTraps.getActiveTrap(trapStack);
    if (activeTrap && !activeTrap._isManuallyPaused()) {
      activeTrap._setPausedState(false);
    }
  }
};
var isSelectableInput = function isSelectableInput2(node) {
  return node.tagName && node.tagName.toLowerCase() === "input" && typeof node.select === "function";
};
var isEscapeEvent = function isEscapeEvent2(e) {
  return (e === null || e === void 0 ? void 0 : e.key) === "Escape" || (e === null || e === void 0 ? void 0 : e.key) === "Esc" || (e === null || e === void 0 ? void 0 : e.keyCode) === 27;
};
var isTabEvent = function isTabEvent2(e) {
  return (e === null || e === void 0 ? void 0 : e.key) === "Tab" || (e === null || e === void 0 ? void 0 : e.keyCode) === 9;
};
var isKeyForward = function isKeyForward2(e) {
  return isTabEvent(e) && !e.shiftKey;
};
var isKeyBackward = function isKeyBackward2(e) {
  return isTabEvent(e) && e.shiftKey;
};
var delay = function delay2(fn) {
  return setTimeout(fn, 0);
};
var valueOrHandler = function valueOrHandler2(value) {
  for (var _len = arguments.length, params = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
    params[_key - 1] = arguments[_key];
  }
  return typeof value === "function" ? value.apply(void 0, params) : value;
};
var getActualTarget = function getActualTarget2(event) {
  return event.target.shadowRoot && typeof event.composedPath === "function" ? event.composedPath()[0] : event.target;
};
var internalTrapStack = [];
var createFocusTrap$1 = function createFocusTrap(elements, userOptions) {
  var doc = (userOptions === null || userOptions === void 0 ? void 0 : userOptions.document) || document;
  var trapStack = (userOptions === null || userOptions === void 0 ? void 0 : userOptions.trapStack) || internalTrapStack;
  var config = _objectSpread2({
    returnFocusOnDeactivate: true,
    escapeDeactivates: true,
    delayInitialFocus: true,
    isolateSubtrees: false,
    isKeyForward,
    isKeyBackward
  }, userOptions);
  var state = {
    // containers given to createFocusTrap()
    /** @type {Array<HTMLElement>} */
    containers: [],
    // list of objects identifying tabbable nodes in `containers` in the trap
    // NOTE: it's possible that a group has no tabbable nodes if nodes get removed while the trap
    //  is active, but the trap should never get to a state where there isn't at least one group
    //  with at least one tabbable node in it (that would lead to an error condition that would
    //  result in an error being thrown)
    /** @type {Array<{
     *    container: HTMLElement,
     *    tabbableNodes: Array<HTMLElement>, // empty if none
     *    focusableNodes: Array<HTMLElement>, // empty if none
     *    posTabIndexesFound: boolean,
     *    firstTabbableNode: HTMLElement|undefined,
     *    lastTabbableNode: HTMLElement|undefined,
     *    firstDomTabbableNode: HTMLElement|undefined,
     *    lastDomTabbableNode: HTMLElement|undefined,
     *    nextTabbableNode: (node: HTMLElement, forward: boolean) => HTMLElement|undefined
     *  }>}
     */
    containerGroups: [],
    // same order/length as `containers` list
    // references to objects in `containerGroups`, but only those that actually have
    //  tabbable nodes in them
    // NOTE: same order as `containers` and `containerGroups`, but __not necessarily__
    //  the same length
    tabbableGroups: [],
    // references to nodes that are siblings to the ancestors of this trap's containers.
    /** @type {Set<HTMLElement>} */
    adjacentElements: /* @__PURE__ */ new Set(),
    // references to nodes that were inert or aria-hidden before the trap was activated.
    /** @type {Set<HTMLElement>} */
    alreadySilent: /* @__PURE__ */ new Set(),
    nodeFocusedBeforeActivation: null,
    mostRecentlyFocusedNode: null,
    active: false,
    paused: false,
    manuallyPaused: false,
    // timer ID for when delayInitialFocus is true and initial focus in this trap
    //  has been delayed during activation
    delayInitialFocusTimer: void 0,
    // the most recent KeyboardEvent for the configured nav key (typically [SHIFT+]TAB), if any
    recentNavEvent: void 0
  };
  var trap;
  var getOption = function getOption2(configOverrideOptions, optionName, configOptionName) {
    return configOverrideOptions && configOverrideOptions[optionName] !== void 0 ? configOverrideOptions[optionName] : config[configOptionName || optionName];
  };
  var findContainerIndex = function findContainerIndex2(element, event) {
    var composedPath = typeof (event === null || event === void 0 ? void 0 : event.composedPath) === "function" ? event.composedPath() : void 0;
    return state.containerGroups.findIndex(function(_ref) {
      var container = _ref.container, tabbableNodes = _ref.tabbableNodes;
      return container.contains(element) || // fall back to explicit tabbable search which will take into consideration any
      //  web components if the `tabbableOptions.getShadowRoot` option was used for
      //  the trap, enabling shadow DOM support in tabbable (`Node.contains()` doesn't
      //  look inside web components even if open)
      (composedPath === null || composedPath === void 0 ? void 0 : composedPath.includes(container)) || tabbableNodes.find(function(node) {
        return node === element;
      });
    });
  };
  var getNodeForOption = function getNodeForOption2(optionName) {
    var _ref2 = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {}, _ref2$hasFallback = _ref2.hasFallback, hasFallback = _ref2$hasFallback === void 0 ? false : _ref2$hasFallback, _ref2$params = _ref2.params, params = _ref2$params === void 0 ? [] : _ref2$params;
    var optionValue = config[optionName];
    if (typeof optionValue === "function") {
      optionValue = optionValue.apply(void 0, _toConsumableArray(params));
    }
    if (optionValue === true) {
      optionValue = void 0;
    }
    if (!optionValue) {
      if (optionValue === void 0 || optionValue === false) {
        return optionValue;
      }
      throw new Error("`".concat(optionName, "` was specified but was not a node, or did not return a node"));
    }
    var node = optionValue;
    if (typeof optionValue === "string") {
      try {
        node = doc.querySelector(optionValue);
      } catch (err) {
        throw new Error("`".concat(optionName, '` appears to be an invalid selector; error="').concat(err.message, '"'));
      }
      if (!node) {
        if (!hasFallback) {
          throw new Error("`".concat(optionName, "` as selector refers to no known node"));
        }
      }
    }
    return node;
  };
  var getInitialFocusNode = function getInitialFocusNode2() {
    var node = getNodeForOption("initialFocus", {
      hasFallback: true
    });
    if (node === false) {
      return false;
    }
    if (node === void 0 || node && !isFocusable$1(node, config.tabbableOptions)) {
      if (findContainerIndex(doc.activeElement) >= 0) {
        node = doc.activeElement;
      } else {
        var firstTabbableGroup = state.tabbableGroups[0];
        var firstTabbableNode = firstTabbableGroup && firstTabbableGroup.firstTabbableNode;
        node = firstTabbableNode || getNodeForOption("fallbackFocus");
      }
    } else if (node === null) {
      node = getNodeForOption("fallbackFocus");
    }
    if (!node) {
      throw new Error("Your focus-trap needs to have at least one focusable element");
    }
    return node;
  };
  var updateTabbableNodes = function updateTabbableNodes2() {
    state.containerGroups = state.containers.map(function(container) {
      var tabbableNodes = tabbable(container, config.tabbableOptions);
      var focusableNodes = focusable(container, config.tabbableOptions);
      var firstTabbableNode = tabbableNodes.length > 0 ? tabbableNodes[0] : void 0;
      var lastTabbableNode = tabbableNodes.length > 0 ? tabbableNodes[tabbableNodes.length - 1] : void 0;
      var firstDomTabbableNode = focusableNodes.find(function(node) {
        return isTabbable(node);
      });
      var lastDomTabbableNode = focusableNodes.slice().reverse().find(function(node) {
        return isTabbable(node);
      });
      var posTabIndexesFound = !!tabbableNodes.find(function(node) {
        return getTabIndex(node) > 0;
      });
      return {
        container,
        tabbableNodes,
        focusableNodes,
        /** True if at least one node with positive `tabindex` was found in this container. */
        posTabIndexesFound,
        /** First tabbable node in container, __tabindex__ order; `undefined` if none. */
        firstTabbableNode,
        /** Last tabbable node in container, __tabindex__ order; `undefined` if none. */
        lastTabbableNode,
        // NOTE: DOM order is NOT NECESSARILY "document position" order, but figuring that out
        //  would require more than just https://developer.mozilla.org/en-US/docs/Web/API/Node/compareDocumentPosition
        //  because that API doesn't work with Shadow DOM as well as it should (@see
        //  https://github.com/whatwg/dom/issues/320) and since this first/last is only needed, so far,
        //  to address an edge case related to positive tabindex support, this seems like a much easier,
        //  "close enough most of the time" alternative for positive tabindexes which should generally
        //  be avoided anyway...
        /** First tabbable node in container, __DOM__ order; `undefined` if none. */
        firstDomTabbableNode,
        /** Last tabbable node in container, __DOM__ order; `undefined` if none. */
        lastDomTabbableNode,
        /**
         * Finds the __tabbable__ node that follows the given node in the specified direction,
         *  in this container, if any.
         * @param {HTMLElement} node
         * @param {boolean} [forward] True if going in forward tab order; false if going
         *  in reverse.
         * @returns {HTMLElement|undefined} The next tabbable node, if any.
         */
        nextTabbableNode: function nextTabbableNode(node) {
          var forward = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : true;
          var nodeIdx = tabbableNodes.indexOf(node);
          if (nodeIdx < 0) {
            if (forward) {
              return focusableNodes.slice(focusableNodes.indexOf(node) + 1).find(function(el) {
                return isTabbable(el);
              });
            }
            return focusableNodes.slice(0, focusableNodes.indexOf(node)).reverse().find(function(el) {
              return isTabbable(el);
            });
          }
          return tabbableNodes[nodeIdx + (forward ? 1 : -1)];
        }
      };
    });
    state.tabbableGroups = state.containerGroups.filter(function(group) {
      return group.tabbableNodes.length > 0;
    });
    if (state.tabbableGroups.length <= 0 && !getNodeForOption("fallbackFocus")) {
      throw new Error("Your focus-trap must have at least one container with at least one tabbable node in it at all times");
    }
    if (state.containerGroups.find(function(g) {
      return g.posTabIndexesFound;
    }) && state.containerGroups.length > 1) {
      throw new Error("At least one node with a positive tabindex was found in one of your focus-trap's multiple containers. Positive tabindexes are only supported in single-container focus-traps.");
    }
  };
  var _getActiveElement = function getActiveElement(el) {
    var activeElement = el.activeElement;
    if (!activeElement) {
      return;
    }
    if (activeElement.shadowRoot && activeElement.shadowRoot.activeElement !== null) {
      return _getActiveElement(activeElement.shadowRoot);
    }
    return activeElement;
  };
  var _tryFocus = function tryFocus(node) {
    if (node === false) {
      return;
    }
    if (node === _getActiveElement(document)) {
      return;
    }
    if (!node || !node.focus) {
      _tryFocus(getInitialFocusNode());
      return;
    }
    node.focus({
      preventScroll: !!config.preventScroll
    });
    state.mostRecentlyFocusedNode = node;
    if (isSelectableInput(node)) {
      node.select();
    }
  };
  var getReturnFocusNode = function getReturnFocusNode2(previousActiveElement) {
    var node = getNodeForOption("setReturnFocus", {
      params: [previousActiveElement]
    });
    return node ? node : node === false ? false : previousActiveElement;
  };
  var findNextNavNode = function findNextNavNode2(_ref3) {
    var target = _ref3.target, event = _ref3.event, _ref3$isBackward = _ref3.isBackward, isBackward = _ref3$isBackward === void 0 ? false : _ref3$isBackward;
    target = target || getActualTarget(event);
    updateTabbableNodes();
    var destinationNode = null;
    if (state.tabbableGroups.length > 0) {
      var containerIndex = findContainerIndex(target, event);
      var containerGroup = containerIndex >= 0 ? state.containerGroups[containerIndex] : void 0;
      if (containerIndex < 0) {
        if (isBackward) {
          destinationNode = state.tabbableGroups[state.tabbableGroups.length - 1].lastTabbableNode;
        } else {
          destinationNode = state.tabbableGroups[0].firstTabbableNode;
        }
      } else if (isBackward) {
        var startOfGroupIndex = state.tabbableGroups.findIndex(function(_ref4) {
          var firstTabbableNode = _ref4.firstTabbableNode;
          return target === firstTabbableNode;
        });
        if (startOfGroupIndex < 0 && (containerGroup.container === target || isFocusable$1(target, config.tabbableOptions) && !isTabbable(target, config.tabbableOptions) && !containerGroup.nextTabbableNode(target, false))) {
          startOfGroupIndex = containerIndex;
        }
        if (startOfGroupIndex >= 0) {
          var destinationGroupIndex = startOfGroupIndex === 0 ? state.tabbableGroups.length - 1 : startOfGroupIndex - 1;
          var destinationGroup = state.tabbableGroups[destinationGroupIndex];
          destinationNode = getTabIndex(target) >= 0 ? destinationGroup.lastTabbableNode : destinationGroup.lastDomTabbableNode;
        } else if (!isTabEvent(event)) {
          destinationNode = containerGroup.nextTabbableNode(target, false);
        }
      } else {
        var lastOfGroupIndex = state.tabbableGroups.findIndex(function(_ref5) {
          var lastTabbableNode = _ref5.lastTabbableNode;
          return target === lastTabbableNode;
        });
        if (lastOfGroupIndex < 0 && (containerGroup.container === target || isFocusable$1(target, config.tabbableOptions) && !isTabbable(target, config.tabbableOptions) && !containerGroup.nextTabbableNode(target))) {
          lastOfGroupIndex = containerIndex;
        }
        if (lastOfGroupIndex >= 0) {
          var _destinationGroupIndex = lastOfGroupIndex === state.tabbableGroups.length - 1 ? 0 : lastOfGroupIndex + 1;
          var _destinationGroup = state.tabbableGroups[_destinationGroupIndex];
          destinationNode = getTabIndex(target) >= 0 ? _destinationGroup.firstTabbableNode : _destinationGroup.firstDomTabbableNode;
        } else if (!isTabEvent(event)) {
          destinationNode = containerGroup.nextTabbableNode(target);
        }
      }
    } else {
      destinationNode = getNodeForOption("fallbackFocus");
    }
    return destinationNode;
  };
  var checkPointerDown = function checkPointerDown2(e) {
    var target = getActualTarget(e);
    if (findContainerIndex(target, e) >= 0) {
      return;
    }
    if (valueOrHandler(config.clickOutsideDeactivates, e)) {
      trap.deactivate({
        // NOTE: by setting `returnFocus: false`, deactivate() will do nothing,
        //  which will result in the outside click setting focus to the node
        //  that was clicked (and if not focusable, to "nothing"); by setting
        //  `returnFocus: true`, we'll attempt to re-focus the node originally-focused
        //  on activation (or the configured `setReturnFocus` node), whether the
        //  outside click was on a focusable node or not
        returnFocus: config.returnFocusOnDeactivate
      });
      return;
    }
    if (valueOrHandler(config.allowOutsideClick, e)) {
      return;
    }
    e.preventDefault();
  };
  var checkFocusIn = function checkFocusIn2(event) {
    var target = getActualTarget(event);
    var targetContained = findContainerIndex(target, event) >= 0;
    if (targetContained || target instanceof Document) {
      if (targetContained) {
        state.mostRecentlyFocusedNode = target;
      }
    } else {
      event.stopImmediatePropagation();
      var nextNode;
      var navAcrossContainers = true;
      if (state.mostRecentlyFocusedNode) {
        if (getTabIndex(state.mostRecentlyFocusedNode) > 0) {
          var mruContainerIdx = findContainerIndex(state.mostRecentlyFocusedNode);
          var tabbableNodes = state.containerGroups[mruContainerIdx].tabbableNodes;
          if (tabbableNodes.length > 0) {
            var mruTabIdx = tabbableNodes.findIndex(function(node) {
              return node === state.mostRecentlyFocusedNode;
            });
            if (mruTabIdx >= 0) {
              if (config.isKeyForward(state.recentNavEvent)) {
                if (mruTabIdx + 1 < tabbableNodes.length) {
                  nextNode = tabbableNodes[mruTabIdx + 1];
                  navAcrossContainers = false;
                }
              } else {
                if (mruTabIdx - 1 >= 0) {
                  nextNode = tabbableNodes[mruTabIdx - 1];
                  navAcrossContainers = false;
                }
              }
            }
          }
        } else {
          if (!state.containerGroups.some(function(g) {
            return g.tabbableNodes.some(function(n) {
              return getTabIndex(n) > 0;
            });
          })) {
            navAcrossContainers = false;
          }
        }
      } else {
        navAcrossContainers = false;
      }
      if (navAcrossContainers) {
        nextNode = findNextNavNode({
          // move FROM the MRU node, not event-related node (which will be the node that is
          //  outside the trap causing the focus escape we're trying to fix)
          target: state.mostRecentlyFocusedNode,
          isBackward: config.isKeyBackward(state.recentNavEvent)
        });
      }
      if (nextNode) {
        _tryFocus(nextNode);
      } else {
        _tryFocus(state.mostRecentlyFocusedNode || getInitialFocusNode());
      }
    }
    state.recentNavEvent = void 0;
  };
  var checkKeyNav = function checkKeyNav2(event) {
    var isBackward = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : false;
    state.recentNavEvent = event;
    var destinationNode = findNextNavNode({
      event,
      isBackward
    });
    if (destinationNode) {
      if (isTabEvent(event)) {
        event.preventDefault();
      }
      _tryFocus(destinationNode);
    }
  };
  var checkTabKey = function checkTabKey2(event) {
    if (config.isKeyForward(event) || config.isKeyBackward(event)) {
      checkKeyNav(event, config.isKeyBackward(event));
    }
  };
  var checkEscapeKey = function checkEscapeKey2(event) {
    if (isEscapeEvent(event) && valueOrHandler(config.escapeDeactivates, event) !== false) {
      event.preventDefault();
      trap.deactivate();
    }
  };
  var checkClick = function checkClick2(e) {
    var target = getActualTarget(e);
    if (findContainerIndex(target, e) >= 0) {
      return;
    }
    if (valueOrHandler(config.clickOutsideDeactivates, e)) {
      return;
    }
    if (valueOrHandler(config.allowOutsideClick, e)) {
      return;
    }
    e.preventDefault();
    e.stopImmediatePropagation();
  };
  var addListeners = function addListeners2() {
    if (!state.active) {
      return Promise.resolve();
    }
    activeFocusTraps.activateTrap(trapStack, trap);
    var promise;
    if (config.delayInitialFocus) {
      promise = new Promise(function(resolve) {
        state.delayInitialFocusTimer = delay(function() {
          _tryFocus(getInitialFocusNode());
          resolve();
        });
      });
    } else {
      promise = Promise.resolve();
      _tryFocus(getInitialFocusNode());
    }
    doc.addEventListener("focusin", checkFocusIn, true);
    doc.addEventListener("mousedown", checkPointerDown, {
      capture: true,
      passive: false
    });
    doc.addEventListener("touchstart", checkPointerDown, {
      capture: true,
      passive: false
    });
    doc.addEventListener("click", checkClick, {
      capture: true,
      passive: false
    });
    doc.addEventListener("keydown", checkTabKey, {
      capture: true,
      passive: false
    });
    doc.addEventListener("keydown", checkEscapeKey);
    return promise;
  };
  var collectAdjacentElements = function collectAdjacentElements2(containers) {
    if (state.active && !state.paused) {
      trap._setSubtreeIsolation(false);
    }
    state.adjacentElements.clear();
    state.alreadySilent.clear();
    var containerAncestors = /* @__PURE__ */ new Set();
    var adjacentElements = /* @__PURE__ */ new Set();
    var _iterator = _createForOfIteratorHelper(containers), _step;
    try {
      for (_iterator.s(); !(_step = _iterator.n()).done; ) {
        var container = _step.value;
        containerAncestors.add(container);
        var insideShadowRoot = typeof ShadowRoot !== "undefined" && container.getRootNode() instanceof ShadowRoot;
        var current = container;
        while (current) {
          containerAncestors.add(current);
          var parent = current.parentElement;
          var siblings = [];
          if (parent) {
            siblings = parent.children;
          } else if (!parent && insideShadowRoot) {
            siblings = current.getRootNode().children;
            parent = current.getRootNode().host;
            insideShadowRoot = typeof ShadowRoot !== "undefined" && parent.getRootNode() instanceof ShadowRoot;
          }
          var _iterator2 = _createForOfIteratorHelper(siblings), _step2;
          try {
            for (_iterator2.s(); !(_step2 = _iterator2.n()).done; ) {
              var child = _step2.value;
              adjacentElements.add(child);
            }
          } catch (err) {
            _iterator2.e(err);
          } finally {
            _iterator2.f();
          }
          current = parent;
        }
      }
    } catch (err) {
      _iterator.e(err);
    } finally {
      _iterator.f();
    }
    containerAncestors.forEach(function(el) {
      adjacentElements["delete"](el);
    });
    state.adjacentElements = adjacentElements;
  };
  var removeListeners = function removeListeners2() {
    if (!state.active) {
      return;
    }
    doc.removeEventListener("focusin", checkFocusIn, true);
    doc.removeEventListener("mousedown", checkPointerDown, true);
    doc.removeEventListener("touchstart", checkPointerDown, true);
    doc.removeEventListener("click", checkClick, true);
    doc.removeEventListener("keydown", checkTabKey, true);
    doc.removeEventListener("keydown", checkEscapeKey);
    return trap;
  };
  var checkDomRemoval = function checkDomRemoval2(mutations) {
    var isFocusedNodeRemoved = mutations.some(function(mutation) {
      var removedNodes = Array.from(mutation.removedNodes);
      return removedNodes.some(function(node) {
        return node === state.mostRecentlyFocusedNode;
      });
    });
    if (isFocusedNodeRemoved) {
      _tryFocus(getInitialFocusNode());
    }
  };
  var mutationObserver = typeof window !== "undefined" && "MutationObserver" in window ? new MutationObserver(checkDomRemoval) : void 0;
  var updateObservedNodes = function updateObservedNodes2() {
    if (!mutationObserver) {
      return;
    }
    mutationObserver.disconnect();
    if (state.active && !state.paused) {
      state.containers.map(function(container) {
        mutationObserver.observe(container, {
          subtree: true,
          childList: true
        });
      });
    }
  };
  trap = {
    get active() {
      return state.active;
    },
    get paused() {
      return state.paused;
    },
    activate: function activate(activateOptions) {
      if (state.active) {
        return this;
      }
      var onActivate = getOption(activateOptions, "onActivate");
      var onPostActivate = getOption(activateOptions, "onPostActivate");
      var checkCanFocusTrap = getOption(activateOptions, "checkCanFocusTrap");
      var preexistingTrap = activeFocusTraps.getActiveTrap(trapStack);
      var revertState = false;
      if (preexistingTrap && !preexistingTrap.paused) {
        var _preexistingTrap$_set;
        (_preexistingTrap$_set = preexistingTrap._setSubtreeIsolation) === null || _preexistingTrap$_set === void 0 || _preexistingTrap$_set.call(preexistingTrap, false);
        revertState = true;
      }
      try {
        if (!checkCanFocusTrap) {
          updateTabbableNodes();
        }
        state.active = true;
        state.paused = false;
        state.nodeFocusedBeforeActivation = _getActiveElement(doc);
        onActivate === null || onActivate === void 0 || onActivate();
        var finishActivation = /* @__PURE__ */ function() {
          var _ref6 = _asyncToGenerator(/* @__PURE__ */ _regenerator().m(function _callee() {
            return _regenerator().w(function(_context) {
              while (1) switch (_context.n) {
                case 0:
                  if (checkCanFocusTrap) {
                    updateTabbableNodes();
                  }
                  _context.n = 1;
                  return addListeners();
                case 1:
                  trap._setSubtreeIsolation(true);
                  updateObservedNodes();
                  onPostActivate === null || onPostActivate === void 0 || onPostActivate();
                case 2:
                  return _context.a(2);
              }
            }, _callee);
          }));
          return function finishActivation2() {
            return _ref6.apply(this, arguments);
          };
        }();
        if (checkCanFocusTrap) {
          checkCanFocusTrap(state.containers.concat()).then(finishActivation, finishActivation);
          return this;
        }
        finishActivation();
      } catch (error) {
        if (preexistingTrap === activeFocusTraps.getActiveTrap(trapStack) && revertState) {
          var _preexistingTrap$_set2;
          (_preexistingTrap$_set2 = preexistingTrap._setSubtreeIsolation) === null || _preexistingTrap$_set2 === void 0 || _preexistingTrap$_set2.call(preexistingTrap, true);
        }
        throw error;
      }
      return this;
    },
    deactivate: function deactivate(deactivateOptions) {
      if (!state.active) {
        return this;
      }
      var options = _objectSpread2({
        onDeactivate: config.onDeactivate,
        onPostDeactivate: config.onPostDeactivate,
        checkCanReturnFocus: config.checkCanReturnFocus
      }, deactivateOptions);
      clearTimeout(state.delayInitialFocusTimer);
      state.delayInitialFocusTimer = void 0;
      if (!state.paused) {
        trap._setSubtreeIsolation(false);
      }
      state.alreadySilent.clear();
      removeListeners();
      state.active = false;
      state.paused = false;
      updateObservedNodes();
      activeFocusTraps.deactivateTrap(trapStack, trap);
      var onDeactivate = getOption(options, "onDeactivate");
      var onPostDeactivate = getOption(options, "onPostDeactivate");
      var checkCanReturnFocus = getOption(options, "checkCanReturnFocus");
      var returnFocus = getOption(options, "returnFocus", "returnFocusOnDeactivate");
      onDeactivate === null || onDeactivate === void 0 || onDeactivate();
      var finishDeactivation = function finishDeactivation2() {
        delay(function() {
          if (returnFocus) {
            _tryFocus(getReturnFocusNode(state.nodeFocusedBeforeActivation));
          }
          onPostDeactivate === null || onPostDeactivate === void 0 || onPostDeactivate();
        });
      };
      if (returnFocus && checkCanReturnFocus) {
        checkCanReturnFocus(getReturnFocusNode(state.nodeFocusedBeforeActivation)).then(finishDeactivation, finishDeactivation);
        return this;
      }
      finishDeactivation();
      return this;
    },
    pause: function pause(pauseOptions) {
      if (!state.active) {
        return this;
      }
      state.manuallyPaused = true;
      return this._setPausedState(true, pauseOptions);
    },
    unpause: function unpause(unpauseOptions) {
      if (!state.active) {
        return this;
      }
      state.manuallyPaused = false;
      if (trapStack[trapStack.length - 1] !== this) {
        return this;
      }
      return this._setPausedState(false, unpauseOptions);
    },
    updateContainerElements: function updateContainerElements(containerElements) {
      var elementsAsArray = [].concat(containerElements).filter(Boolean);
      state.containers = elementsAsArray.map(function(element) {
        return typeof element === "string" ? doc.querySelector(element) : element;
      });
      if (config.isolateSubtrees) {
        collectAdjacentElements(state.containers);
      }
      if (state.active) {
        updateTabbableNodes();
        if (!state.paused) {
          trap._setSubtreeIsolation(true);
        }
      }
      updateObservedNodes();
      return this;
    }
  };
  Object.defineProperties(trap, {
    _isManuallyPaused: {
      value: function value() {
        return state.manuallyPaused;
      }
    },
    _setPausedState: {
      value: function value(paused, options) {
        if (state.paused === paused) {
          return this;
        }
        state.paused = paused;
        if (paused) {
          var onPause = getOption(options, "onPause");
          var onPostPause = getOption(options, "onPostPause");
          onPause === null || onPause === void 0 || onPause();
          removeListeners();
          trap._setSubtreeIsolation(false);
          updateObservedNodes();
          onPostPause === null || onPostPause === void 0 || onPostPause();
        } else {
          var onUnpause = getOption(options, "onUnpause");
          var onPostUnpause = getOption(options, "onPostUnpause");
          onUnpause === null || onUnpause === void 0 || onUnpause();
          var finishUnpause = /* @__PURE__ */ function() {
            var _ref7 = _asyncToGenerator(/* @__PURE__ */ _regenerator().m(function _callee2() {
              return _regenerator().w(function(_context2) {
                while (1) switch (_context2.n) {
                  case 0:
                    updateTabbableNodes();
                    _context2.n = 1;
                    return addListeners();
                  case 1:
                    trap._setSubtreeIsolation(true);
                    updateObservedNodes();
                    onPostUnpause === null || onPostUnpause === void 0 || onPostUnpause();
                  case 2:
                    return _context2.a(2);
                }
              }, _callee2);
            }));
            return function finishUnpause2() {
              return _ref7.apply(this, arguments);
            };
          }();
          finishUnpause();
        }
        return this;
      }
    },
    _setSubtreeIsolation: {
      value: function value(isEnabled) {
        if (config.isolateSubtrees) {
          state.adjacentElements.forEach(function(el) {
            var _el$getAttribute;
            if (isEnabled) {
              switch (config.isolateSubtrees) {
                case "aria-hidden":
                  if (el.ariaHidden === "true" || ((_el$getAttribute = el.getAttribute("aria-hidden")) === null || _el$getAttribute === void 0 ? void 0 : _el$getAttribute.toLowerCase()) === "true") {
                    state.alreadySilent.add(el);
                  }
                  el.setAttribute("aria-hidden", "true");
                  break;
                default:
                  if (el.inert || el.hasAttribute("inert")) {
                    state.alreadySilent.add(el);
                  }
                  el.setAttribute("inert", true);
                  break;
              }
            } else {
              if (state.alreadySilent.has(el)) ;
              else {
                switch (config.isolateSubtrees) {
                  case "aria-hidden":
                    el.removeAttribute("aria-hidden");
                    break;
                  default:
                    el.removeAttribute("inert");
                    break;
                }
              }
            }
          });
        }
      }
    }
  });
  trap.updateContainerElements(elements);
  return trap;
};
const focusTrap_esm = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  createFocusTrap: createFocusTrap$1
}, Symbol.toStringTag, { value: "Module" }));
const require$$1 = /* @__PURE__ */ getAugmentedNamespace(focusTrap_esm);
const require$$2 = /* @__PURE__ */ getAugmentedNamespace(index_esm);
function _typeof(o) {
  "@babel/helpers - typeof";
  return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function(o2) {
    return typeof o2;
  } : function(o2) {
    return o2 && "function" == typeof Symbol && o2.constructor === Symbol && o2 !== Symbol.prototype ? "symbol" : typeof o2;
  }, _typeof(o);
}
var _exec$, _exec;
function _classCallCheck(a, n) {
  if (!(a instanceof n)) throw new TypeError("Cannot call a class as a function");
}
function _defineProperties(e, r) {
  for (var t = 0; t < r.length; t++) {
    var o = r[t];
    o.enumerable = o.enumerable || false, o.configurable = true, "value" in o && (o.writable = true), Object.defineProperty(e, _toPropertyKey(o.key), o);
  }
}
function _createClass(e, r, t) {
  return r && _defineProperties(e.prototype, r), Object.defineProperty(e, "prototype", { writable: false }), e;
}
function _callSuper(t, o, e) {
  return o = _getPrototypeOf(o), _possibleConstructorReturn(t, _isNativeReflectConstruct() ? Reflect.construct(o, e || [], _getPrototypeOf(t).constructor) : o.apply(t, e));
}
function _possibleConstructorReturn(t, e) {
  if (e && ("object" == _typeof(e) || "function" == typeof e)) return e;
  if (void 0 !== e) throw new TypeError("Derived constructors may only return object or undefined");
  return _assertThisInitialized(t);
}
function _assertThisInitialized(e) {
  if (void 0 === e) throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
  return e;
}
function _isNativeReflectConstruct() {
  try {
    var t = !Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function() {
    }));
  } catch (t2) {
  }
  return (_isNativeReflectConstruct = function _isNativeReflectConstruct2() {
    return !!t;
  })();
}
function _getPrototypeOf(t) {
  return _getPrototypeOf = Object.setPrototypeOf ? Object.getPrototypeOf.bind() : function(t2) {
    return t2.__proto__ || Object.getPrototypeOf(t2);
  }, _getPrototypeOf(t);
}
function _inherits(t, e) {
  if ("function" != typeof e && null !== e) throw new TypeError("Super expression must either be null or a function");
  t.prototype = Object.create(e && e.prototype, { constructor: { value: t, writable: true, configurable: true } }), Object.defineProperty(t, "prototype", { writable: false }), e && _setPrototypeOf(t, e);
}
function _setPrototypeOf(t, e) {
  return _setPrototypeOf = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function(t2, e2) {
    return t2.__proto__ = e2, t2;
  }, _setPrototypeOf(t, e);
}
function _defineProperty(e, r, t) {
  return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: true, configurable: true, writable: true }) : e[r] = t, e;
}
function _toPropertyKey(t) {
  var i = _toPrimitive(t, "string");
  return "symbol" == _typeof(i) ? i : i + "";
}
function _toPrimitive(t, r) {
  if ("object" != _typeof(t) || !t) return t;
  var e = t[Symbol.toPrimitive];
  if (void 0 !== e) {
    var i = e.call(t, r);
    if ("object" != _typeof(i)) return i;
    throw new TypeError("@@toPrimitive must return a primitive value.");
  }
  return ("string" === r ? String : Number)(t);
}
var React = reactExports;
var _require = require$$1, createFocusTrap2 = _require.createFocusTrap;
var _require2 = require$$2, isFocusable2 = _require2.isFocusable;
var reactVerMajor = parseInt((_exec$ = (_exec = /^(\d+)\./.exec(React.version)) === null || _exec === void 0 ? void 0 : _exec[1]) !== null && _exec$ !== void 0 ? _exec$ : 0, 10);
var FocusTrap$1 = /* @__PURE__ */ function(_React$Component) {
  function FocusTrap2(props) {
    var _this;
    _classCallCheck(this, FocusTrap2);
    _this = _callSuper(this, FocusTrap2, [props]);
    _defineProperty(_this, "getNodeForOption", function(optionName2) {
      var _this$internalOptions;
      var optionValue = (_this$internalOptions = this.internalOptions[optionName2]) !== null && _this$internalOptions !== void 0 ? _this$internalOptions : this.originalOptions[optionName2];
      if (typeof optionValue === "function") {
        for (var _len = arguments.length, params = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
          params[_key - 1] = arguments[_key];
        }
        optionValue = optionValue.apply(void 0, params);
      }
      if (optionValue === true) {
        optionValue = void 0;
      }
      if (!optionValue) {
        if (optionValue === void 0 || optionValue === false) {
          return optionValue;
        }
        throw new Error("`".concat(optionName2, "` was specified but was not a node, or did not return a node"));
      }
      var node = optionValue;
      if (typeof optionValue === "string") {
        var _this$getDocument;
        node = (_this$getDocument = this.getDocument()) === null || _this$getDocument === void 0 ? void 0 : _this$getDocument.querySelector(optionValue);
        if (!node) {
          throw new Error("`".concat(optionName2, "` as selector refers to no known node"));
        }
      }
      return node;
    });
    _this.handleDeactivate = _this.handleDeactivate.bind(_this);
    _this.handlePostDeactivate = _this.handlePostDeactivate.bind(_this);
    _this.handleClickOutsideDeactivates = _this.handleClickOutsideDeactivates.bind(_this);
    _this.internalOptions = {
      // We need to hijack the returnFocusOnDeactivate option,
      // because React can move focus into the element before we arrived at
      // this lifecycle hook (e.g. with autoFocus inputs). So the component
      // captures the previouslyFocusedElement in componentWillMount,
      // then (optionally) returns focus to it in componentWillUnmount.
      returnFocusOnDeactivate: false,
      // the rest of these are also related to deactivation of the trap, and we
      //  need to use them and control them as well
      checkCanReturnFocus: null,
      onDeactivate: _this.handleDeactivate,
      onPostDeactivate: _this.handlePostDeactivate,
      // we need to special-case this setting as well so that we can know if we should
      //  NOT return focus if the trap gets auto-deactivated as the result of an
      //  outside click (otherwise, we'll always think we should return focus because
      //  of how we manage that flag internally here)
      clickOutsideDeactivates: _this.handleClickOutsideDeactivates
    };
    _this.originalOptions = {
      // because of the above `internalOptions`, we maintain our own flag for
      //  this option, and default it to `true` because that's focus-trap's default
      returnFocusOnDeactivate: true,
      // because of the above `internalOptions`, we keep these separate since
      //  they're part of the deactivation process which we configure (internally) to
      //  be shared between focus-trap and focus-trap-react
      onDeactivate: null,
      onPostDeactivate: null,
      checkCanReturnFocus: null,
      // the user's setting, defaulted to false since focus-trap defaults this to false
      clickOutsideDeactivates: false
    };
    var focusTrapOptions = props.focusTrapOptions;
    for (var optionName in focusTrapOptions) {
      if (!Object.prototype.hasOwnProperty.call(focusTrapOptions, optionName)) {
        continue;
      }
      if (optionName === "returnFocusOnDeactivate" || optionName === "onDeactivate" || optionName === "onPostDeactivate" || optionName === "checkCanReturnFocus" || optionName === "clickOutsideDeactivates") {
        _this.originalOptions[optionName] = focusTrapOptions[optionName];
        continue;
      }
      _this.internalOptions[optionName] = focusTrapOptions[optionName];
    }
    _this.outsideClick = null;
    _this.focusTrapElements = props.containerElements || [];
    _this.updatePreviousElement();
    return _this;
  }
  _inherits(FocusTrap2, _React$Component);
  return _createClass(FocusTrap2, [{
    key: "getDocument",
    value: function getDocument() {
      return this.props.focusTrapOptions.document || (typeof document !== "undefined" ? document : void 0);
    }
  }, {
    key: "getReturnFocusNode",
    value: function getReturnFocusNode() {
      var node = this.getNodeForOption("setReturnFocus", this.previouslyFocusedElement);
      return node ? node : node === false ? false : this.previouslyFocusedElement;
    }
    /** Update the previously focused element with the currently focused element. */
  }, {
    key: "updatePreviousElement",
    value: function updatePreviousElement() {
      var currentDocument = this.getDocument();
      if (currentDocument) {
        this.previouslyFocusedElement = currentDocument.activeElement;
      }
    }
  }, {
    key: "deactivateTrap",
    value: function deactivateTrap2() {
      if (!this.focusTrap || !this.focusTrap.active) {
        return;
      }
      this.focusTrap.deactivate({
        // NOTE: we never let the trap return the focus since we do that ourselves
        returnFocus: false,
        // we'll call this in our own post deactivate handler so make sure the trap doesn't
        //  do it prematurely
        checkCanReturnFocus: null,
        // let it call the user's original deactivate handler, if any, instead of
        //  our own which calls back into this function
        onDeactivate: this.originalOptions.onDeactivate
        // NOTE: for post deactivate, don't specify anything so that it calls the
        //  onPostDeactivate handler specified on `this.internalOptions`
        //  which will always be our own `handlePostDeactivate()` handler, which
        //  will finish things off by calling the user's provided onPostDeactivate
        //  handler, if any, at the right time
        // onPostDeactivate: NOTHING
      });
    }
  }, {
    key: "handleClickOutsideDeactivates",
    value: function handleClickOutsideDeactivates(event) {
      var allowDeactivation = typeof this.originalOptions.clickOutsideDeactivates === "function" ? this.originalOptions.clickOutsideDeactivates.call(null, event) : this.originalOptions.clickOutsideDeactivates;
      if (allowDeactivation) {
        this.outsideClick = {
          target: event.target,
          allowDeactivation
        };
      }
      return allowDeactivation;
    }
  }, {
    key: "handleDeactivate",
    value: function handleDeactivate() {
      if (this.originalOptions.onDeactivate) {
        this.originalOptions.onDeactivate.call(null);
      }
      this.deactivateTrap();
    }
  }, {
    key: "handlePostDeactivate",
    value: function handlePostDeactivate() {
      var _this2 = this;
      var finishDeactivation = function finishDeactivation2() {
        var returnFocusNode = _this2.getReturnFocusNode();
        var canReturnFocus = !!// did the consumer allow it?
        (_this2.originalOptions.returnFocusOnDeactivate && // can we actually focus the node?
        returnFocusNode !== null && returnFocusNode !== void 0 && returnFocusNode.focus && // was there an outside click that allowed deactivation?
        (!_this2.outsideClick || // did the consumer allow deactivation when the outside node was clicked?
        _this2.outsideClick.allowDeactivation && // is the outside node NOT focusable (implying that it did NOT receive focus
        //  as a result of the click-through) -- in which case do NOT restore focus
        //  to `returnFocusNode` because focus should remain on the outside node
        !isFocusable2(_this2.outsideClick.target, _this2.internalOptions.tabbableOptions)));
        var _this2$internalOption = _this2.internalOptions.preventScroll, preventScroll = _this2$internalOption === void 0 ? false : _this2$internalOption;
        if (canReturnFocus) {
          returnFocusNode.focus({
            preventScroll
          });
        }
        if (_this2.originalOptions.onPostDeactivate) {
          _this2.originalOptions.onPostDeactivate.call(null);
        }
        _this2.outsideClick = null;
      };
      if (this.originalOptions.checkCanReturnFocus) {
        this.originalOptions.checkCanReturnFocus.call(null, this.getReturnFocusNode()).then(finishDeactivation, finishDeactivation);
      } else {
        finishDeactivation();
      }
    }
  }, {
    key: "setupFocusTrap",
    value: function setupFocusTrap() {
      if (this.focusTrap) {
        if (this.props.active && !this.focusTrap.active) {
          this.focusTrap.activate();
          if (this.props.paused) {
            this.focusTrap.pause();
          }
        }
      } else {
        var nodesExist = this.focusTrapElements.some(Boolean);
        if (nodesExist) {
          this.focusTrap = this.props._createFocusTrap(this.focusTrapElements, this.internalOptions);
          if (this.props.active) {
            this.focusTrap.activate();
          }
          if (this.props.paused) {
            this.focusTrap.pause();
          }
        }
      }
    }
  }, {
    key: "componentDidMount",
    value: function componentDidMount() {
      if (this.props.active) {
        this.setupFocusTrap();
      }
    }
  }, {
    key: "componentDidUpdate",
    value: function componentDidUpdate(prevProps) {
      if (this.focusTrap) {
        if (prevProps.containerElements !== this.props.containerElements) {
          this.focusTrap.updateContainerElements(this.props.containerElements);
        }
        var hasActivated = !prevProps.active && this.props.active;
        var hasDeactivated = prevProps.active && !this.props.active;
        var hasPaused = !prevProps.paused && this.props.paused;
        var hasUnpaused = prevProps.paused && !this.props.paused;
        if (hasActivated) {
          this.updatePreviousElement();
          this.focusTrap.activate();
        }
        if (hasDeactivated) {
          this.deactivateTrap();
          return;
        }
        if (hasPaused) {
          this.focusTrap.pause();
        }
        if (hasUnpaused) {
          this.focusTrap.unpause();
        }
      } else {
        if (prevProps.containerElements !== this.props.containerElements) {
          this.focusTrapElements = this.props.containerElements;
        }
        if (this.props.active) {
          this.updatePreviousElement();
          this.setupFocusTrap();
        }
      }
    }
  }, {
    key: "componentWillUnmount",
    value: function componentWillUnmount() {
      this.deactivateTrap();
    }
  }, {
    key: "render",
    value: function render() {
      var _this3 = this;
      var child = this.props.children ? React.Children.only(this.props.children) : void 0;
      if (child) {
        if (child.type && child.type === React.Fragment) {
          throw new Error("A focus-trap cannot use a Fragment as its child container. Try replacing it with a <div> element.");
        }
        var callbackRef = function callbackRef2(element) {
          var containerElements = _this3.props.containerElements;
          if (child) {
            if (reactVerMajor >= 19) {
              if (typeof child.props.ref === "function") {
                child.props.ref(element);
              } else if (child.props.ref) {
                child.props.ref.current = element;
              }
            } else {
              if (typeof child.ref === "function") {
                child.ref(element);
              } else if (child.ref) {
                child.ref.current = element;
              }
            }
          }
          _this3.focusTrapElements = containerElements ? containerElements : [element];
        };
        var childWithRef = React.cloneElement(child, {
          ref: callbackRef
        });
        return childWithRef;
      }
      return null;
    }
  }]);
}(React.Component);
FocusTrap$1.defaultProps = {
  active: true,
  paused: false,
  focusTrapOptions: {},
  _createFocusTrap: createFocusTrap2
};
focusTrapReact.exports = FocusTrap$1;
focusTrapReact.exports.FocusTrap = FocusTrap$1;
var focusTrapReactExports = focusTrapReact.exports;
const FocusTrap = /* @__PURE__ */ getDefaultExportFromCjs(focusTrapReactExports);
function ProductCard({ product, theme, onAddToCart, onClick, isAdding }) {
  const handleCardClick = () => {
    if (onClick && product.available) {
      onClick(product);
    }
  };
  const handleKeyDown = (e) => {
    if ((e.key === "Enter" || e.key === " ") && onClick && product.available) {
      e.preventDefault();
      onClick(product);
    }
  };
  const handleAddToCart = (e) => {
    e.stopPropagation();
    if (onAddToCart && product.available) {
      onAddToCart(product);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "product-card",
      onClick: handleCardClick,
      onKeyDown: handleKeyDown,
      tabIndex: onClick ? 0 : void 0,
      role: onClick ? "button" : void 0,
      "aria-label": onClick ? `View details for ${product.title}` : void 0,
      style: {
        display: "flex",
        gap: 12,
        padding: 12,
        backgroundColor: "#ffffff",
        borderRadius: 12,
        border: product.isPinned ? `2px solid ${theme.primaryColor}` : "1px solid #e5e7eb",
        marginBottom: 8,
        cursor: onClick ? "pointer" : "default",
        transition: "box-shadow 0.2s, border-color 0.2s",
        position: "relative"
      },
      children: [
        product.isPinned && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: "featured-badge",
            style: {
              position: "absolute",
              top: -8,
              left: 8,
              background: theme.primaryColor,
              color: "white",
              padding: "2px 8px",
              borderRadius: 4,
              fontSize: 10,
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: 3,
              boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
              zIndex: 1
            },
            children: "⭐ Featured"
          }
        ),
        product.imageUrl && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "img",
          {
            src: product.imageUrl,
            alt: product.title,
            style: {
              width: 64,
              height: 64,
              objectFit: "cover",
              borderRadius: 8,
              flexShrink: 0
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { flex: 1, minWidth: 0 }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                fontWeight: 500,
                fontSize: 13,
                marginBottom: 4,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              },
              children: product.title
            }
          ),
          product.productType && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                fontSize: 11,
                color: "#6b7280",
                marginBottom: 4
              },
              children: product.productType
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              style: {
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 8
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontWeight: 600, fontSize: 14 }, children: [
                  "$",
                  (product.price ?? 0).toFixed(2)
                ] }),
                onAddToCart && /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleAddToCart,
                    disabled: !product.available || isAdding,
                    style: {
                      padding: "6px 12px",
                      fontSize: 12,
                      fontWeight: 500,
                      backgroundColor: product.available ? theme.primaryColor : "#9ca3af",
                      color: "white",
                      border: "none",
                      borderRadius: 8,
                      cursor: product.available ? "pointer" : "not-allowed",
                      opacity: isAdding ? 0.7 : 1
                    },
                    children: isAdding ? "Adding..." : product.available ? "Add to Cart" : "Sold Out"
                  }
                )
              ]
            }
          )
        ] })
      ]
    }
  );
}
function ProductList({ products, theme, onAddToCart, onProductClick, addingProductId }) {
  if (products.length === 0) {
    return null;
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "product-list", style: { marginTop: 8 }, children: products.map((product) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    ProductCard,
    {
      product,
      theme,
      onAddToCart,
      onClick: onProductClick,
      isAdding: addingProductId === product.id
    },
    product.id
  )) });
}
function CartView({
  cart,
  theme,
  onRemoveItem,
  onCheckout,
  isCheckingOut,
  removingItemId
}) {
  if (cart.items.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "cart-view cart-view--empty",
        style: {
          padding: 16,
          textAlign: "center",
          color: "#6b7280",
          fontSize: 13
        },
        children: "Your cart is empty"
      }
    );
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "cart-view",
      style: {
        backgroundColor: "#f9fafb",
        borderRadius: 12,
        padding: 12,
        marginTop: 8
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            style: {
              fontSize: 13,
              fontWeight: 600,
              marginBottom: 12,
              display: "flex",
              alignItems: "center",
              gap: 8
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "svg",
                {
                  width: "16",
                  height: "16",
                  viewBox: "0 0 24 24",
                  fill: "none",
                  stroke: "currentColor",
                  strokeWidth: "2",
                  strokeLinecap: "round",
                  strokeLinejoin: "round",
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "9", cy: "21", r: "1" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "20", cy: "21", r: "1" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" })
                  ]
                }
              ),
              "Your Cart (",
              cart.itemCount,
              " ",
              cart.itemCount === 1 ? "item" : "items",
              ")"
            ]
          }
        ),
        cart.items.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          CartItemView,
          {
            item,
            onRemove: onRemoveItem,
            isRemoving: removingItemId === item.variantId
          },
          item.variantId
        )),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            style: {
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: 12,
              paddingTop: 12,
              borderTop: "1px solid #e5e7eb"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontWeight: 600 }, children: [
                "Total: $",
                (cart.total ?? 0).toFixed(2)
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: 8 }, children: [
                cart.shopifyCartUrl && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                  "a",
                  {
                    href: cart.shopifyCartUrl,
                    target: "_blank",
                    rel: "noopener noreferrer",
                    style: {
                      padding: "8px 16px",
                      fontSize: 13,
                      fontWeight: 500,
                      backgroundColor: "transparent",
                      color: theme.primaryColor,
                      border: `1px solid ${theme.primaryColor}`,
                      borderRadius: 8,
                      textDecoration: "none",
                      display: "flex",
                      alignItems: "center",
                      gap: 4
                    },
                    children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsxs(
                        "svg",
                        {
                          width: "14",
                          height: "14",
                          viewBox: "0 0 24 24",
                          fill: "none",
                          stroke: "currentColor",
                          strokeWidth: "2",
                          strokeLinecap: "round",
                          strokeLinejoin: "round",
                          children: [
                            /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" }),
                            /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "15 3 21 3 21 9" }),
                            /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "10", y1: "14", x2: "21", y2: "3" })
                          ]
                        }
                      ),
                      "View on Store"
                    ]
                  }
                ),
                onCheckout && /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: onCheckout,
                    disabled: isCheckingOut,
                    style: {
                      padding: "8px 16px",
                      fontSize: 13,
                      fontWeight: 500,
                      backgroundColor: theme.primaryColor,
                      color: "white",
                      border: "none",
                      borderRadius: 8,
                      cursor: "pointer",
                      opacity: isCheckingOut ? 0.7 : 1
                    },
                    children: isCheckingOut ? "Processing..." : "Checkout"
                  }
                )
              ] })
            ]
          }
        )
      ]
    }
  );
}
function CartItemView({ item, onRemove, isRemoving }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "cart-item",
      style: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "8px 0",
        borderBottom: "1px solid #e5e7eb"
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { flex: 1, minWidth: 0 }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                fontSize: 13,
                fontWeight: 500,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              },
              children: item.title
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontSize: 12, color: "#6b7280" }, children: [
            "Qty: ",
            item.quantity,
            " × $",
            (item.price ?? 0).toFixed(2)
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: 8 }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontWeight: 500, fontSize: 13 }, children: [
            "$",
            ((item.price ?? 0) * item.quantity).toFixed(2)
          ] }),
          onRemove && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              onClick: () => onRemove(item.variantId),
              disabled: isRemoving,
              style: {
                padding: 4,
                background: "none",
                border: "none",
                cursor: "pointer",
                opacity: isRemoving ? 0.5 : 1
              },
              "aria-label": `Remove ${item.title}`,
              children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "svg",
                {
                  width: "16",
                  height: "16",
                  viewBox: "0 0 24 24",
                  fill: "none",
                  stroke: "#ef4444",
                  strokeWidth: "2",
                  strokeLinecap: "round",
                  strokeLinejoin: "round",
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "3 6 5 6 21 6" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" })
                  ]
                }
              )
            }
          )
        ] })
      ]
    }
  );
}
function MessageList({
  messages,
  botName,
  welcomeMessage,
  theme,
  isLoading,
  onAddToCart,
  onProductClick,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut
}) {
  const messagesEndRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    var _a;
    (_a = messagesEndRef.current) == null ? void 0 : _a.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  if (messages.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "message-list message-list--empty",
        role: "log",
        "aria-live": "polite",
        style: {
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 16,
          textAlign: "center",
          color: theme.textColor,
          opacity: 0.7
        },
        children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "svg",
            {
              width: "48",
              height: "48",
              viewBox: "0 0 24 24",
              fill: "none",
              stroke: "currentColor",
              strokeWidth: "1.5",
              strokeLinecap: "round",
              strokeLinejoin: "round",
              "aria-hidden": "true",
              style: { margin: "0 auto 12px", opacity: 0.5 },
              children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" })
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: welcomeMessage ?? "Start a conversation" })
        ] })
      }
    );
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "message-list",
      role: "log",
      "aria-live": "polite",
      "aria-label": "Chat messages",
      "aria-busy": isLoading ? "true" : "false",
      style: {
        flex: 1,
        overflowY: "auto",
        padding: 16
      },
      children: [
        messages.map((message) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          MessageBubble,
          {
            message,
            botName,
            theme,
            onAddToCart,
            onProductClick,
            onRemoveFromCart,
            onCheckout,
            addingProductId,
            removingItemId,
            isCheckingOut
          },
          message.messageId
        )),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { ref: messagesEndRef })
      ]
    }
  );
}
function MessageBubble({
  message,
  botName,
  theme,
  onAddToCart,
  onProductClick,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut
}) {
  const isUser = message.sender === "user";
  const isMerchant = message.sender === "merchant";
  const displayName = isMerchant ? "Merchant" : botName;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: `message-bubble message-bubble--${message.sender}`,
      role: "listitem",
      style: {
        marginBottom: 12
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            style: {
              display: "flex",
              justifyContent: isUser ? "flex-end" : "flex-start"
            },
            children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "div",
              {
                style: {
                  maxWidth: "75%",
                  padding: "10px 14px",
                  borderRadius: 16,
                  backgroundColor: isUser ? theme.userBubbleColor : theme.botBubbleColor,
                  color: isUser ? "white" : theme.textColor,
                  borderBottomRightRadius: isUser ? 4 : 16,
                  borderBottomLeftRadius: isUser ? 16 : 4
                },
                children: [
                  !isUser && /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "div",
                    {
                      style: {
                        fontSize: 11,
                        fontWeight: 600,
                        marginBottom: 4,
                        opacity: 0.8
                      },
                      children: displayName
                    }
                  ),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { whiteSpace: "pre-wrap", wordBreak: "break-word" }, children: message.content })
                ]
              }
            )
          }
        ),
        !isUser && message.products && message.products.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { maxWidth: "100%", marginTop: 8 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          ProductList,
          {
            products: message.products,
            theme,
            onAddToCart,
            onProductClick,
            addingProductId
          }
        ) }),
        !isUser && message.cart && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { maxWidth: "100%", marginTop: 8 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          CartView,
          {
            cart: message.cart,
            theme,
            onRemoveItem: onRemoveFromCart,
            onCheckout,
            isCheckingOut,
            removingItemId
          }
        ) }),
        !isUser && message.checkoutUrl && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { marginTop: 8 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          "a",
          {
            href: message.checkoutUrl,
            target: "_blank",
            rel: "noopener noreferrer",
            style: {
              display: "inline-block",
              padding: "8px 16px",
              backgroundColor: theme.primaryColor,
              color: "white",
              textDecoration: "none",
              borderRadius: 8,
              fontWeight: 500,
              fontSize: 13
            },
            children: "Complete Checkout →"
          }
        ) })
      ]
    }
  );
}
function MessageInput({
  value,
  onChange,
  onSend,
  disabled,
  placeholder,
  inputRef,
  theme,
  maxLength = 2e3
}) {
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };
  const handleSubmit = (event) => {
    event.preventDefault();
    onSend();
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "form",
    {
      className: "message-input",
      onSubmit: handleSubmit,
      style: {
        display: "flex",
        padding: 12,
        borderTop: "1px solid #e5e7eb",
        backgroundColor: theme.backgroundColor,
        borderRadius: `0 0 ${theme.borderRadius}px ${theme.borderRadius}px`
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            ref: inputRef,
            type: "text",
            value,
            onChange: (e) => onChange(e.target.value),
            onKeyDown: handleKeyDown,
            disabled,
            placeholder,
            "aria-label": "Type a message",
            maxLength,
            style: {
              flex: 1,
              padding: "10px 14px",
              border: "1px solid #e5e7eb",
              borderRadius: 20,
              fontSize: theme.fontSize,
              fontFamily: theme.fontFamily,
              outline: "none",
              backgroundColor: disabled ? "#f9fafb" : "white"
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "submit",
            disabled: disabled || !value.trim(),
            "aria-label": "Send message",
            style: {
              marginLeft: 8,
              padding: "10px 16px",
              backgroundColor: disabled || !value.trim() ? "#e5e7eb" : theme.primaryColor,
              color: disabled || !value.trim() ? "#9ca3af" : "white",
              border: "none",
              borderRadius: 20,
              cursor: disabled || !value.trim() ? "not-allowed" : "pointer",
              fontSize: theme.fontSize,
              fontWeight: 500
            },
            children: "Send"
          }
        )
      ]
    }
  );
}
function TypingIndicator({ isVisible, botName, theme }) {
  if (!isVisible) return null;
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      className: "typing-indicator",
      role: "status",
      "aria-live": "polite",
      "aria-label": `${botName} is typing`,
      style: {
        display: "flex",
        alignItems: "center",
        padding: "8px 16px"
      },
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          style: {
            padding: "8px 12px",
            borderRadius: 16,
            backgroundColor: theme.botBubbleColor,
            display: "flex",
            alignItems: "center",
            gap: 4
          },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontSize: 11, color: theme.textColor, marginRight: 8, opacity: 0.8 }, children: botName }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(TypingDot, {}),
            /* @__PURE__ */ jsxRuntimeExports.jsx(TypingDot, {}),
            /* @__PURE__ */ jsxRuntimeExports.jsx(TypingDot, {})
          ]
        }
      )
    }
  );
}
function TypingDot() {
  return /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "typing-dot" });
}
const severityStyles = {
  [ErrorSeverity.INFO]: {
    bg: "#eff6ff",
    border: "#3b82f6",
    icon: "ℹ️"
  },
  [ErrorSeverity.WARNING]: {
    bg: "#fffbeb",
    border: "#f59e0b",
    icon: "⚠️"
  },
  [ErrorSeverity.ERROR]: {
    bg: "#fef2f2",
    border: "#ef4444",
    icon: "❌"
  },
  [ErrorSeverity.CRITICAL]: {
    bg: "#fef2f2",
    border: "#dc2626",
    icon: "🚨"
  }
};
function ErrorToast({
  error,
  onDismiss,
  onRetry,
  actions,
  autoDismiss = true,
  autoDismissDelay = 8e3,
  showProgress = true
}) {
  const [isVisible, setIsVisible] = reactExports.useState(false);
  const [isExiting, setIsExiting] = reactExports.useState(false);
  const [timeLeft, setTimeLeft] = reactExports.useState(autoDismissDelay);
  const [isPaused, setIsPaused] = reactExports.useState(false);
  const timerRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    requestAnimationFrame(() => {
      setIsVisible(true);
    });
  }, []);
  reactExports.useEffect(() => {
    if (!autoDismiss || error.dismissed || isPaused) return;
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 100) {
          handleDismiss();
          return 0;
        }
        return prev - 100;
      });
    }, 100);
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [autoDismiss, error.dismissed, isPaused]);
  const handleDismiss = reactExports.useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(error.id);
    }, 300);
  }, [error.id, onDismiss]);
  const handleRetry = reactExports.useCallback(() => {
    if (onRetry) {
      onRetry(error.id);
      handleDismiss();
    }
  }, [error.id, onRetry, handleDismiss]);
  const handleMouseEnter = () => setIsPaused(true);
  const handleMouseLeave = () => setIsPaused(false);
  const styles = severityStyles[error.severity];
  const progress = timeLeft / autoDismissDelay * 100;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      role: "alert",
      "aria-live": "assertive",
      "aria-atomic": "true",
      className: `error-toast ${isVisible && !isExiting ? "error-toast--visible" : ""} ${isExiting ? "error-toast--exiting" : ""}`,
      style: {
        backgroundColor: styles.bg,
        borderLeft: `4px solid ${styles.border}`,
        borderRadius: "8px",
        padding: "12px 16px",
        marginBottom: "8px",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
        transform: isVisible && !isExiting ? "translateX(0)" : "translateX(100%)",
        opacity: isExiting ? 0 : 1,
        transition: "transform 0.3s ease, opacity 0.3s ease",
        position: "relative",
        overflow: "hidden"
      },
      onMouseEnter: handleMouseEnter,
      onMouseLeave: handleMouseLeave,
      children: [
        showProgress && autoDismiss && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: "error-toast__progress",
            style: {
              position: "absolute",
              bottom: 0,
              left: 0,
              height: "3px",
              backgroundColor: styles.border,
              width: `${progress}%`,
              transition: "width 0.1s linear"
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            className: "error-toast__content",
            style: {
              display: "flex",
              alignItems: "flex-start",
              gap: "12px"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "span",
                {
                  className: "error-toast__icon",
                  style: {
                    fontSize: "18px",
                    lineHeight: 1,
                    flexShrink: 0
                  },
                  "aria-hidden": "true",
                  children: styles.icon
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "div",
                {
                  className: "error-toast__body",
                  style: {
                    flex: 1,
                    minWidth: 0
                  },
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "div",
                      {
                        className: "error-toast__title",
                        style: {
                          fontWeight: 600,
                          fontSize: "14px",
                          color: "#1f2937",
                          marginBottom: "4px"
                        },
                        children: error.message
                      }
                    ),
                    error.detail && /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "div",
                      {
                        className: "error-toast__detail",
                        style: {
                          fontSize: "13px",
                          color: "#4b5563",
                          marginBottom: error.retryable || (actions == null ? void 0 : actions.length) ? "12px" : 0
                        },
                        children: error.detail
                      }
                    ),
                    (error.retryable || (actions == null ? void 0 : actions.length)) && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                      "div",
                      {
                        className: "error-toast__actions",
                        style: {
                          display: "flex",
                          gap: "8px",
                          flexWrap: "wrap"
                        },
                        children: [
                          error.retryable && onRetry && /* @__PURE__ */ jsxRuntimeExports.jsx(
                            "button",
                            {
                              type: "button",
                              onClick: handleRetry,
                              className: "error-toast__retry",
                              style: {
                                padding: "6px 12px",
                                fontSize: "13px",
                                fontWeight: 500,
                                backgroundColor: styles.border,
                                color: "white",
                                border: "none",
                                borderRadius: "6px",
                                cursor: "pointer",
                                transition: "opacity 0.2s"
                              },
                              onMouseEnter: (e) => e.currentTarget.style.opacity = "0.8",
                              onMouseLeave: (e) => e.currentTarget.style.opacity = "1",
                              children: error.retryAction || "Try Again"
                            }
                          ),
                          error.fallbackUrl && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                            "a",
                            {
                              href: error.fallbackUrl,
                              target: "_blank",
                              rel: "noopener noreferrer",
                              className: "error-toast__fallback",
                              style: {
                                padding: "6px 12px",
                                fontSize: "13px",
                                fontWeight: 500,
                                backgroundColor: "transparent",
                                color: styles.border,
                                border: `1px solid ${styles.border}`,
                                borderRadius: "6px",
                                textDecoration: "none",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px"
                              },
                              children: [
                                "Visit Store",
                                /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "12", height: "12", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", children: [
                                  /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" }),
                                  /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "15 3 21 3 21 9" }),
                                  /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "10", y1: "14", x2: "21", y2: "3" })
                                ] })
                              ]
                            }
                          ),
                          actions == null ? void 0 : actions.map((action, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                            "button",
                            {
                              type: "button",
                              onClick: action.handler,
                              className: `error-toast__action ${action.primary ? "error-toast__action--primary" : ""}`,
                              style: {
                                padding: "6px 12px",
                                fontSize: "13px",
                                fontWeight: 500,
                                backgroundColor: action.primary ? styles.border : "transparent",
                                color: action.primary ? "white" : "#4b5563",
                                border: `1px solid ${action.primary ? styles.border : "#d1d5db"}`,
                                borderRadius: "6px",
                                cursor: "pointer",
                                transition: "opacity 0.2s"
                              },
                              onMouseEnter: (e) => e.currentTarget.style.opacity = "0.8",
                              onMouseLeave: (e) => e.currentTarget.style.opacity = "1",
                              children: action.label
                            },
                            index
                          )),
                          error.retryAfter && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                            "span",
                            {
                              className: "error-toast__retry-after",
                              style: {
                                fontSize: "12px",
                                color: "#6b7280",
                                display: "flex",
                                alignItems: "center"
                              },
                              children: [
                                "Retry in ",
                                formatRetryTime(error.retryAfter)
                              ]
                            }
                          )
                        ]
                      }
                    )
                  ]
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  type: "button",
                  onClick: handleDismiss,
                  className: "error-toast__dismiss",
                  "aria-label": "Dismiss error",
                  style: {
                    background: "none",
                    border: "none",
                    padding: "4px",
                    cursor: "pointer",
                    color: "#9ca3af",
                    flexShrink: 0,
                    transition: "color 0.2s"
                  },
                  onMouseEnter: (e) => e.currentTarget.style.color = "#4b5563",
                  onMouseLeave: (e) => e.currentTarget.style.color = "#9ca3af",
                  children: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "16", height: "16", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "18", y1: "6", x2: "6", y2: "18" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "6", y1: "6", x2: "18", y2: "18" })
                  ] })
                }
              )
            ]
          }
        )
      ]
    }
  );
}
function ProductDetailModal({
  productId,
  sessionId,
  theme,
  isOpen,
  onClose,
  onAddToCart
}) {
  const [product, setProduct] = reactExports.useState(null);
  const [loading, setLoading] = reactExports.useState(false);
  const [error, setError] = reactExports.useState(null);
  const [quantity, setQuantity] = reactExports.useState(1);
  const [added, setAdded] = reactExports.useState(false);
  reactExports.useEffect(() => {
    if (!isOpen || !productId) {
      setProduct(null);
      setError(null);
      setQuantity(1);
      setAdded(false);
      return;
    }
    const fetchProduct = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await widgetClient.getProduct(sessionId, productId);
        setProduct(data);
      } catch (err) {
        setError(err instanceof WidgetApiException ? err.message : "Failed to load product");
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [isOpen, productId, sessionId]);
  reactExports.useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);
  reactExports.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);
  if (!isOpen) return null;
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };
  const inStock = product && product.available && (product.inventoryQuantity ?? 0) > 0;
  const maxQuantity = (product == null ? void 0 : product.inventoryQuantity) ?? 99;
  const handleAddToCartClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!product || !inStock || !onAddToCart) return;
    onAddToCart(product, quantity);
    setAdded(true);
    setTimeout(() => {
      setAdded(false);
      onClose();
    }, 1e3);
  };
  const handleCloseClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onClose();
  };
  const handleIncrement = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (quantity < maxQuantity) {
      setQuantity(quantity + 1);
    }
  };
  const handleDecrement = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };
  const getStockStatus = () => {
    if (!product) return null;
    if (!product.available) {
      return { text: "Out of Stock", color: "#dc2626", bg: "#fef2f2" };
    }
    if (product.inventoryQuantity === 0) {
      return { text: "Out of Stock", color: "#dc2626", bg: "#fef2f2" };
    }
    if (product.inventoryQuantity && product.inventoryQuantity <= 5) {
      return { text: `Only ${product.inventoryQuantity} in stock`, color: "#ea580c", bg: "#fff7ed" };
    }
    if (product.inventoryQuantity && product.inventoryQuantity <= 10) {
      return { text: `${product.inventoryQuantity} in stock`, color: "#ca8a04", bg: "#fefce8" };
    }
    return { text: "In Stock", color: "#16a34a", bg: "#f0fdf4" };
  };
  const stockStatus = getStockStatus();
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      style: {
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 2147483647,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
        backgroundColor: "rgba(0, 0, 0, 0.5)"
      },
      onClick: handleBackdropClick,
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          style: {
            backgroundColor: "#ffffff",
            borderRadius: "16px",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            maxWidth: "400px",
            width: "100%",
            maxHeight: "90vh",
            overflow: "hidden",
            display: "flex",
            flexDirection: "column"
          },
          onClick: (e) => e.stopPropagation(),
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "div",
              {
                style: {
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "16px",
                  borderBottom: "1px solid #e5e7eb"
                },
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { style: { fontSize: "18px", fontWeight: 600, color: "#111827", margin: 0 }, children: "Product Details" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "button",
                    {
                      type: "button",
                      onClick: handleCloseClick,
                      style: {
                        padding: "8px",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        borderRadius: "50%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#9ca3af"
                      },
                      "aria-label": "Close modal",
                      children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "20", height: "20", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M18 6L6 18M6 6l12 12" }) })
                    }
                  )
                ]
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { overflowY: "auto", flex: 1 }, children: [
              loading && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", alignItems: "center", justifyContent: "center", padding: "48px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "svg",
                {
                  style: { animation: "spin 1s linear infinite", width: 32, height: 32, color: theme.primaryColor },
                  viewBox: "0 0 24 24",
                  fill: "none",
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { style: { opacity: 0.25 }, cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("path", { style: { opacity: 0.75 }, fill: "currentColor", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })
                  ]
                }
              ) }),
              error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "24px", textAlign: "center" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#dc2626", marginBottom: "16px" }, children: error }),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleCloseClick,
                    style: { padding: "8px 16px", fontSize: "14px", color: "#6b7280", background: "none", border: "none", cursor: "pointer" },
                    children: "Close"
                  }
                )
              ] }),
              product && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "16px" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "div",
                  {
                    style: {
                      position: "relative",
                      aspectRatio: "1 / 1",
                      backgroundColor: "#f3f4f6",
                      borderRadius: "8px",
                      overflow: "hidden",
                      marginBottom: "16px"
                    },
                    children: product.imageUrl ? /* @__PURE__ */ jsxRuntimeExports.jsx("img", { src: product.imageUrl, alt: product.title, style: { width: "100%", height: "100%", objectFit: "cover" } }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "64", height: "64", viewBox: "0 0 24 24", fill: "none", stroke: "#9ca3af", strokeWidth: "1.5", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" }) }) })
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { style: { fontSize: "20px", fontWeight: 600, color: "#111827", marginBottom: "8px" }, children: product.title }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontSize: "24px", fontWeight: 700, color: theme.primaryColor, marginBottom: "12px" }, children: [
                  "$",
                  product.price.toFixed(2)
                ] }),
                stockStatus && /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "div",
                  {
                    style: {
                      display: "inline-flex",
                      alignItems: "center",
                      padding: "4px 12px",
                      borderRadius: "9999px",
                      fontSize: "12px",
                      fontWeight: 500,
                      backgroundColor: stockStatus.bg,
                      color: stockStatus.color,
                      marginBottom: "12px"
                    },
                    children: stockStatus.text
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", flexWrap: "wrap", gap: "16px", marginBottom: "12px", fontSize: "14px" }, children: [
                  product.productType && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { color: "#6b7280" }, children: "Category: " }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontWeight: 500, color: "#111827" }, children: product.productType })
                  ] }),
                  product.vendor && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { color: "#6b7280" }, children: "Vendor: " }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontWeight: 500, color: "#111827" }, children: product.vendor })
                  ] })
                ] }),
                product.description && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { borderTop: "1px solid #e5e7eb", paddingTop: "12px" }, children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { style: { fontSize: "14px", fontWeight: 500, color: "#374151", marginBottom: "8px" }, children: "Description" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "14px", color: "#4b5563", lineHeight: 1.6, whiteSpace: "pre-line" }, children: product.description })
                ] })
              ] })
            ] }),
            product && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "16px", borderTop: "1px solid #e5e7eb", backgroundColor: "#f9fafb" }, children: [
              inStock && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontSize: "14px", color: "#4b5563" }, children: "Qty:" }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", border: "1px solid #d1d5db", borderRadius: "8px" }, children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "button",
                    {
                      type: "button",
                      onClick: handleDecrement,
                      disabled: quantity <= 1,
                      style: {
                        width: "32px",
                        height: "32px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "none",
                        border: "none",
                        borderRight: "1px solid #d1d5db",
                        cursor: quantity <= 1 ? "not-allowed" : "pointer",
                        fontSize: "16px",
                        fontWeight: 500,
                        color: "#374151",
                        opacity: quantity <= 1 ? 0.5 : 1
                      },
                      children: "-"
                    }
                  ),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { padding: "0 16px", textAlign: "center", minWidth: "40px" }, children: quantity }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "button",
                    {
                      type: "button",
                      onClick: handleIncrement,
                      disabled: quantity >= maxQuantity,
                      style: {
                        width: "32px",
                        height: "32px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "none",
                        border: "none",
                        borderLeft: "1px solid #d1d5db",
                        cursor: quantity >= maxQuantity ? "not-allowed" : "pointer",
                        fontSize: "16px",
                        fontWeight: 500,
                        color: "#374151",
                        opacity: quantity >= maxQuantity ? 0.5 : 1
                      },
                      children: "+"
                    }
                  )
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "8px" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleAddToCartClick,
                    disabled: !inStock || added,
                    style: {
                      flex: 1,
                      padding: "10px 16px",
                      borderRadius: "8px",
                      fontWeight: 500,
                      fontSize: "14px",
                      cursor: added || !inStock ? "not-allowed" : "pointer",
                      border: "none",
                      backgroundColor: added ? "#22c55e" : inStock ? theme.primaryColor : "#d1d5db",
                      color: "white",
                      opacity: added || inStock ? 1 : 0.7
                    },
                    children: added ? "Added to Cart!" : inStock ? "Add to Cart" : "Out of Stock"
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleCloseClick,
                    style: {
                      padding: "10px 16px",
                      backgroundColor: "#e5e7eb",
                      color: "#374151",
                      borderRadius: "8px",
                      fontWeight: 500,
                      fontSize: "14px",
                      border: "none",
                      cursor: "pointer"
                    },
                    children: "Close"
                  }
                )
              ] })
            ] })
          ]
        }
      )
    }
  );
}
function ChatWindow({
  isOpen,
  onClose,
  theme,
  config,
  messages,
  isTyping,
  onSendMessage,
  error,
  errors = [],
  onDismissError,
  onRetryError,
  onAddToCart,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  sessionId
}) {
  const [inputValue, setInputValue] = reactExports.useState("");
  const [selectedProductId, setSelectedProductId] = reactExports.useState(null);
  const [isProductModalOpen, setIsProductModalOpen] = reactExports.useState(false);
  const inputRef = reactExports.useRef(null);
  const handleProductClick = (product) => {
    setSelectedProductId(product.id);
    setIsProductModalOpen(true);
  };
  const handleProductModalClose = () => {
    setIsProductModalOpen(false);
    setSelectedProductId(null);
  };
  const handleProductAddToCart = (product, quantity) => {
    if (onAddToCart) {
      onAddToCart({
        id: product.id,
        variantId: product.variantId || product.id,
        title: product.title,
        description: product.description,
        price: product.price,
        imageUrl: product.imageUrl,
        available: product.available,
        productType: product.productType
      });
    }
  };
  const positionStyle = theme.position === "bottom-left" ? { left: 20 } : { right: 20 };
  reactExports.useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);
  reactExports.useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);
  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const message = inputValue.trim();
    setInputValue("");
    await onSendMessage(message);
  };
  if (!isOpen) return null;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(FocusTrap, { active: isOpen && !isProductModalOpen, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        role: "dialog",
        "aria-modal": "true",
        "aria-label": "Chat window",
        className: "shopbot-chat-window",
        style: {
          position: "fixed",
          bottom: 90,
          ...positionStyle,
          width: theme.width,
          height: theme.height,
          maxWidth: "calc(100vw - 40px)",
          maxHeight: "calc(100vh - 120px)",
          backgroundColor: theme.backgroundColor,
          borderRadius: theme.borderRadius,
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.15)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          zIndex: 2147483646,
          fontFamily: theme.fontFamily,
          fontSize: theme.fontSize,
          color: theme.textColor
        },
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              className: "chat-header",
              style: {
                padding: "16px",
                backgroundColor: theme.primaryColor,
                color: "white",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderRadius: `${theme.borderRadius}px ${theme.borderRadius}px 0 0`
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "chat-header-title", style: { fontWeight: 600 }, children: (config == null ? void 0 : config.botName) ?? "Assistant" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: onClose,
                    "aria-label": "Close chat window",
                    style: {
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      padding: 4,
                      color: "white"
                    },
                    children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                      "svg",
                      {
                        width: "20",
                        height: "20",
                        viewBox: "0 0 24 24",
                        fill: "none",
                        stroke: "currentColor",
                        strokeWidth: "2",
                        strokeLinecap: "round",
                        strokeLinejoin: "round",
                        "aria-hidden": "true",
                        children: [
                          /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "18", y1: "6", x2: "6", y2: "18" }),
                          /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "6", y1: "6", x2: "18", y2: "18" })
                        ]
                      }
                    )
                  }
                )
              ]
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            MessageList,
            {
              messages,
              botName: (config == null ? void 0 : config.botName) ?? "Assistant",
              welcomeMessage: config == null ? void 0 : config.welcomeMessage,
              theme,
              isLoading: isTyping,
              onAddToCart,
              onProductClick: handleProductClick,
              onRemoveFromCart,
              onCheckout,
              addingProductId,
              removingItemId,
              isCheckingOut
            }
          ),
          isTyping && /* @__PURE__ */ jsxRuntimeExports.jsx(
            TypingIndicator,
            {
              isVisible: isTyping,
              botName: (config == null ? void 0 : config.botName) ?? "Assistant",
              theme
            }
          ),
          (errors.length > 0 || error) && /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              className: "chat-errors",
              style: {
                padding: "8px",
                maxHeight: "150px",
                overflowY: "auto"
              },
              children: [
                errors.filter((e) => !e.dismissed).map((widgetError) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                  ErrorToast,
                  {
                    error: widgetError,
                    onDismiss: onDismissError || (() => {
                    }),
                    onRetry: onRetryError,
                    autoDismiss: true,
                    autoDismissDelay: 1e4,
                    showProgress: true
                  },
                  widgetError.id
                )),
                error && errors.filter((e) => !e.dismissed).length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                  "div",
                  {
                    className: "chat-error",
                    role: "alert",
                    style: {
                      padding: "12px 16px",
                      backgroundColor: "#fee2e2",
                      color: "#dc2626",
                      fontSize: "13px",
                      borderRadius: "8px",
                      borderLeft: "4px solid #dc2626",
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "12px"
                    },
                    children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "aria-hidden": "true", children: "❌" }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: error })
                    ]
                  }
                )
              ]
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            MessageInput,
            {
              value: inputValue,
              onChange: setInputValue,
              onSend: handleSend,
              disabled: isTyping,
              placeholder: "Type a message...",
              inputRef,
              theme
            }
          )
        ]
      }
    ) }),
    sessionId && /* @__PURE__ */ jsxRuntimeExports.jsx(
      ProductDetailModal,
      {
        productId: selectedProductId,
        sessionId,
        theme,
        isOpen: isProductModalOpen,
        onClose: handleProductModalClose,
        onAddToCart: handleProductAddToCart
      }
    )
  ] });
}
export {
  ChatWindow as default
};

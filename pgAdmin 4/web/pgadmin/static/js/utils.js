//////////////////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2020, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////////////////

import _ from 'underscore';
import { getTreeNodeHierarchyFromIdentifier } from 'sources/tree/pgadmin_tree_node';

export function parseShortcutValue(obj) {
  var shortcut = '';
  if (obj.alt) { shortcut += 'alt+'; }
  if (obj.shift) { shortcut += 'shift+'; }
  if (obj.control) { shortcut += 'ctrl+'; }
  shortcut += obj.key.char.toLowerCase();
  return shortcut;
}

export function findAndSetFocus(container) {
  if (container.length == 0) {
    return;
  }
  setTimeout(function() {
    var first_el = container
      .find('button.fa-plus:first');

    /* Adding the tabindex condition makes sure that
     * when testing accessibility it works consistently across all
     * browser. For eg, in safari focus() works only when element has
     * tabindex="0", whereas in Chrome it works in any case
     */
    if (first_el.length == 0) {
      first_el = container
        .find(`
          .pgadmin-controls:first input:enabled,
          .pgadmin-controls:first .btn:not(.toggle),
          .ajs-commands:first,
          .CodeMirror-scroll`)
        .find('*[tabindex]:not([tabindex="-1"])');
    }

    if(first_el.length > 0) {
      first_el[0].focus();
    } else {
      container[0].focus();
    }
  }, 200);
}

let isValidData = (data) => (!_.isUndefined(data) && !_.isNull(data));
let isFunction = (fn) => (_.isFunction(fn));
let isString = (str) => (_.isString(str));

export {
  isValidData, isFunction, isString,
};

export function getEpoch(inp_date) {
  let date_obj = inp_date ? inp_date : new Date();
  return parseInt(date_obj.getTime()/1000);
}

/* Eucladian GCD */
export function getGCD(inp_arr) {
  let gcd_for_two = (a, b) => {
    return a == 0?b:gcd_for_two(b % a, a);
  };

  let inp_len = inp_arr.length;
  if(inp_len <= 2) {
    return gcd_for_two(inp_arr[0], inp_arr[1]);
  }

  let result = inp_arr[0];
  for(let i=1; i<inp_len; i++) {
    result = gcd_for_two(inp_arr[i], result);
  }

  return result;
}

export function getMod(no, divisor) {
  return ((no % divisor) + divisor) % divisor;
}

export function parseFuncParams(label) {
  let paramArr = [],
    funcName = '',
    paramStr = '';

  if(label.endsWith('()')) {
    funcName = label.substring(0, label.length-2);
  } else if(!label.endsWith(')')) {
    funcName = label;
  } else if(!label.endsWith('()') && label.endsWith(')')) {
    let i = 0,
      startBracketPos = label.length;

    /* Parse through the characters in reverse to find the param start bracket */
    i = label.length-2;
    while(i >= 0) {
      if(label[i] == '(') {
        startBracketPos = i;
        break;
      } else if(label[i] == '"') {
        /* If quotes, skip all the chars till next quote */
        i--;
        while(label[i] != '"') i--;
      }
      i--;
    }

    funcName = label.substring(0, startBracketPos);
    paramStr = label.substring(startBracketPos+1, label.length-1);

    let paramStart = 0,
      paramName = '',
      paramModes = ['IN', 'OUT', 'INOUT', 'VARIADIC'];

    paramStart = i = 0;
    while(i < paramStr.length) {
      if(paramStr[i] == '"') {
        /* If quotes, skip all the chars till next quote */
        i++;
        while(paramStr[i] != '"') i++;
      } else if (paramStr[i] == ' ') {
        /* if paramName is already set, ignore till comma
         * Or if paramName is parsed as one of the modes, reset.
         */
        if(paramName == '' || paramModes.indexOf(paramName) > -1 ) {
          paramName = paramStr.substring(paramStart, i);
          paramStart = i+1;
        }
      }
      else if (paramStr[i] == ',') {
        paramArr.push([paramName, paramStr.substring(paramStart, i)]);
        paramName = '';
        paramStart = i+1;
      }
      i++;
    }
    paramArr.push([paramName, paramStr.substring(paramStart)]);
  }

  return {
    'func_name': funcName,
    'param_string': paramStr,
    'params': paramArr,
  };
}

export function quote_ident(value) {
  /* check if the string is number or not */
  let quoteIt = false;
  if (!isNaN(parseInt(value))){
    quoteIt = true;
  }

  if(value.search(/[^a-z0-9_]/g) > -1) {
    /* escape double quotes */
    value = value.replace(/"/g, '""');
    quoteIt = true;
  }

  if(quoteIt) {
    return `"${value}"`;
  } else {
    return value;
  }
}

export function fully_qualify(pgBrowser, data, item) {
  const parentData = getTreeNodeHierarchyFromIdentifier.call(pgBrowser, item);
  let namespace = '';

  if (parentData.schema !== undefined) {
    namespace = quote_ident(parentData.schema._label);
  }
  else if (parentData.view !== undefined) {
    namespace = quote_ident(parentData.view._label);
  }
  else if (parentData.catalog !== undefined) {
    namespace = quote_ident(parentData.catalog._label);
  }

  if (parentData.package !== undefined && data._type != 'package') {
    if(namespace == '') {
      namespace = quote_ident(parentData.package._label);
    } else {
      namespace += '.' + quote_ident(parentData.package._label);
    }
  }

  if(namespace != '') {
    return namespace + '.' + quote_ident(data._label);
  } else {
    return quote_ident(data._label);
  }
}

export function getRandomInt(min, max) {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function titleize(i_str) {
  if(i_str === '' || i_str === null) return i_str;
  return i_str.split(' ')
    .map(w => w[0].toUpperCase() + w.substr(1).toLowerCase())
    .join(' ');
}

export function sprintf(i_str) {
  try {
    let replaceArgs = arguments;
    return i_str.split('%s')
      .map(function(w, i) {
        if(i > 0) {
          if(i < replaceArgs.length) {
            return [replaceArgs[i], w].join('');
          } else {
            return ['%s', w].join('');
          }
        } else {
          return w;
        }
      })
      .join('');
  } catch(e) {
    console.error(e);
    return i_str;
  }
}

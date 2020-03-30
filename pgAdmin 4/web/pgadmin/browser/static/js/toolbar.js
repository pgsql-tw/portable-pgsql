/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2020, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////

import gettext from 'sources/gettext';
import _ from 'underscore';
import pgAdmin from 'sources/pgadmin';

let _toolbarButtons = {};
let _browserPanel = null;

// Default Tool Bar Buttons.
let _defaultToolBarButtons = [
  {
    label: gettext('Query Tool'),
    ariaLabel: gettext('Query Tool'),
    btnClass: 'pg-font-icon icon-query-tool',
    text: '',
    toggled: false,
    toggleClass: '',
    parentClass: 'pg-toolbar-btn btn-secondary',
    enabled: false,
  },
  {
    label: gettext('View Data'),
    ariaLabel: gettext('View Data'),
    btnClass: 'fa fa-table',
    text: '',
    toggled: false,
    toggleClass: '',
    parentClass: 'pg-toolbar-btn btn-secondary',
    enabled: false,
  },
  {
    label: gettext('Filtered Rows'),
    ariaLabel: gettext('Filtered Rows'),
    btnClass: 'pg-font-icon icon-filter-table-toolbar',
    text: '',
    toggled: false,
    toggleClass: '',
    parentClass: 'pg-toolbar-btn btn-secondary',
    enabled: false,
  },
];

// Place holder for non default tool bar buttons.
let _otherToolbarButtons = [];

// This function is used to add button into the browser panel.
function registerToolBarButton(btn) {
  /* Sometimes the panel onCreate is called two times.
   * Add buttons if not present in the panel also.
   */
  if (!(btn.label in _toolbarButtons)
        || (_.findIndex(_browserPanel._buttonList,{name:btn.label}) < 0)) {
    _browserPanel.addButton(
      btn.label, btn.btnClass, btn.text, btn.label, btn.toggled,
      btn.toggleClass, btn.parentClass, btn.enabled, btn.ariaLabel
    );

    _toolbarButtons[btn.label] = btn;
  }
}

// This function is used to add tool bar button and
// listen on the button event.
export function initializeToolbar(panel, wcDocker) {
  _browserPanel = panel;

  // Iterate through default tool bar buttons and add them into the
  // browser panel.
  _.each(_defaultToolBarButtons, (btn) => {
    registerToolBarButton(btn);
  });

  // Iterate through other tool bar buttons and add them into the
  // browser panel.
  _.each(_otherToolbarButtons, (btn) => {
    registerToolBarButton(btn);
  });

  // Listen on button click event.
  panel.on(wcDocker.EVENT.BUTTON, function(data) {
    if ('name' in data && data.name === gettext('Query Tool'))
      pgAdmin.DataGrid.show_query_tool('', pgAdmin.Browser.tree.selected());
    else if ('name' in data && data.name === gettext('View Data'))
      pgAdmin.DataGrid.show_data_grid({mnuid: 3}, pgAdmin.Browser.tree.selected());
    else if ('name' in data && data.name === gettext('Filtered Rows'))
      pgAdmin.DataGrid.show_filtered_row({mnuid: 4}, pgAdmin.Browser.tree.selected());
  });
}

// This function is used to enable/disable the specific button
// based on their label.
export function enable(label, enable) {
  if (label in _toolbarButtons) {
    _browserPanel.buttonEnable(label, enable);
  } else {
    console.warn('Developer warning: No tool button found with label: ' + label);
  }
}

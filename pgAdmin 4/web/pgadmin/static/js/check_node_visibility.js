//////////////////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2020, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////////////////

define(['jquery', 'underscore'],
  function ($, _) {

    var check_node_visibility = function (pgBrowser, node_type) {
      if(_.isUndefined(node_type) || _.isNull(node_type)) {
        return true;
      }

      // Target actual node instead of collection.
      // If node is disabled then there is no meaning of
      // adding collection node menu
      if(node_type.startsWith('coll-')) {
        node_type = node_type.replace('coll-', '');
      }

      // Exclude non-applicable nodes
      var nodes_not_supported = [
        'server_group', 'server', 'catalog_object_column',
      ];
      if(_.indexOf(nodes_not_supported, node_type) >= 0) {
        return true;
      }

      var preference = pgBrowser.get_preference('browser', 'show_node_'+node_type);

      if (preference) {
        return preference.value;
      }
      else {
        return true;
      }
    };

    return check_node_visibility;
  });

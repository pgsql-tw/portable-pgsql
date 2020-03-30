/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2020, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////

define('misc.dependencies', [
  'sources/gettext', 'underscore', 'jquery', 'backbone',
  'pgadmin', 'pgadmin.browser', 'pgadmin.alertifyjs', 'pgadmin.backgrid',
  'sources/utils',
], function(gettext, _, $, Backbone, pgAdmin, pgBrowser, Alertify, Backgrid, pgadminUtils) {

  if (pgBrowser.NodeDependencies)
    return pgBrowser.NodeDependencies;

  var wcDocker = window.wcDocker;

  pgBrowser.NodeDependencies = pgBrowser.NodeDependencies || {};

  _.extend(pgBrowser.NodeDependencies, {
    init: function() {
      if (this.initialized) {
        return;
      }

      this.initialized = true;
      this.dependenciesPanel = pgBrowser.docker.findPanels('dependencies')[0];
      /* Parameter is used to set the proper label of the
       * backgrid header cell.
       */
      _.bindAll(this, 'showDependencies', '__loadMoreRows', '__appendGridToPanel');

      // Defining Backbone Model for Dependencies.
      var Model = Backbone.Model.extend({
        defaults: {
          icon: 'icon-unknown',
          type: undefined,
          name: undefined,
          /* field contains 'Database Name' for 'Tablespace and Role node',
           * for other node it contains 'Restriction'.
           */
          field: undefined,
        },
        // This function is used to fetch/set the icon for the type(Function, Role, Database, ....)
        parse: function(res) {
          var node = pgBrowser.Nodes[res.type];
          if(res.icon == null || res.icon == '') {
            res.icon = node ? (_.isFunction(node['node_image']) ?
              (node['node_image']).apply(node, [null, null]) :
              (node['node_image'] || ('icon-' + res.type))) :
              ('icon-' + res.type);
          }
          res.type = pgadminUtils.titleize(res.type.replace(/_/g, ' '), true);
          return res;
        },
      });

      // Defining Backbone Collection for Dependencies.
      this.dependenciesCollection = new(Backbone.Collection.extend({
        model: Model,
      }))(null);

      pgBrowser.Events.on('pgadmin-browser:tree:selected', this.showDependencies);
      this.__appendGridToPanel();
    },

    /* Function is used to create and render backgrid with
       * empty collection. We just want to add backgrid into the
       * panel only once.
    */
    __appendGridToPanel: function() {
      var $container = this.dependenciesPanel.layout().scene().find('.pg-panel-content'),
        $gridContainer = $container.find('.pg-panel-dependencies-container'),
        grid = new Backgrid.Grid({
          emptyText: 'No data found',
          columns: [{
            name: 'type',
            label: gettext('Type'),
            // Extend it to render the icon as per the type.
            cell: Backgrid.Cell.extend({
              render: function() {
                Backgrid.Cell.prototype.render.apply(this, arguments);
                this.$el.prepend($('<i>', {
                  class: 'wcTabIcon ' + this.model.get('icon'),
                }));
                return this;
              },
            }),
            editable: false,
          },
          {
            name: 'name',
            label: gettext('Name'),
            cell: 'string',
            editable: false,
          },
          {
            name: 'field',
            label: '', // label kept blank, it will change dynamically
            cell: 'string',
            editable: false,
          },
          ],

          collection: this.dependenciesCollection,
          className: 'backgrid table presentation table-bordered table-noouter-border table-hover',
        });

      // Condition is used to save grid object to change the label of the header.
      this.dependenciesGrid = grid;

      $gridContainer.append(grid.render().el);

      return true;
    },

    // Fetch the actual data and update the collection
    showDependencies: function(item, data, node) {
      let self = this,
        msg = gettext('Please select an object in the tree view.'),
        panel = this.dependenciesPanel,
        $container = panel.layout().scene().find('.pg-panel-content'),
        $msgContainer = $container.find('.pg-panel-depends-message'),
        $gridContainer = $container.find('.pg-panel-dependencies-container'),
        treeHierarchy = node.getTreeNodeHierarchy(item),
        n_type = data._type,
        url = node.generate_url(item, 'dependency', data, true);

      if (node) {
        /* We fetch the Dependencies and Dependencies tab only for
         * those node who set the parameter hasDepends to true.
         */
        msg = gettext('No dependency information is available for the selected object.');
        if (node.hasDepends) {
          /* Updating the label for the 'field' type of the backbone model.
           * Label should be "Database" if the node type is tablespace or role
           * and dependencies tab is selected. For other nodes and dependencies tab
           * it should be 'Restriction'.
           */

          this.dependenciesGrid.columns.models[2].set({
            'label': gettext('Restriction'),
          });

          // Hide message container and show grid container.
          $msgContainer.addClass('d-none');
          $gridContainer.removeClass('d-none');

          var timer = '';
          $.ajax({
            url: url,
            type: 'GET',
            beforeSend: function(xhr) {
              xhr.setRequestHeader(pgAdmin.csrf_token_header, pgAdmin.csrf_token);
              // Generate a timer for the request
              timer = setTimeout(function() {
                // notify user if request is taking longer than 1 second

                $msgContainer.text(gettext('Fetching dependency information from the server...'));
                $msgContainer.removeClass('d-none');
                msg = '';

              }, 1000);
            },
          })
            .done(function(res) {
              clearTimeout(timer);

              if (res.length > 0) {

                if (!$msgContainer.hasClass('d-none')) {
                  $msgContainer.addClass('d-none');
                }
                $gridContainer.removeClass('d-none');

                self.dependenciesData = res;

                // Load only 100 rows
                self.dependenciesCollection.reset(self.dependenciesData.splice(0, 100), {parse: true});

                // Load more rows on scroll down
                pgBrowser.Events.on(
                  'pgadmin-browser:panel-dependencies:' +
                wcDocker.EVENT.SCROLLED,
                  self.__loadMoreRows
                );

              } else {
                // Do not listen the scroll event
                pgBrowser.Events.off(
                  'pgadmin-browser:panel-dependencies:' +
                wcDocker.EVENT.SCROLLED
                );

                self.dependenciesCollection.reset({silent: true});
                $msgContainer.text(msg);
                $msgContainer.removeClass('d-none');

                if (!$gridContainer.hasClass('d-none')) {
                  $gridContainer.addClass('d-none');
                }
              }


            })
            .fail(function(xhr, error, message) {
              var _label = treeHierarchy[n_type].label;
              pgBrowser.Events.trigger(
                'pgadmin:node:retrieval:error', 'depends', xhr, error, message
              );
              if (!Alertify.pgHandleItemError(xhr, error, message, {
                item: item,
                info: treeHierarchy,
              })) {
                Alertify.pgNotifier(
                  error, xhr,
                  gettext('Error retrieving data from the server: %s', message || _label),
                  function(msg) {
                    if(msg === 'CRYPTKEY_SET') {
                      self.showDependencies(item, data, node);
                    } else {
                      console.warn(arguments);
                    }
                  });
              }
              // show failed message.
              $msgContainer.text(gettext('Failed to retrieve data from the server.'));
            });
        }
      } if (msg != '') {
        $msgContainer.text(msg);
        $msgContainer.removeClass('d-none');
        if (!$gridContainer.hasClass('d-none')) {
          $gridContainer.addClass('d-none');
        }
      }
    },
    __loadMoreRows: function() {
      if (this.dependenciesPanel.length < 1) return ;

      let elem = this.dependenciesPanel.$container.find('.pg-panel-dependencies-container').closest('.wcFrameCenter')[0];
      if ((elem.scrollHeight - 10) < elem.scrollTop + elem.offsetHeight) {
        if (this.dependenciesData.length > 0) {
          this.dependenciesCollection.add(this.dependenciesData.splice(0, 100), {parse: true});
        }
      }
    },
  });

  return pgBrowser.NodeDependencies;
});

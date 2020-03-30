/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2020, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////

define('misc.dependents', [
  'sources/gettext', 'underscore', 'jquery', 'backbone',
  'sources/pgadmin', 'pgadmin.browser', 'pgadmin.alertifyjs', 'pgadmin.backgrid',
  'sources/utils',
], function(gettext, _, $, Backbone, pgAdmin, pgBrowser, Alertify, Backgrid, pgadminUtils) {

  if (pgBrowser.NodeDependents)
    return pgBrowser.NodeDependents;

  var wcDocker = window.wcDocker;

  pgBrowser.NodeDependents = pgBrowser.NodeDependents || {};

  _.extend(pgBrowser.NodeDependents, {
    init: function() {
      if (this.initialized) {
        return;
      }

      this.initialized = true;
      this.dependentsPanel = pgBrowser.docker.findPanels('dependents')[0];
      /* Parameter is used to set the proper label of the
       * backgrid header cell.
       */
      _.bindAll(this, 'showDependents', '__loadMoreRows', '__appendGridToPanel');

      // Defining Backbone Model for Dependents.
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

      // Defining Backbone Collection for Dependents.
      this.dependentCollection = new(Backbone.Collection.extend({
        model: Model,
      }))(null);

      pgBrowser.Events.on('pgadmin-browser:tree:selected', this.showDependents);
      pgBrowser.Events.on('pgadmin-browser:tree:refreshing', this.refreshDependents, this);
      this.__appendGridToPanel();
    },

    /* Function is used to create and render backgrid with
       * empty collection. We just want to add backgrid into the
       * panel only once.
    */
    __appendGridToPanel: function() {
      var $container = this.dependentsPanel.layout().scene().find('.pg-panel-content'),
        $gridContainer = $container.find('.pg-panel-dependents-container'),
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

          collection: this.dependentCollection,
          className: 'backgrid table presentation table-bordered table-noouter-border table-hover',
        });

      // Condition is used to save grid object to change the label of the header.
      this.dependentGrid = grid;

      $gridContainer.append(grid.render().el);

      return true;
    },

    // Fetch the actual data and update the collection
    showDependents: function(item, data, node) {
      let self = this,
        msg = gettext('Please select an object in the tree view.'),
        panel = this.dependentsPanel,
        $container = panel.layout().scene().find('.pg-panel-content'),
        $msgContainer = $container.find('.pg-panel-depends-message'),
        $gridContainer = $container.find('.pg-panel-dependents-container'),
        treeHierarchy = node.getTreeNodeHierarchy(item),
        n_type = data._type,
        url = node.generate_url(item, 'dependent', data, true);

      if (node) {
        /* We fetch the Dependencies and Dependents tab only for
         * those node who set the parameter hasDepends to true.
         */
        msg = gettext('No dependent information is available for the selected object.');
        if (node.hasDepends) {
          /* Updating the label for the 'field' type of the backbone model.
           * Label should be "Database" if the node type is tablespace or role
           * and dependent tab is selected. For other nodes and dependencies tab
           * it should be 'Restriction'.
           */
          if (node.type == 'tablespace' || node.type == 'role') {
            this.dependentGrid.columns.models[2].set({
              'label': gettext('Database'),
            });
          } else {
            this.dependentGrid.columns.models[2].set({
              'label': gettext('Restriction'),
            });
          }

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

                $msgContainer.text(gettext('Fetching dependent information from the server...'));
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

                self.dependentData = res;

                // Load only 100 rows
                self.dependentCollection.reset(self.dependentData.splice(0, 100), {parse: true});

                // Load more rows on scroll down
                pgBrowser.Events.on(
                  'pgadmin-browser:panel-dependents:' +
                wcDocker.EVENT.SCROLLED,
                  self.__loadMoreRows
                );

              } else {
                // Do not listen the scroll event
                pgBrowser.Events.off(
                  'pgadmin-browser:panel-dependents:' +
                wcDocker.EVENT.SCROLLED
                );

                self.dependentCollection.reset({silent: true});
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
                      self.showDependents(item, data, node);
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
      if (this.dependentsPanel.length < 1) return ;

      let elem = this.dependentsPanel.$container.find('.pg-panel-dependents-container').closest('.wcFrameCenter')[0];
      if ((elem.scrollHeight - 10) < elem.scrollTop + elem.offsetHeight) {
        if (this.dependentData.length > 0) {
          this.dependentCollection.add(this.dependentData.splice(0, 100), {parse: true});
        }
      }
    },
  });

  return pgBrowser.NodeDependents;
});

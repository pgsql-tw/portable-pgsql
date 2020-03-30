/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2020, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////

define('pgadmin.node.table_partition_utils', [
  'sources/gettext', 'jquery', 'underscore', 'backbone', 'pgadmin.browser',
  'pgadmin.backform','pgadmin.backgrid', 'pgadmin.browser.collection',
], function(gettext, $, _, Backbone, pgBrowser, Backform, Backgrid) {

  Backgrid.PartitionRow = Backgrid.Row.extend({
    modelDuplicateClass: 'bg-model-duplicate',

    initialize: function () {
      Backgrid.Row.prototype.initialize.apply(this, arguments);
      var self = this;
      self.model.on('change:is_attach', function() {
        setTimeout(function() {
          self.columns.each(function(col) {
            if (col.get('name') == 'partition_name') {
              var idx = self.columns.indexOf(col),
                cf = col.get('cellFunction'),
                cell = new (cf.apply(col, [self.model]))({
                  column: col,
                  model: self.model,
                }),
                oldCell = self.cells[idx];
              oldCell.remove();
              self.cells[idx] = cell;
              self.render();
            }
          });
        }, 10);
      });
      self.listenTo(self.model, 'pgadmin-session:model:duplicate', self.modelDuplicate);
      self.listenTo(self.model, 'pgadmin-session:model:unique', self.modelUnique);
    },
    modelDuplicate: function() {
      $(this.el).removeClass('new');
      $(this.el).addClass(this.modelDuplicateClass);
    },
    modelUnique: function() {
      $(this.el).removeClass(this.modelDuplicateClass);
    },
  });

  var getPartitionCell = function(model) {
    var is_attach = model.get('is_attach');
    if (is_attach) {
      var options = [];
      model.set({'partition_name': undefined}, {silent:true});
      _.each(model.top.table_options, function(t) {
        options.push([t.label, t.value]);
      });
      return Backgrid.Extension.Select2Cell.extend({optionValues: options});

    } else {
      return Backgrid.StringCell;
    }
  };

  Backform.PartitionKeyModel = pgBrowser.Node.Model.extend({
    defaults: {
      key_type: 'column',
      pt_column: undefined,
      expression: undefined,
    },
    keys:['pt_column'],
    schema: [{
      id: 'key_type', label: gettext('Key type'), type:'select2', editable: true,
      cell:'select2', cellHeaderClasses: 'width_percent_25',
      select2: {allowClear: false},
      options:[{
        label: gettext('Column'), value: 'column',
      },{
        label: gettext('Expression'), value: 'expression',
      }],
    },{
      id: 'pt_column', label: gettext('Column'), type:'text',
      cell: Backgrid.Extension.Select2DepCell.extend({
        keyPathAccessor: function(obj, path) {
          var res = obj;
          if(_.isArray(res)) {
            return _.map(res, function(o) { return o['pt_column'];
            });
          }
          path = path.split('.');
          for (var i = 0; i < path.length; i++) {
            if (_.isNull(res)) return null;
            if (_.isEmpty(path[i])) continue;
            if (!_.isUndefined(res[path[i]])) res = res[path[i]];
          }
          return _.isObject(res) && !_.isArray(res) ? null : res;
        },
        initialize: function() {
          // Here we will decide if we need to call URL
          // Or fetch the data from parent columns collection
          var self = this;
          if(this.model.handler) {
            Backgrid.Extension.Select2DepCell.prototype.initialize.apply(this, arguments);
            // Do not listen for any event(s) for existing constraint.
            if (_.isUndefined(self.model.get('oid'))) {
              var tableCols = self.model.top.get('columns');
              self.listenTo(tableCols, 'remove' , self.resetColOptions);
              self.listenTo(tableCols, 'change:name', self.resetColOptions);
            }

            self.custom_options();
          }
        },
        resetColOptions: function() {
          var self = this;

          setTimeout(function () {
            self.custom_options();
            self.render.apply(self);
          }, 50);
        },
        custom_options: function() {
          // We will add all the columns entered by user in table model
          var columns = this.model.top.get('columns'),
            typename = this.model.top.get('typname'),
            of_types_tables = this.model.top.of_types_tables,
            added_columns_from_tables = [];

          if (columns.length > 0) {
            _.each(columns.models, function(m) {
              var col = m.get('name');
              if(!_.isUndefined(col) && !_.isNull(col)) {
                added_columns_from_tables.push(
                  {label: col, value: col, image:'icon-column'}
                );
              }
            });
          } else if (!_.isUndefined(typename) && !_.isNull(typename)
              && !_.isUndefined(of_types_tables) && of_types_tables.length > 0) {
            // Iterate through all the of_type tables
            _.each(of_types_tables, function(type) {
              if (type.label == typename) {
                // Iterate all the columns of selected "OF TYPE".
                _.each(type.oftype_columns, function(col) {
                  added_columns_from_tables.push(
                    {label: col.name, value: col.name, image:'icon-column'}
                  );
                });
              }
            });
          }

          // Set the values in to options so that user can select
          this.column.set('options', added_columns_from_tables);
        },
        remove: function() {
          if(this.model.handler) {
            var self = this,
              tableCols = self.model.top.get('columns');
            self.stopListening(tableCols, 'remove' , self.resetColOptions);
            self.stopListening(tableCols, 'change:name' , self.resetColOptions);
            Backgrid.Extension.Select2DepCell.prototype.remove.apply(this, arguments);
          }
        },
      }),
      deps: ['key_type'],
      cellHeaderClasses: 'width_percent_30',
      transform : function(data){
        var res = [];
        if (data && _.isArray(data)) {
          _.each(data, function(d) {
            res.push({label: d.label, value: d.label, image:'icon-column'});
          });
        }
        return res;
      },
      select2:{allowClear:false},
      editable: function(m) {
        if (m.get('key_type') == 'expression') {
          setTimeout( function() {
            m.set('pt_column', undefined);
          }, 10);
          return false;
        }
        return true;
      },
    },{
      id: 'expression', label: gettext('Expression'), type:'text',
      cell:Backgrid.Extension.StringDepCell,
      cellHeaderClasses: 'width_percent_45',
      deps: ['key_type'],
      editable: function(m) {
        if (m.get('key_type') == 'column') {
          setTimeout( function() {
            m.set('expression', undefined);
          }, 10);
          return false;
        }
        return true;
      },
    },
    ],
    validate: function() {
      var col_type = this.get('key_type'),
        pt_column = this.get('pt_column'),
        expression = this.get('expression'),
        msg;

      // Have to clear existing validation before initiating current state
      // validation only
      this.errorModel.clear();

      if (_.isUndefined(col_type) || _.isNull(col_type) ||
        String(col_type).replace(/^\s+|\s+$/g, '') == '') {
        msg = gettext('Partition key type cannot be empty.');
        this.errorModel.set('key_type', msg);
        return msg;
      }
      else if (col_type == 'column' &&
        _.isUndefined(pt_column) || _.isNull(pt_column) ||
        String(pt_column).replace(/^\s+|\s+$/g, '') == '') {
        msg = gettext('Partition key column cannot be empty.');
        this.errorModel.set('pt_column', msg);
        return msg;
      }
      else if (col_type == 'expression' &&
        _.isUndefined(expression) || _.isNull(expression) ||
        String(expression).replace(/^\s+|\s+$/g, '') == '') {
        msg = gettext('Partition key expression cannot be empty.');
        this.errorModel.set('expression', msg);
        return msg;
      }

      return null;
    },
  });

  Backform.PartitionsModel = pgBrowser.Node.Model.extend({
    idAttribute: 'oid',
    defaults: {
      oid: undefined,
      is_attach: false,
      partition_name: undefined,
      is_default: undefined,
      values_from: undefined,
      values_to: undefined,
      values_in: undefined,
      values_modulus: undefined,
      values_remainder: undefined,
      is_sub_partitioned: false,
      sub_partition_type: 'range',
    },
    keys:['partition_name'],
    schema: [{
      id: 'oid', label: gettext('OID'), type: 'text',
      mode: ['properties'],
    },{
      id: 'is_attach', label:gettext('Operation'), cell: 'switch', type: 'switch',
      options: {'onText': gettext('Attach'), 'offText': gettext('Create'), 'width': 65},
      cellHeaderClasses: 'width_percent_5',
      editable: function(m) {
        if (m instanceof Backbone.Model && m.isNew() && !m.top.isNew())
          return true;
        return false;
      },
      disabled: function(m) {
        if (m instanceof Backbone.Model && m.isNew() && !m.top.isNew())
          return false;
        return true;
      },
    },{
      id: 'partition_name', label: gettext('Name'), type: 'text', cell:'string',
      cellHeaderClasses: 'width_percent_15',
      editable: function(m) {
        if (m instanceof Backbone.Model && m.isNew())
          return true;
        return false;
      }, cellFunction: getPartitionCell,
      disabled: function(m) {
        if (m instanceof Backbone.Model && m.isNew())
          return false;
        return true;
      },
    },{
      id: 'is_default', label: gettext('Default'), type: 'switch', cell:'switch',
      cellHeaderClasses: 'width_percent_5',  min_version: 110000,
      options: {'onText': gettext('Yes'), 'offText': gettext('No')},
      editable: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          (m.handler.top.attributes.partition_type === 'range' ||
          m.handler.top.attributes.partition_type === 'list') &&
          m instanceof Backbone.Model && m.isNew() &&
          m.handler.top.node_info.server.version >= 110000)
          return true;
        return false;
      },
      disabled: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          (m.handler.top.attributes.partition_type === 'range' ||
          m.handler.top.attributes.partition_type === 'list') &&
          m instanceof Backbone.Model && m.isNew() &&
          m.handler.top.node_info.server.version >= 110000)
          return false;
        return true;
      },
    },{
      id: 'values_from', label: gettext('From'), type:'text',
      cell:Backgrid.Extension.StringDepCell, deps: ['is_default'],
      cellHeaderClasses: 'width_percent_15',
      editable: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'range' &&
          m instanceof Backbone.Model && m.isNew() && m.get('is_default') !== true)
          return true;
        return false;
      },
      disabled: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'range' &&
          m instanceof Backbone.Model && m.isNew() && m.get('is_default') !== true)
          return false;
        return true;
      },
    },{
      id: 'values_to', label: gettext('To'), type:'text',
      cell:Backgrid.Extension.StringDepCell, deps: ['is_default'],
      cellHeaderClasses: 'width_percent_15',
      editable: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'range' &&
          m instanceof Backbone.Model && m.isNew() && m.get('is_default') !== true)
          return true;
        return false;
      },
      disabled: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'range' &&
          m instanceof Backbone.Model && m.isNew() && m.get('is_default') !== true)
          return false;
        return true;
      },
    },{
      id: 'values_in', label: gettext('In'), type:'text',
      cell:Backgrid.Extension.StringDepCell, deps: ['is_default'],
      cellHeaderClasses: 'width_percent_15',
      editable: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'list' &&
          m instanceof Backbone.Model && m.isNew() && m.get('is_default') !== true)
          return true;
        return false;
      },
      disabled: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'list' &&
          m instanceof Backbone.Model && m.isNew() && m.get('is_default') !== true)
          return false;
        return true;
      },
    },{
      id: 'values_modulus', label: gettext('Modulus'), type:'int',
      cell:Backgrid.Extension.StringDepCell,
      cellHeaderClasses: 'width_percent_15',
      editable: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'hash' &&
          m instanceof Backbone.Model && m.isNew())
          return true;
        return false;
      },
      disabled: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'hash' &&
          m instanceof Backbone.Model && m.isNew())
          return false;
        return true;
      },
    },{
      id: 'values_remainder', label: gettext('Remainder'), type:'int',
      cell:Backgrid.Extension.StringDepCell,
      cellHeaderClasses: 'width_percent_15 width_percent_20',
      editable: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'hash' &&
          m instanceof Backbone.Model && m.isNew())
          return true;
        return false;
      },
      disabled: function(m) {
        if(m.handler && m.handler.top &&
          m.handler.top.attributes &&
          m.handler.top.attributes.partition_type === 'hash' &&
          m instanceof Backbone.Model && m.isNew())
          return false;
        return true;
      },
    },{
      id: 'is_sub_partitioned', label:gettext('Partitioned table?'), cell: 'switch',
      group: 'Partition', type: 'switch', mode: ['properties', 'create', 'edit'],
      deps: ['is_attach'],
      disabled: function(m) {
        if(!m.isNew())
          return true;

        if (m.get('is_attach')) {
          setTimeout( function() {
            m.set('is_sub_partitioned', false);
          }, 10);
          return true;
        }
        return false;
      },
    },{
      id: 'sub_partition_type', label:gettext('Partition Type'),
      editable: false, type: 'select2', select2: {allowClear: false},
      group: 'Partition', deps: ['is_sub_partitioned'],
      options: function() {
        var options = [{
          label: gettext('Range'), value: 'range',
        },{
          label: gettext('List'), value: 'list',
        }];

        if(!_.isUndefined(this.node_info) && !_.isUndefined(this.node_info.server)
          && !_.isUndefined(this.node_info.server.version) &&
            this.node_info.server.version >= 110000) {
          options.push({
            label: gettext('Hash'), value: 'hash',
          });
        }
        return options;
      },
      visible: function(m) {
        if (m.isNew())
          return true;
        return false;
      },
      disabled: function(m) {
        if (!m.isNew() || !m.get('is_sub_partitioned'))
          return true;
        return false;
      },
    },{
      id: 'sub_partition_keys', label:gettext('Partition Keys'),
      model: Backform.PartitionKeyModel,
      subnode: Backform.PartitionKeyModel,
      editable: true, type: 'collection',
      group: 'Partition', mode: ['properties', 'create', 'edit'],
      deps: ['is_sub_partitioned', 'sub_partition_type'],
      canEdit: false, canDelete: true,
      control: 'sub-node-collection',
      canAdd: function(m) {
        if (m.isNew() && m.get('is_sub_partitioned'))
          return true;
        return false;
      },
      canAddRow: function(m) {
        var columns = m.top.get('columns'),
          typename = m.top.get('typname'),
          columns_exist= false;

        var max_row_count = 1000;
        if (m.get('sub_partition_type') && m.get('sub_partition_type') == 'list')
          max_row_count = 1;

        /* If columns are not specified by the user then it may be
           * possible that he/she selected 'OF TYPE', so we should check
           * for that as well.
           */
        if (columns.length <= 0 && !_.isUndefined(typename)
          && !_.isNull(typename) && m.of_types_tables.length > 0){
          _.each(m.of_types_tables, function(data) {
            if (data.label == typename && data.oftype_columns.length > 0){
              columns_exist = true;
            }
          });
        } else if (columns.length > 0) {
          columns_exist = _.some(columns.pluck('name'));
        }

        return (m.get('sub_partition_keys') &&
          m.get('sub_partition_keys').length < max_row_count && columns_exist
        );

      },
      disabled: function(m) {
        if (m.get('sub_partition_keys') && m.get('sub_partition_keys').models.length > 0) {
          setTimeout(function () {
            var coll = m.get('sub_partition_keys');
            coll.remove(coll.filter(function() { return true; }));

          }, 10);
        }
      },
      visible: function(m) {
        if (m.isNew())
          return true;
        return false;
      },
    },{
      id: 'sub_partition_scheme', label: gettext('Partition Scheme'),
      type: 'note', group: 'Partition', mode: ['edit'],
      visible: function(m) {
        if (!m.isNew() && !_.isUndefined(m.get('sub_partition_scheme')) &&
          m.get('sub_partition_scheme') != '')
          return true;
        return false;
      },
      disabled: function(m) {
        if (!m.isNew()) {
          this.text = m.get('sub_partition_scheme');
        }
      },
    }],
    validate: function() {
      var partition_name = this.get('partition_name'),
        is_default = this.get('is_default'),
        values_from = this.get('values_from'),
        values_to = this.get('values_to'),
        values_in = this.get('values_in'),
        values_modulus = this.get('values_modulus'),
        values_remainder = this.get('values_remainder'),
        is_sub_partitioned = this.get('is_sub_partitioned'),
        sub_partition_keys = this.get('sub_partition_keys'),
        msg;

      // Have to clear existing validation before initiating current state
      // validation only
      this.errorModel.clear();
      this.top.errorModel.clear();

      if (_.isUndefined(partition_name) || _.isNull(partition_name) ||
       String(partition_name).replace(/^\s+|\s+$/g, '') === '') {
        msg = gettext('Partition name cannot be empty.');
        this.errorModel.set('partition_name', msg);
        return msg;
      }

      if (is_sub_partitioned && this.isNew() &&
        !_.isNull(sub_partition_keys) && sub_partition_keys.length <= 0) {
        msg = gettext('Please specify at least one key for partitioned table.');
        this.top.errorModel.set('sub_partition_keys', msg);
        return msg;
      }

      if (this.top.get('partition_type') === 'range') {
        if (is_default !== true && (_.isUndefined(values_from) ||
         _.isNull(values_from) || String(values_from).replace(/^\s+|\s+$/g, '') === '')) {
          msg = gettext('For range partition From field cannot be empty.');
          this.errorModel.set('values_from', msg);
          return msg;
        } else if (is_default !== true && (_.isUndefined(values_to) || _.isNull(values_to) ||
          String(values_to).replace(/^\s+|\s+$/g, '') === '')) {
          msg = gettext('For range partition To field cannot be empty.');
          this.errorModel.set('values_to', msg);
          return msg;
        }
      } else if (this.top.get('partition_type') === 'list') {
        if (is_default !== true && (_.isUndefined(values_in) || _.isNull(values_in) ||
          String(values_in).replace(/^\s+|\s+$/g, '') === '')) {
          msg = gettext('For list partition In field cannot be empty.');
          this.errorModel.set('values_in', msg);
          return msg;
        }
      } else if (this.top.get('partition_type') === 'hash') {
        if (_.isUndefined(values_modulus) || _.isNull(values_modulus) ||
          String(values_modulus).replace(/^\s+|\s+$/g, '') === '') {
          msg = gettext('For hash partition Modulus field cannot be empty.');
          this.errorModel.set('values_modulus', msg);
          return msg;
        } else if (_.isUndefined(values_remainder) || _.isNull(values_remainder) ||
          String(values_remainder).replace(/^\s+|\s+$/g, '') === '') {
          msg = gettext('For hash partition Remainder field cannot be empty.');
          this.errorModel.set('values_remainder', msg);
          return msg;
        }
      }

      return null;
    },
  });

});

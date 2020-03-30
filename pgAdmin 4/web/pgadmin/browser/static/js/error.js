/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2020, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////

define(
  ['sources/gettext', 'underscore', 'alertify', 'sources/pgadmin'],
  function(gettext, _, alertify, pgAdmin) {
    pgAdmin.Browser = pgAdmin.Browser || {};

    _.extend(pgAdmin.Browser, {
      report_error: function(title, message, info) {
        title = _.escape(title);
        message = _.escape(message);
        info = _.escape(info);
        let text = '<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">\
           <div class="panel panel-default">\
           <div class="panel-heading" role="tab" id="headingOne">\
           <h4 class="panel-title">\
           <a data-toggle="collapse" data-parent="#accordion" href="#collapseOne" aria-expanded="true" aria-controls="collapseOne">\
           ' + gettext('Error message') + '</a>\
        </h4>\
        </div>\
        <div id="collapseOne" class="panel-collapse collapse show" role="tabpanel" aria-labelledby="headingOne">\
        <div class="panel-body" style="overflow: auto;">' + message + '</div>\
        </div>\
        </div>';

        if (info != null && info != '') {
          text += '<div class="panel panel-default">\
            <div class="panel-heading" role="tab" id="headingTwo">\
            <h4 class="panel-title">\
            <a class="collapsed" data-toggle="collapse" data-parent="#accordion" href="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">\
            ' + gettext('Additional info') + '</a>\
          </h4>\
          </div>\
          <div id="collapseTwo" class="panel-collapse collapse" role="tabpanel" aria-labelledby="headingTwo">\
          <div class="panel-body" style="overflow: auto;">' + info + '</div>\
          </div>\
          </div>\
          </div>';
        }

        text += '</div>';
        alertify.alert(
          title,
          text
        ).set('closable', true);
      },
    });

    return pgAdmin.Browser.report_error;
  });

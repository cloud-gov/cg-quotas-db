var Backbone = require('backbone');
var $ = require('jquery');
var _ = require('underscore');

var QuotaModel = Backbone.Model.extend({
  url: '/api/quotas/',
  idAttribute: 'guid',
  defaults: {
    'guid': undefined,
    'name': 'default',
    'created_at': undefined,
    'updated_at': undefined,
    'memory': [],
  }
});

module.exports = QuotaModel;

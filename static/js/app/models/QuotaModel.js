var Backbone = require('backbone');
var $ = require('jquery');
var _ = require('underscore');

var QuotaModel = Backbone.Model.extend({
  defaults: {
    'guid': undefined,
    'data': [],
    'name': 'default',
    'services': []
  }
});

module.exports = QuotaModel;

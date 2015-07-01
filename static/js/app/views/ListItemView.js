var fs = require('fs');

var Backbone = require('backbone');
var _ = require('underscore');

var QuotaModel = require('../models/QuotaModel');
var templateHtml = fs.readFileSync(__dirname + '/../templates/ListItemView.html').toString();

var ListItemView = Backbone.View.extend({
  tagName: 'tr',
  model: QuotaModel,
  template: _.template(templateHtml),
  initialize: function initialize () {
    this.render();
  },
  render: function render () {
    var quota = this.model.toJSON();
    quota['cost'] = quota['cost'].toFixed(2);
    var html = this.template(quota);
    this.$el.html(html);
  }
});

module.exports = ListItemView;

var fs = require('fs');

var Backbone = require('backbone');
var _ = require('underscore');

var QuotaModel = require('../models/QuotaModel');
var templateHtml = fs.readFileSync(__dirname + '/../templates/DetailView.html').toString();

var DetailView = Backbone.View.extend({
  model: QuotaModel,
  template: _.template(templateHtml),
  initialize: function initialize () {
    this.render();
  },
  render: function render () {
    var html = this.template(this.model.toJSON());
    this.$el.html(html);
  }
});

module.exports = DetailView;

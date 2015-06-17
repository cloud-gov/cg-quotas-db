var fs = require('fs');

var Backbone = require('backbone');
var _ = require('underscore');

var QuotaModel = require('../models/QuotaModel');
var templateHtml = fs.readFileSync(__dirname + '/../templates/DetailView.html').toString();

var DetailView = Backbone.View.extend({
  tagName: 'div',
  model: QuotaModel,
  template: _.template(templateHtml),
  initialize: function initialize () {
    this.render();
  },
  render: function render () {
    console.log('rendering');
    var html = this.template(this.model.toJSON());
    this.$el.html(html);
  }
});

module.exports = DetailView;

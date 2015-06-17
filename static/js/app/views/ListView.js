var fs = require('fs');

var Backbone = require('backbone');
var _ = require('underscore');

var ListItemView = require('./ListItemView');

var formControlHtml = fs.readFileSync(__dirname + '/../templates/FormControlsView.html').toString();
var formTemplate = _.template(formControlHtml);
var listTemplateHtml = fs.readFileSync(__dirname + '/../templates/ListView.html').toString();

var ListView = Backbone.View.extend({
  initialize: function initialize () {
    this.listenTo(this.collection, 'sync', this.render);
  },
  render: function render () {
    this.$el.html(listTemplateHtml);
    var formControls = this.$('formset');
    var tbody = this.$('tbody');

    var formHtml = formTemplate({ collection: this.collection.toJSON() });
    formControls.html(formHtml);

    this.collection.each(function(model) {
       var quota = new ListItemView({ model: model });
       tbody.append(quota.$el);
     }, this);
  }
});

module.exports = ListView;

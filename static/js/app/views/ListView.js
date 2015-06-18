var fs = require('fs');

var Backbone = require('backbone');
var _ = require('underscore');

var ListItemView = require('./ListItemView');

var formControlHtml = fs.readFileSync(__dirname + '/../templates/FormControlsView.html').toString();
var formTemplate = _.template(formControlHtml);
var listTemplateHtml = fs.readFileSync(__dirname + '/../templates/ListView.html').toString();

var ListView = Backbone.View.extend({
  events: {
    'click #filter-action': 'filter',
    'click #reset-action': 'clearFilter',
    'click #download-csv-action': 'downloadCSV'
  },
  initialize: function initialize () {
    this.listenTo(this.collection, 'sync', this.render);
    this.listenTo(this.collection, 'update', function (x){
      console.log('x', x);
    });
  },
  render: function render () {
    console.log('rendering');
    this.$el.html(listTemplateHtml);
    var formControls = this.$('form');
    var tbody = this.$('tbody');

    var formHtml = formTemplate({ collection: this.collection.toJSON() });
    formControls.html(formHtml);

    this.collection.each(function(model) {
       var quota = new ListItemView({ model: model });
       tbody.append(quota.$el);
     }, this);
  },
  filter: function filter (e) {
    e.preventDefault();
    var formData = this.$('form').serializeArray();
    var filterData = {};
    _.each(formData, function(field) {
      if (field.value != '') { filterData[field.name] = field.value; }
    });
    this.collection.filterByDates(filterData['since-date'], filterData['until-date'], filterData['quota-selection']);
  },
  clearFilter: function clearFilter (e) {
    e.preventDefault();
    this.$('form')[0].reset();
  },
  downloadCSV: function downloadCSV (e) {
    console.log('k, downloading.... (not really)');
  }
});

module.exports = ListView;

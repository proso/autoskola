'use strict';

/* Directives */


angular.module('blindMaps.directives', [])

  .directive('placeLabel', function () {
    return {
      restrict: 'A',
      template: '<i class="flag-{{place.code}}"></i> {{place.name}}',
      compile: function(element, attributes) {
        element.addClass('label');
        element.addClass('label-default');
      }
    };
  })
  
  .directive('blindMap', function (mapControler, places) {
    return {
      restrict: 'E',
      template: '<div class="map-container">' +
                  '<div id="map-holder">' +
                      '<div class="loading-indicator"></div>' +
                  '</div>' +
                  '<h1 ng-bind="name"></h1>' +
                  '<a  ng-show="practice"' +
                      'href="#/practice/{{part}}/"' +
                      'class="btn btn-primary btn-lg btn-practice" >' +
                    'Procvičovat' +
                  '</a>' +
                '</div>',
      link: function ($scope, elem, attrs) {
        $scope.name = places.getName($scope.part);
        $scope.practice = attrs.practice;
        var showTooltips = attrs.practice !== undefined;
        mapControler.init($scope.part, showTooltips);
      },
      replace: true
    };
  })
  
  .directive('email', function () {
    return {
      restrict: 'C',
      compile: function (elem, attrs) {
        var emailAddress = elem.html();
        emailAddress = emailAddress.replace("{zavinac}", "@");
        emailAddress = '<a href="mailto:'+emailAddress+'">'+ emailAddress+ '</a>';
        elem.html(emailAddress);
      }
    }
  })

  .directive('atooltip', function () {
    return {
      restrict: 'C',
      compile: function (elem, attrs) {      
        elem.tooltip({"placement" : "bottom"});
      }
    };
  })

  .directive('dropLogin', function () {
    return {
      restrict: 'C',
      compile: function (elem, attrs) { 
        elem.bind('click', function(){
          elem.tooltip('destroy');
          elem.parent().find(".tooltip").remove();
        })
      }
    };
  });
  
  


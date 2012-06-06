The geoportlet works as a wrapper around the exiting portlet types.

Usage
-----

When you select the "Geoportlet" type under "Manage portlets", the add
form lets you select from a database of countries and languages, and
choose a portlet type. In the next screen, you'll create the chosen
portlet (if it requires user input).

The geoportlet toggles its availability based on IP address lookup
and/or HTTP language accept strings. You can use it to segment the
audience for a portlet into particular countries or language groups,
e.g. China and Mandarin.

It uses the geolocation database provided by http://Software77.net.

Compatibility: Plone 4+.


HTML
----

Each geoportlet wraps the contained portlet assignment in an HTML
``<div>`` element with CSS-classes corresponding to the selected
countries and/or languages. The format is ``geoportlet-<country>`` and
``geoportlet-<language>`` where the country is provided as the
three-letter `ISO 3166-1 alpha-3
<http://en.wikipedia.org/wiki/ISO_3166-1_alpha-3>`_ country code and
the language is provided as the two-letter `ISO 639-1
<http://en.wikipedia.org/wiki/ISO_639-1>`_ language code::

  <div class="geoportlet-dnk geoportlet-da">
     <div class="portlet ...">
        ...
     </div>
  </div>

  
Author
------

Malthe Borch <mborch@gmail.com>

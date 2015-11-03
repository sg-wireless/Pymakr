# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module containing some HTML resources.
"""

from __future__ import unicode_literals

parseForms_js = """
(function (){
    var forms = new Array;
    for (var i = 0; i < document.forms.length; ++i) {
        var form = document.forms[i];
        var formObject = new Object;
        formObject.name = form.name;
        formObject.index = i
        var elements = new Array;
        for (var j = 0; j < form.elements.length; ++j) {
            var e = form.elements[j];
            var element = new Object;
            element.name = e.name;
            element.value = e.value;
            element.type = e.type;
            element.autocomplete = e.attributes.getNamedItem("autocomplete");
            if (element.autocomplete != null)
                element.autocomplete = element.autocomplete.value;
            elements.push(element);
        }
        formObject.elements = elements;
        forms.push(formObject);
    }
    return forms;
}());
"""

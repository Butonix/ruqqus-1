// Bold Text

makeBold = function (form) {
    var text = document.getElementById(form);
    var startIndex = text.selectionStart,
        endIndex = text.selectionEnd;
    var selectedText = text.value.substring(startIndex, endIndex);

    var format = '**'
    
    if (selectedText.includes('**')) {
    text.value = selectedText.replace(/\*/g, '');
    
    }
    else if (selectedText.length == 0) {
    text.value = text.value.substring(0, startIndex) + selectedText + text.value.substring(endIndex);
    }
    else {
        text.value = text.value.substring(0, startIndex) + format + selectedText + format + text.value.substring(endIndex);
    }
}

// Italicize Comment Text

makeItalics = function (form) {
    var text = document.getElementById(form);
    var startIndex = text.selectionStart,
        endIndex = text.selectionEnd;
    var selectedText = text.value.substring(startIndex, endIndex);

    var format = '*'
    
    if (selectedText.includes('*')) {
    text.value = selectedText.replace(/\*/g, '');
    
    }
    else if (selectedText.length == 0) {
    text.value = text.value.substring(0, startIndex) + selectedText + text.value.substring(endIndex);
    }
    else {
        text.value = text.value.substring(0, startIndex) + format + selectedText + format + text.value.substring(endIndex);
    }
}

// Quote Comment Text

makeQuote = function (form) {
    var text = document.getElementById(form);
    var startIndex = text.selectionStart,
        endIndex = text.selectionEnd;
    var selectedText = text.value.substring(startIndex, endIndex);

    var format = '>'
    
    if (selectedText.includes('>')) {
    text.value = selectedText.replace(/\>/g, '');
    
    }
    else if (selectedText.length == 0) {
    text.value = text.value.substring(0, startIndex) + selectedText + text.value.substring(endIndex);
    }
    else {
        text.value = text.value.substring(0, startIndex) + format + selectedText + text.value.substring(endIndex);
    }
}
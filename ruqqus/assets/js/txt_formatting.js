// Bold Text

makeBold = function () {
    var text = document.getElementById("comment-form");
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

// Bold Text

makeItalics = function () {
    var text = document.getElementById("comment-form");
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
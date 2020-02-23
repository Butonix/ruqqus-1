function getId(url) {
    var regExp = /^.*(bitchute.com\/|embed\)([^#\&\?]*).*/;
    var match = url.match(regExp);

    if (match && match[2].length == 12) {
        return match[2];
    } else {
        return 'error';
    }
}

var myUrl = $('#embedURL').text();

myId = getId(myUrl);

$('#ytEmbed').html('<iframe width="100%" height="475" src="//www.bitchute.com/embed/' + myId + '" frameborder="0" allowfullscreen></iframe>');
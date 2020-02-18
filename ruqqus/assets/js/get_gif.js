  function getGif(searchTerm) {

    if (searchTerm != null) {
      document.getElementById('gifSearch').value = searchTerm;
    }
    else {
      document.getElementById('gifSearch').value = null;
    }

    // categories var

    var cats = document.getElementById('GIFcats');

    // container var

    var container = document.getElementById('GIFs');

    // UI buttons

    var backBtn = document.getElementById('gifs-back-btn');

    var cancelBtn = document.getElementById('gifs-cancel-btn');

    container.innerHTML = '';

    if (searchTerm == null) {
      container.innerHTML = 'jinja template cats.html';

      backBtn.innerHTML = null;

      cancelBtn.innerHTML = null;
    }
    else {
      backBtn.innerHTML = '<button class="btn btn-link pl-3 pr-0" id="gifs-back-btn" onclick="getGif();"><i class="fas fa-long-arrow-left text-muted"></i></button>';

      cancelBtn.innerHTML = '<button class="btn btn-link pl-0 pr-3" id="gifs-cancel-btn" onclick="getGif();"><i class="fas fa-times text-muted"></i></button>';

          console.log('searchTerm is: ', searchTerm)
    $.ajax({
      url: "//api.giphy.com/v1/gifs/search?q=" + searchTerm + "&limit=12" + "&api_key=eOTkZX92KQM80g9NcBsq0heqZxZSVP86",
      type: "GET",
      success: function(response) {
        console.log(response)
        var max = response.data.length - 1 //length of response, minus 1 (cuz array starts at index 0)
        console.log('response.data.length is ', max)
        //var randomNumber = Math.round(Math.random() * max) //random number between 0 and max -1
        var randomNumber = Math.round(Math.random() * 6) //random number between 0 and max -1
        // GIF array
        var gifURL = [];

        // loop for fetching mutliple GIFs and creating the card divs
        for (var i = 0; i <= 12; i++) {
          gifURL[i] = "https://media.giphy.com/media/" + response.data[i].id + "/giphy.gif";
          container.innerHTML += ('<div class="card bg-secondary gif-keyboard-option" style="overflow: hidden" data-dismiss="modal" aria-label="Close" onclick="insertGIF(\'' + gifURL[i] + '\')"><img class="img-fluid" src="' + gifURL[i] + '"></div>');
        }
        console.log(container);
      },
      error: function(e) {
        alert(e);
      }
    });
    };
  }

  // Insert GIF markdown into comment box function

  function insertGIF(url) {

    var gif = "![](" + url +")";

    var commentBox = document.getElementById('comment-form');

    var old  = commentBox.value;

    commentBox.value = old + gif;

  }

  // When GIF keyboard is hidden, hide all GIFs

  $('#gifModal').on('hidden.bs.modal', function (e) {

    document.getElementById('gifSearch').value = null;

    // container var

    var container = document.getElementById('GIFs');

    container.innerHTML = '';
  
})

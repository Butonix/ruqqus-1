  function getGif(searchTerm) {

    if (searchTerm !== undefined) {
      document.getElementById('gifSearch').value = searchTerm;
    }
    else {
      document.getElementById('gifSearch').value = null;
    }

    // categories var

    var cats = document.getElementById('GIFcats');

    // container var

    var container = document.getElementById('GIFs');

    // modal body var

    var modalBody = document.getElementById('gif-modal-body')

    // UI buttons

    var backBtn = document.getElementById('gifs-back-btn');

    var cancelBtn = document.getElementById('gifs-cancel-btn');

    container.innerHTML = '';

    if (searchTerm == undefined) {
      container.innerHTML = '<div class="card" onclick="getGif(\'agree\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Agree</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'laugh\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Laugh</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'confused\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Confused</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'sad\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Sad</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'happy\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Happy</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'awesome\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Awesome</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'yes\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Yes</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif('no');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">No</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif('love');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Love</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'please\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Please</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'scared\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Scared</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'angry\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Angry</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'awkward\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Awkward</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'cringe\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Cringe</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'omg\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">OMG</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'why\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Why</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"></div>';

      backBtn.innerHTML = null;

      cancelBtn.innerHTML = null;
    }
    else {
      backBtn.innerHTML = '<button class="btn btn-link pl-3 pr-0" id="gifs-back-btn" onclick="getGif();"><i class="fas fa-long-arrow-left text-muted"></i></button>';

      cancelBtn.innerHTML = '<button class="btn btn-link pl-0 pr-3" id="gifs-cancel-btn" onclick="getGif();"><i class="fas fa-times text-muted"></i></button>';

      console.log('searchTerm is: ', searchTerm)
      $.ajax({
        url: "//api.giphy.com/v1/gifs/search?q=" + searchTerm + "&api_key=eOTkZX92KQM80g9NcBsq0heqZxZSVP86",
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
        if (max < 15 && max > 0) {
          for (var i = 0; i <= max; i++) {
            gifURL[i] = "https://media.giphy.com/media/" + response.data[i].id + "/giphy.gif";
            container.innerHTML += ('<div class="card bg-secondary gif-keyboard-option" style="overflow: hidden" data-dismiss="modal" aria-label="Close" onclick="insertGIF(\'' + gifURL[i] + '\')"><img class="img-fluid" src="' + gifURL[i] + '"></div>');
          }
        }
        else if (max <= 0) {
            container.innerHTML = '<div class="p-5"><div class="text-center"><div class="mb-3"><i class="fad fa-frown text-muted" style="font-size: 3.5rem;"></i></div><p>Aw shucks. No GIFs found...</p></div><div class="d-flex justify-content-center"><button class="btn btn-sm btn-outline-gray-500 mr-2" onclick="getGif(\'agree\');">Agree</button><button class="btn btn-sm btn-outline-gray-500 mr-2" onclick="getGif(\'disagree\');">Disagree</button><button class="btn btn-sm btn-outline-gray-500" onclick="getGif(\'laugh\');">Laugh</button></div></div>';
        }
        else {
          for (var i = 0; i <= 15; i++) {
            gifURL[i] = "https://media.giphy.com/media/" + response.data[i].id + "/giphy.gif";
            container.innerHTML += ('<div class="card bg-secondary gif-keyboard-option" style="overflow: hidden" data-dismiss="modal" aria-label="Close" onclick="insertGIF(\'' + gifURL[i] + '\')"><img class="img-fluid" src="' + gifURL[i] + '"></div>');
          }
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

    // UI buttons

    var backBtn = document.getElementById('gifs-back-btn');

    var cancelBtn = document.getElementById('gifs-cancel-btn');

    // Remove inner HTML from container var

    container.innerHTML = '<div class="card" onclick="getGif(\'agree\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Agree</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'laugh\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Laugh</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'confused\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Confused</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'sad\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Sad</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'happy\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Happy</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'awesome\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Awesome</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'yes\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Yes</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif('no');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">No</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif('love');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Love</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'please\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Please</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'scared\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Scared</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'angry\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Angry</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'awkward\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Awkward</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'cringe\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Cringe</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'omg\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">OMG</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"> </div> <div class="card" onclick="getGif(\'why\');" style="overflow: hidden;"> <div class="position-absolute text-center h-100 w-100" style="background-color: rgba(0, 0, 0, 0.35);"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Why</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/giphy.gif"></div>';

    // Hide UI buttons

    backBtn.innerHTML = null;

    cancelBtn.innerHTML = null;

  })

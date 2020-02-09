// Flag Comment

report_commentModal = function(id, author, board) {

  document.getElementById("comment-author").textContent = author;

  var offtopic = document.getElementById('report-comment-to-guild-dropdown-option')
  offtopic.innerHTML= 'This comment is off-topic for +' + board;
  offtopic.disabled=true;

    document.getElementById("reportCommentButton").onclick = function() {

      this.innerHTML='<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Reporting comment';
      this.disabled = true;
      post('/api/flag/comment/' + id,
        callback = function() {

          document.getElementById("reportCommentFormBefore").classList.add('d-none');
          document.getElementById("reportCommentFormAfter").classList.remove('d-none');
        }
        )
    }

};

$('#reportCommentModal').on('hidden.bs.modal', function () {

  var button = document.getElementById("reportCommentButton");

  var beforeModal = document.getElementById("reportCommentFormBefore");
  var afterModal = document.getElementById("reportCommentFormAfter");

  button.innerHTML='Report comment';
  button.disabled= false;
  afterModal.classList.add('d-none');

  if ( beforeModal.classList.contains('d-none') ) {
    beforeModal.classList.remove('d-none');
  }

});


// Flag Submission

report_postModal = function(id, author, board) {

  document.getElementById("post-author").textContent = author;

  offtopic=document.getElementById('report-post-to-guild-dropdown-option');
  offtopic.innerHTML= 'This post is off-topic for +' + board;

  if (board=='general') {
    offtopic.disabled=true;
  }
  else {
    offtopic.disabled=false;
  }

  selectbox=document.getElementById('report-type-dropdown');
  selectbox.value='reason_not_selected';

  submitbutton=document.getElementById("reportPostButton");
  submitbutton.disabled=true;

    submitbutton.onclick = function() {

      this.innerHTML='<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Reporting post';
      this.disabled = true;

      var xhr = new XMLHttpRequest();
      xhr.open("POST", '/api/flag/post/'+id, true);
      var form = new FormData()
      form.append("formkey", formkey());

      dropdown=document.getElementById("report-type-dropdown");
      form.append("report_type", dropdown.options[dropdown.selectedIndex].value);

      xhr.withCredentials=true;

      xhr.onload=function() {
        document.getElementById("reportPostFormBefore").classList.add('d-none');
        document.getElementById("reportPostFormAfter").classList.remove('d-none');
      };

      xhr.onerror=function(){alert(errortext)};
      xhr.send(form);

    }
};

$('#reportPostModal').on('hidden.bs.modal', function () {

  var button = document.getElementById("reportPostButton");

  var beforeModal = document.getElementById("reportPostFormBefore");
  var afterModal = document.getElementById("reportPostFormAfter");

  button.innerHTML='Report post';
  button.disabled= false;

  afterModal.classList.add('d-none');

  if ( beforeModal.classList.contains('d-none') ) {
    beforeModal.classList.remove('d-none');
  }

});
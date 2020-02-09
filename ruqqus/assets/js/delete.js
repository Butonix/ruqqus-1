// Delete Post

delete_postModal = function(id) {

  // Passed data for modal

  document.getElementById("deletePostButton").onclick = function() {  

    this.innerHTML='<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Deleting post';  
    this.disabled = true; 
    post('/delete_post/' + id,
      callback = function() {

        location.reload();
      }
      )
  }

};

// Delete Comment

delete_commentModal = function(id) {

  // Passed data for modal

  document.getElementById("deleteCommentButton").onclick = function() {  

    this.innerHTML='<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Deleting comment';  
    this.disabled = true; 
    post('/delete/comment/' + id,
      callback = function() {

        location.reload();
      }
      )
  }

};
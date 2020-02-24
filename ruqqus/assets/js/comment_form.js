
// Expand comment box on focus, hide otherwise

$('.comment-box').focus(function (event) {
    event.preventDefault();

    $(this).parent().parent().addClass("collapsed");

});


/*
$('.comment-box').blur(function () {
    event.preventDefault();

    $(this).parent().parent().removeClass("collapsed");
});

*/

//Comment edit form

toggleEdit=function(id){
    comment=document.getElementById("comment-text-"+id);
    form=document.getElementById("comment-edit-"+id);
    box=document.getElementById('edit-box-comment-'+id);
    actions = document.getElementById('comment-' + id +'-actions');

    comment.classList.toggle("d-none");
    form.classList.toggle("d-none");
    actions.classList.toggle("d-none");
    autoExpand(box);
}

togglePostEdit=function(id){

    body=document.getElementById("post-body"+id);
    form=document.getElementById("edit-post-body"+id);
    box=document.getElementById("post-edit-box"+id);
    actions = document.getElementById('comment-' + id +'-actions');

    body.classList.toggle("d-none");
    form.classList.toggle("d-none");
    actions.classList.toggle("d-none");
    autoExpand(box);
}
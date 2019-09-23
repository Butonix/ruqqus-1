$('.comment-box').focus(function () {
    event.preventDefault();

    $(this).parent().parent().addClass("collapsed");

});

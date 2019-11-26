
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


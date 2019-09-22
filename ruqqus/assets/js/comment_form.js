$('#comment-box').focus(function () {
    event.preventDefault();

    document.getElementById("comment-write").classList.add("collapsed");
});

$('#comment-box').blur(function () {
    event.preventDefault();

    document.getElementById("comment-write").classList.remove("collapsed");
});

// Enlarge thumbnail on post-img click

$(".post-img").click(function (event) {
    event.preventDefault();

    var id = $(this).parent().parent().parent().attr("id");

    document.getElementById(id).classList.toggle("enlarged");

});
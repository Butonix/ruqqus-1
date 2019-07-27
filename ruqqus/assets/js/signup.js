// Display username and password requirements on input

$('#password-register').on('input', function () {

    var charCount = document.getElementById("password-register").value;
    var id = document.getElementById("passwordHelpRegister");
    var successID = document.getElementById("passwordHelpSuccess");

    console.log(charCount.length);

    if (charCount.length >= 8) {
            id.classList.add("d-none");
            successID.classList.remove("d-none");
    }
    else {
            id.classList.remove("d-none");
            successID.classList.add("d-none");
    };

});

$('#username-register').on('input', function () {

    var charCount = document.getElementById("username-register").value;
    var id = document.getElementById("usernameHelpRegister");
    var successID = document.getElementById("usernameHelpSuccess");

    console.log(charCount.length);

    if (charCount.length >= 5) {
        id.classList.add("d-none");
        successID.classList.remove("d-none");
    }
    else {
        id.classList.remove("d-none");
        successID.classList.add("d-none");
    };

});

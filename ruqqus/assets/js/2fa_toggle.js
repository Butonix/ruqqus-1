$('#2faModal').on('hidden.bs.modal', function () {

  var box = document.getElementById("2faToggle");
  
  if (box.checked) {
    box.checked = false;
  } else {
    box.checked = true;
  }

});
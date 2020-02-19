function expandDesktopImage(image) {

$("#expandImageModal").modal("show");

document.getElementById("desktop-expanded-image").src = image;

document.getElementById("desktop-expanded-image-link").href = image;

}

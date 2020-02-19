function expandDesktopImage(image, link) {

$("#expandImageModal").modal("show");

document.getElementById("desktop-expanded-image").src = image;

document.getElementById("desktop-expanded-image-link").href = link;

}

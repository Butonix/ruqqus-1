function expandDesktopImage(image) {

// GIPHY attribution div

var attribution = document.getElementById("modal-image-attribution");

document.getElementById("desktop-expanded-image").src = image;

document.getElementById("desktop-expanded-image-link").href = image;

if (image.includes("media.giphy.com")) {
	attribution.innerHTML = '<img src="/assets/images/icons/PoweredBy_200px-Black_HorizLogo.png" style="width: 150px;">';
}

}

// When image modal is closed

$('#expandImageModal').on('hidden.bs.modal', function (e) {

  	// GIPHY attribution div

  	var attribution = document.getElementById("modal-image-attribution");

  	// remove the attribution

  	attribution.innerHTML = null;

	// remove image src and link

	document.getElementById("desktop-expanded-image").src = null;

	document.getElementById("desktop-expanded-image-link").href = null;

})
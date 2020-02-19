function expandDesktopImage(image, link) {

// GIPHY attribution div

var attribution = document.getElementById("modal-image-attribution");

// Link text

var linkText= document.getElementById("desktop-expanded-image-link")

document.getElementById("desktop-expanded-image").src = image;

if (image.includes("i.ruqqus.com")) {
	linkText.href = link;
	linkText.textContent = 'Go to website';
}
else if (image.includes("www.imgur.com") || image.includes("cdn.discordapp.com")){
	linkText.href = image;
	linkText.textContent = 'View original';
else {
	linkText.href = image;
	linkText.textContent = 'View original';
}

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
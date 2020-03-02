// Gloabl Desktop Vars

var toggleCard = document.getElementById('toggle-card-view-btn');
var toggleList = document.getElementById('toggle-list-view-btn');

var contentRow = document.getElementById('main-content-row');
var contentCol = document.getElementById('main-content-col');

// Desktop

if (localStorage.view_pref == 'list') {

	document.body.classList.add('toggle-list-view');

	if ( document.body.classList.contains('toggle-card-view')) {
		document.body.classList.remove('toggle-card-view')
	}

	toggleList.classList.add('active');
	toggleCard.classList.remove('active');
  
} else {

	document.body.classList.add('toggle-card-view');

	if ( document.body.classList.contains('toggle-list-view')) {
		document.body.classList.remove('toggle-list-view')
	}

	toggleCard.classList.add('active');
	toggleList.classList.remove('active');
}

toggle_card_view = function() {

	// Store Pref
	localStorage.setItem("view_pref", "card");

	document.body.classList.add('toggle-card-view');

	if ( document.body.classList.contains('toggle-list-view')) {
		document.body.classList.remove('toggle-list-view')
	}

	toggleCard.classList.add('active');
	toggleList.classList.remove('active');

}

toggle_list_view = function() {

	// Store Pref
	localStorage.setItem("view_pref", "list");

	document.body.classList.add('toggle-list-view');

	if ( document.body.classList.contains('toggle-card-view')) {
		document.body.classList.remove('toggle-card-view')
	}

	toggleList.classList.add('active');
	toggleCard.classList.remove('active');

}
// Desktop

if (localStorage.view_pref == 'list') {

	var toggleCard = document.getElementById('toggle-card-view-btn');
	var toggleList = document.getElementById('toggle-list-view-btn');

	var contentCol = document.getElementById('main-content-col');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-list-view');
	contentCol.classList.add('bg-white','shadow-sm','shadow-sm-0');

	if ( posts.classList.contains('toggle-card-view')) {
		posts.classList.remove('toggle-card-view')
	}

	toggleList.classList.add('active');
	toggleCard.classList.remove('active');
  
} else {

	var toggleCard = document.getElementById('toggle-card-view-btn');
	var toggleList = document.getElementById('toggle-list-view-btn');

	var contentCol = document.getElementById('main-content-col');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-card-view');

	if ( contentCol.classList.contains('bg-white','shadow-sm','shadow-sm-0')) {
	contentCol.classList.remove('bg-white','shadow-sm','shadow-sm-0')
	}

	if ( posts.classList.contains('toggle-list-view')) {
		posts.classList.remove('toggle-list-view')
	}

	toggleCard.classList.add('active');
	toggleList.classList.remove('active');
}

toggle_card_view = function() {

	// Store Pref
	localStorage.setItem("view_pref", "card");

	var toggleCard = document.getElementById('toggle-card-view-btn');
	var toggleList = document.getElementById('toggle-list-view-btn');

	var contentCol = document.getElementById('main-content-col');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-card-view');

	if ( contentCol.classList.contains('bg-white','shadow-sm','shadow-sm-0')) {
	contentCol.classList.remove('bg-white','shadow-sm','shadow-sm-0')
	}

	if ( posts.classList.contains('toggle-list-view')) {
		posts.classList.remove('toggle-list-view')
	}

	toggleCard.classList.add('active');
	toggleList.classList.remove('active');

}

toggle_list_view = function() {

	// Store Pref
	localStorage.setItem("view_pref", "list");

	var toggleCard = document.getElementById('toggle-card-view-btn');
	var toggleList = document.getElementById('toggle-list-view-btn');

	var contentCol = document.getElementById('main-content-col');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-list-view');
	contentCol.classList.add('bg-white','shadow-sm','shadow-sm-0');

	if ( posts.classList.contains('toggle-card-view')) {
		posts.classList.remove('toggle-card-view')
	}

	toggleList.classList.add('active');
	toggleCard.classList.remove('active');

}


// Mobile

if (localStorage.view_pref_mobile == 'list') {

	var toggleCard = document.getElementById('toggle-card-view-btn-sm');
	var toggleList = document.getElementById('toggle-list-view-btn-sm');

	var contentCol = document.getElementById('main-content-col');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-list-view');
	contentCol.classList.add('bg-white','shadow-sm','shadow-sm-0');

	if ( posts.classList.contains('toggle-card-view')) {
		posts.classList.remove('toggle-card-view')
	}

	toggleList.classList.add('active');
	toggleCard.classList.remove('active');
	
} else {

	var toggleCard = document.getElementById('toggle-card-view-btn-sm');
	var toggleList = document.getElementById('toggle-list-view-btn-sm');

	var contentCol = document.getElementById('main-content-col');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-card-view');

	if ( contentCol.classList.contains('bg-white','shadow-sm','shadow-sm-0')) {
	contentCol.classList.remove('bg-white','shadow-sm','shadow-sm-0')
	}

	if ( posts.classList.contains('toggle-list-view')) {
		posts.classList.remove('toggle-list-view')
	}

	toggleCard.classList.add('active');
	toggleList.classList.remove('active');
}

toggle_card_view_sm = function() {

	// Store Mobile Pref
	localStorage.setItem("view_pref_mobile", "card");

	var toggleCard = document.getElementById('toggle-card-view-btn-sm');
	var toggleList = document.getElementById('toggle-list-view-btn-sm');

	var contentCol = document.getElementById('main-content-col');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-card-view');

	if ( contentCol.classList.contains('bg-white','shadow-sm','shadow-sm-0')) {
	contentCol.classList.remove('bg-white','shadow-sm','shadow-sm-0')
	}

	if ( posts.classList.contains('toggle-list-view')) {
		posts.classList.remove('toggle-list-view')
	}

	toggleCard.classList.add('active');
	toggleList.classList.remove('active');

}

toggle_list_view_sm = function() {

	// Store Mobile Pref
	localStorage.setItem("view_pref_mobile", "list");

	var toggleCard = document.getElementById('toggle-card-view-btn-sm');
	var toggleList = document.getElementById('toggle-list-view-btn-sm');

	var contentCol = document.getElementById('main-content-col');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-list-view');
	contentCol.classList.add('bg-white','shadow-sm','shadow-sm-0');

	if ( posts.classList.contains('toggle-card-view')) {
		posts.classList.remove('toggle-card-view')
	}

	toggleList.classList.add('active');
	toggleCard.classList.remove('active');

}
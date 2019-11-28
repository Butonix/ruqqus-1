// Desktop

toggle_card_view = function() {

	var toggleCard = document.getElementById('toggle-card-view-btn');
	var toggleList = document.getElementById('toggle-list-view-btn');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-card-view');

	if ( posts.classList.contains('toggle-list-view')) {
		posts.classList.remove('toggle-list-view')
	}

	toggleCard.classList.add('active');
	toggleList.classList.remove('active');

}

toggle_list_view = function() {

	var toggleCard = document.getElementById('toggle-card-view-btn');
	var toggleList = document.getElementById('toggle-list-view-btn');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-list-view');

	if ( posts.classList.contains('toggle-card-view')) {
		posts.classList.remove('toggle-card-view')
	}

	toggleList.classList.add('active');
	toggleCard.classList.remove('active');

}

// Mobile

toggle_card_view_sm = function() {

	var toggleCard = document.getElementById('toggle-card-view-btn-sm');
	var toggleList = document.getElementById('toggle-list-view-btn-sm');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-card-view');

	if ( posts.classList.contains('toggle-list-view')) {
		posts.classList.remove('toggle-list-view')
	}

	toggleCard.classList.add('active');
	toggleList.classList.remove('active');

}

toggle_list_view_sm = function() {

	var toggleCard = document.getElementById('toggle-card-view-btn-sm');
	var toggleList = document.getElementById('toggle-list-view-btn-sm');

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-list-view');

	if ( posts.classList.contains('toggle-card-view')) {
		posts.classList.remove('toggle-card-view')
	}

	toggleList.classList.add('active');
	toggleCard.classList.remove('active');

}
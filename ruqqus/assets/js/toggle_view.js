toggle_card_view = function() {

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-card-vew');

	if ( posts.classList.contains('toggle-list-view')) {
		posts.classList.remove('toggle-list-view')
	}

}

toggle_list_view = function() {

	var posts = document.getElementById('posts');

	posts.classList.add('toggle-list-vew');

	if ( posts.classList.contains('toggle-card-view')) {
		posts.classList.remove('toggle-card-view')
	}

}
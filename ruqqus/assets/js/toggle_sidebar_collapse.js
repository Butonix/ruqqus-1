// Desktop

if (localStorage.sidebar_pref == 'collapsed') {

	document.getElementById('sidebar-left').classList.add('sidebar-collapsed');
  
}

toggle_sidebar_collapse = function() {

	// Store Pref
	localStorage.setItem('sidebar_pref', 'collapsed');

	document.getElementById('sidebar-left').classList.toggle('sidebar-collapsed');

}

toggle_sidebar_expand = function() {

	// Remove Pref
	localStorage.removeItem('sidebar_pref');

	document.getElementById('sidebar-left').classList.toggle('sidebar-collapsed');

}
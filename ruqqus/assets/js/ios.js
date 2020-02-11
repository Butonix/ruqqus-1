var eventHandler = function (event) {
    // Only run for iOS full screen apps
    if (('standalone' in window.navigator) && window.navigator.standalone) {
        // Only run if link is an anchor and points to the current page
        if ( event.target.tagName.toLowerCase() !== 'a' || event.target.hostname !== window.location.hostname || event.target.pathname !== window.location.pathname || !/#/.test(event.target.href) ) return;

        // Open link in same tab
        event.preventDefault();
        window.location = event.target.href;
    }
}
window.addEventListener('click', eventHandler, false);